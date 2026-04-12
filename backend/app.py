import json
import os
import random
from collections import defaultdict

import joblib
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

load_dotenv()

from schemas import SkillsInput, TestSubmission, ChatRequest, RecommendResponse, EvaluateResponse
from database import init_db, get_db, UserSession, TestResult
from utils import (
    SKILLS_LIST, DOMAIN_DATA, DOMAIN_SKILLS,
    normalize_skills, compute_skill_gap,
    get_resources_for_skills, get_xai_explanation,
)
import llm_service

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Career Intelligence API", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# ── Static question bank (fallback when LLM is unavailable) ──────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
_QB_PATH   = os.path.join(BASE_DIR, "questions.json")
with open(_QB_PATH, "r", encoding="utf-8") as _f:
    QUESTION_BANK: dict[str, list[dict]] = json.load(_f)

# ── ML model ──────────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(BASE_DIR, "models", "career_model.pkl")
try:
    model = joblib.load(MODEL_PATH)
except FileNotFoundError:
    raise RuntimeError("Model not found. Run: python generate_dataset.py && python model.py")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_correct_index(questions: list[dict]) -> list[dict]:
    """Return questions safe for the frontend — no correct_index exposed."""
    return [
        {
            "id":        q["id"],
            "text":      q.get("text", q.get("question", "")),
            "question":  q.get("text", q.get("question", "")),
            "options":   q["options"],
            "sub_topic": q.get("sub_topic", q.get("topic_tag", "")),
            "topic_tag": q.get("topic_tag", q.get("sub_topic", "")),
        }
        for q in questions
    ]


def _sample_static(domain: str, n: int = 10) -> list[dict]:
    pool = QUESTION_BANK.get(domain, [])
    if not pool:
        return []
    sampled = random.sample(pool, min(n, len(pool)))
    return _strip_correct_index(sampled)


def _parse_answers(raw_answers: list) -> dict[str, int]:
    result: dict[str, int] = {}
    if isinstance(raw_answers, dict):
        return {str(k): int(v) for k, v in raw_answers.items() if isinstance(v, int) or str(v).lstrip("-").isdigit()}
    for item in raw_answers:
        if isinstance(item, dict):
            qid = str(item.get("id", item.get("question_id", "")))
            val = item.get("answer", item.get("selected", None))
            if qid and val is not None:
                try:
                    result[qid] = int(val)
                except (ValueError, TypeError):
                    pass
    return result


def _score_answers(
    served_questions: list[dict],
    user_answer_map: dict[str, int],
) -> tuple[int, float, list[str]]:
    correct, weak = 0, []
    for q in served_questions:
        if user_answer_map.get(q["id"], -1) == q["correct_index"]:
            correct += 1
        else:
            weak.append(q.get("sub_topic", q.get("topic_tag", "")))
    total = len(served_questions)
    return correct, round((correct / total) * 100, 1) if total else 0.0, weak


def _detect_weak_topics(served_questions: list[dict], user_answer_map: dict[str, int]) -> list[dict]:
    stats: dict[str, dict] = defaultdict(lambda: {"wrong": 0, "total": 0})
    for q in served_questions:
        tag = q.get("sub_topic", q.get("topic_tag", ""))
        stats[tag]["total"] += 1
        if user_answer_map.get(q["id"], -1) != q["correct_index"]:
            stats[tag]["wrong"] += 1
    weak = [
        {"sub_topic": tag, "wrong": s["wrong"], "total": s["total"]}
        for tag, s in stats.items()
        if s["total"] > 0 and (s["wrong"] / s["total"]) > 0.4
    ]
    weak.sort(key=lambda x: x["wrong"] / x["total"], reverse=True)
    return weak


def _weighted_skill_match(skills: dict[str, int], domain: str) -> float:
    """
    Weighted skill match = sum(proficiency/5) for matched domain skills / total domain skills.
    Returns 0-100.
    """
    required = DOMAIN_SKILLS.get(domain, [])
    if not required:
        return 0.0
    total_possible = len(required)
    weighted_sum   = sum(skills.get(s, 0) / 5.0 for s in required)
    return round((weighted_sum / total_possible) * 100, 1)


def _compute_readiness(skill_match: float, quiz_score: float, domain: str) -> dict:
    score = round((0.6 * skill_match) + (0.4 * quiz_score), 1)
    label = "Job Ready" if score >= 75 else "Developing" if score >= 45 else "Beginner"
    return {
        "domain":                 domain,
        "skill_match":            round(skill_match, 1),
        "assessment_performance": round(quiz_score, 1),
        "readiness_score":        score,
        "label":                  label,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Career Intelligence API v4.0 is running", "domains": list(QUESTION_BANK.keys())}


# ── GET /questions/{domain}  ──────────────────────────────────────────────────
@app.get("/questions/{domain:path}")
async def get_questions(domain: str, skills: str = ""):
    """
    Returns 10 questions for the domain.
    If GEMINI_API_KEY is set and `skills` query param is provided as JSON,
    questions are generated dynamically by the LLM.
    Otherwise falls back to the static question bank.

    ?skills={"python":4,"sql":2}
    """
    domain = domain.strip()

    # Try LLM generation if skills provided and API configured
    skills_dict: dict[str, int] = {}
    if skills:
        try:
            skills_dict = json.loads(skills)
        except json.JSONDecodeError:
            pass

    if skills_dict and llm_service._CONFIGURED:
        try:
            questions = await llm_service.generate_questions(domain, skills_dict)
            return {"domain": domain, "questions": _strip_correct_index(questions), "total": len(questions), "source": "llm"}
        except Exception:
            pass  # fall through to static

    # Static fallback
    questions = _sample_static(domain)
    if not questions:
        raise HTTPException(
            status_code=404,
            detail=f"No questions found for '{domain}'. Available: {list(QUESTION_BANK.keys())}",
        )
    return {"domain": domain, "questions": questions, "total": len(questions), "source": "static"}


# ── Legacy path ───────────────────────────────────────────────────────────────
@app.get("/get-questions/{domain:path}")
async def get_questions_legacy(domain: str, skills: str = ""):
    return await get_questions(domain, skills)


# ── POST /evaluate ────────────────────────────────────────────────────────────
@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(data: TestSubmission, db: Session = Depends(get_db)):
    domain       = data.domain.strip()
    skills_dict  = data.skills_as_dict()

    # Resolve the full question pool (LLM cache first, then static)
    full_questions: list[dict] = []
    if skills_dict and llm_service._CONFIGURED:
        try:
            full_questions = await llm_service.generate_questions(domain, skills_dict)
        except Exception:
            pass

    if not full_questions:
        full_questions = QUESTION_BANK.get(domain, [])

    if not full_questions:
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found.")

    user_answer_map = _parse_answers(data.answers)
    if not user_answer_map:
        raise HTTPException(status_code=422, detail="No valid answers received.")

    served_ids       = set(user_answer_map.keys())
    served_questions = [q for q in full_questions if q["id"] in served_ids]

    if not served_questions:
        raise HTTPException(
            status_code=422,
            detail=f"Question IDs don't match domain '{domain}'. Expected like: {[q['id'] for q in full_questions[:3]]}",
        )

    # ── Score ─────────────────────────────────────────────────────────────────
    correct, quiz_score, weak_subtopics = _score_answers(served_questions, user_answer_map)
    weak_sub_topics = _detect_weak_topics(served_questions, user_answer_map)

    # ── Weighted readiness: (0.6 × weighted_skill_match) + (0.4 × quiz_score) ─
    skill_match = _weighted_skill_match(skills_dict, domain) if skills_dict else 0.0
    readiness   = _compute_readiness(skill_match, quiz_score, domain)

    # ── Feedback ──────────────────────────────────────────────────────────────
    if quiz_score >= 80:
        feedback = "Excellent — your quiz performance is strong."
    elif quiz_score >= 60:
        feedback = "Good progress. Review the flagged sub-topics to level up."
    elif quiz_score >= 40:
        feedback = "Keep going — focus on the weak areas identified below."
    else:
        feedback = "Start with the fundamentals. Use the resources below to build a solid base."

    # ── Resources ─────────────────────────────────────────────────────────────
    missing = [s for s in DOMAIN_SKILLS.get(domain, []) if s not in skills_dict]
    resources = get_resources_for_skills(missing[:5])

    # ── Persist ───────────────────────────────────────────────────────────────
    db.add(TestResult(
        user_id=data.user_id,
        domain=domain,
        assessment_score=quiz_score,
        skill_match=skill_match,
        readiness_score=readiness["readiness_score"],
    ))
    db.commit()

    return {
        "quiz_score":      int(quiz_score),
        "correct_count":   correct,
        "score":           int(quiz_score),
        "feedback":        feedback,
        "weak_sub_topics": weak_sub_topics,
        "weak_areas":      list(dict.fromkeys(weak_subtopics)),
        "readiness":       readiness,
        "resources":       resources,
    }


# ── POST /evaluate-test  (legacy) ─────────────────────────────────────────────
@app.post("/evaluate-test", response_model=EvaluateResponse)
async def evaluate_test_legacy(data: TestSubmission, db: Session = Depends(get_db)):
    return await evaluate(data, db)


# ── POST /api/chat  (streaming consultant) ────────────────────────────────────
@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    Streaming endpoint for the AI Career Consultant.
    Returns text/event-stream chunks.
    """
    weak_str = ", ".join(req.weak_areas) if req.weak_areas else "none identified"

    system_prompt = (
        f"You are an expert Career Consultant specialising in tech careers. "
        f"The user just completed a {req.domain} assessment. "
        f"Their quiz score was {req.quiz_score}% and overall readiness score is {req.readiness_score:.0f}%. "
        f"Their weak areas are: {weak_str}. "
        f"Be concise, encouraging, and actionable. "
        f"When asked for a learning path, provide exactly 3 numbered steps with specific resources."
    )

    async def event_stream():
        try:
            async for chunk in llm_service.stream_chat(system_prompt, req.message):
                # SSE format
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── POST /recommend-career ────────────────────────────────────────────────────
@app.post("/recommend-career", response_model=RecommendResponse)
def recommend(data: SkillsInput, db: Session = Depends(get_db)):
    skills_list = data.skills_as_list()
    skills_dict = data.skills_as_dict()

    user_skills  = normalize_skills(skills_list)
    input_vector = [1 if s in user_skills else 0 for s in SKILLS_LIST]

    if not any(input_vector):
        raise HTTPException(status_code=400, detail="No recognised skills. Try: python, sql, react, docker.")

    probs   = model.predict_proba([input_vector])[0]
    classes = model.classes_
    top_idx = probs.argsort()[-3:][::-1]

    recommendations, skill_gap_list, all_missing = [], [], []

    for i in top_idx:
        domain  = classes[i]
        matched = list(set(user_skills) & set(DOMAIN_SKILLS[domain]))
        xai     = get_xai_explanation(model, SKILLS_LIST, input_vector)

        recommendations.append({
            "domain":     domain,
            "confidence": round(float(probs[i]) * 100, 2),
            "salary":     DOMAIN_DATA[domain]["salary"],
            "demand":     DOMAIN_DATA[domain]["demand"],
            "reason":     [f"You know {s.upper()}" for s in matched] or ["Explore this domain"],
            "top_skills": xai,
        })

        gap = compute_skill_gap(user_skills, domain)
        skill_gap_list.append(gap)
        all_missing.extend(gap["missing_skills"])

    resources = get_resources_for_skills(list(dict.fromkeys(all_missing))[:8])

    db.add(UserSession(
        user_id=data.user_id,
        skills_input=",".join(user_skills),
        top_domain=recommendations[0]["domain"],
        confidence=recommendations[0]["confidence"],
    ))
    db.commit()

    return {"recommendations": recommendations, "skill_gap": skill_gap_list, "resources": resources}
