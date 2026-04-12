import json
import os
import random
from uuid import uuid4
from collections import defaultdict

import joblib
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from schemas import (
    SkillsInput, TestSubmission, RecommendResponse, EvaluateResponse,
    UserSignup, UserLogin, AuthResponse, JourneyDashboardResponse,
)
from database import init_db, get_db, UserSession, TestResult, User
from utils import (
    SKILLS_LIST, DOMAIN_DATA, DOMAIN_SKILLS,
    normalize_skills, compute_skill_gap, compute_readiness_score,
    get_resources_for_skills, get_xai_explanation, hash_password, verify_password,
    build_learning_roadmap, build_fit_reasoning,
)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Career Intelligence API", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# ── Question bank ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_QB_PATH = os.path.join(BASE_DIR, "questions.json")

with open(_QB_PATH, "r", encoding="utf-8") as _f:
    QUESTION_BANK: dict[str, list[dict]] = json.load(_f)

# ── ML model ──────────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(BASE_DIR, "models", "career_model.pkl")
try:
    model = joblib.load(MODEL_PATH)
except FileNotFoundError:
    raise RuntimeError("Model not found. Run: python generate_dataset.py && python model.py")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sample_questions(domain: str, n: int = 10) -> list[dict]:
    """
    Return n randomly sampled questions, safe for the frontend.
    Exposes: id, text, question (alias), options, sub_topic, topic_tag.
    Never exposes correct_index.
    """
    pool = QUESTION_BANK.get(domain, [])
    if not pool:
        return []
    sampled = random.sample(pool, min(n, len(pool)))
    return [
        {
            "id":        q["id"],
            "text":      q["text"],
            "question":  q["text"],        # alias for legacy frontend
            "options":   q["options"],
            "sub_topic": q["sub_topic"],
            "topic_tag": q["sub_topic"],   # alias so both field names work
        }
        for q in sampled
    ]


def _parse_answers(raw_answers: list) -> dict[str, int]:
    """
    Normalise the answers payload into {question_id: chosen_index (int)}.

    Accepts:
      1. [{"id": "ds_01", "answer": 2}]   ← index-based (preferred)
      2. {"ds_01": 2, ...}                ← dict form
    """
    result: dict[str, int] = {}

    if isinstance(raw_answers, dict):
        return {str(k): int(v) for k, v in raw_answers.items() if str(v).isdigit() or isinstance(v, int)}

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
    """
    Returns (correct_count, quiz_score_pct, weak_area_subtopics).
    Scores by comparing chosen index against correct_index.
    weak_area_subtopics = sub_topic strings for every incorrect answer.
    """
    correct = 0
    weak_subtopics: list[str] = []

    for q in served_questions:
        chosen_idx = user_answer_map.get(q["id"], -1)
        if chosen_idx == q["correct_index"]:
            correct += 1
        else:
            weak_subtopics.append(q["sub_topic"])

    total      = len(served_questions)
    quiz_score = round((correct / total) * 100, 1) if total else 0.0
    return correct, quiz_score, weak_subtopics


def _detect_weak_topics(
    served_questions: list[dict],
    user_answer_map: dict[str, int],
    threshold: float = 0.4,
) -> list[dict]:
    """
    Group wrong answers by sub_topic.
    Flag any sub-topic where wrong_rate > threshold.
    """
    stats: dict[str, dict] = defaultdict(lambda: {"wrong": 0, "total": 0})

    for q in served_questions:
        tag = q["sub_topic"]
        stats[tag]["total"] += 1
        if user_answer_map.get(q["id"], -1) != q["correct_index"]:
            stats[tag]["wrong"] += 1

    weak = [
        {"sub_topic": tag, "wrong": s["wrong"], "total": s["total"]}
        for tag, s in stats.items()
        if s["total"] > 0 and (s["wrong"] / s["total"]) > threshold
    ]
    weak.sort(key=lambda x: x["wrong"] / x["total"], reverse=True)
    return weak


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Career Intelligence API v3.1 is running", "domains": list(QUESTION_BANK.keys())}


@app.post("/auth/signup", response_model=AuthResponse)
def signup(data: UserSignup, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(
        public_id=str(uuid4()),
        name=data.name.strip(),
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Account created successfully.",
        "user": {
            "user_id": user.public_id,
            "name": user.name,
            "email": user.email,
        },
    }


@app.post("/auth/login", response_model=AuthResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return {
        "message": f"Welcome back, {user.name}.",
        "user": {
            "user_id": user.public_id,
            "name": user.name,
            "email": user.email,
        },
    }


@app.get("/users/{user_id}/dashboard", response_model=JourneyDashboardResponse)
def get_user_dashboard(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.public_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id)
        .order_by(UserSession.created_at.desc())
        .all()
    )
    tests = (
        db.query(TestResult)
        .filter(TestResult.user_id == user_id)
        .order_by(TestResult.created_at.desc())
        .all()
    )

    latest_session = sessions[0] if sessions else None
    latest_test = tests[0] if tests else None
    latest_skills = latest_session.skills_input.split(",") if latest_session and latest_session.skills_input else []
    latest_domain = latest_session.top_domain if latest_session else (latest_test.domain if latest_test else None)
    average_readiness = round(
        sum(item.readiness_score for item in tests) / len(tests),
        1,
    ) if tests else 0.0
    latest_readiness = round(latest_test.readiness_score, 1) if latest_test else 0.0

    roadmap = None
    if latest_domain:
        roadmap = build_learning_roadmap(
            user_skills=latest_skills,
            domain=latest_domain,
            recent_readiness=latest_readiness if tests else None,
        )

    return {
        "user": {
            "user_id": user.public_id,
            "name": user.name,
            "email": user.email,
        },
        "overview": {
            "analyses_count": len(sessions),
            "assessments_count": len(tests),
            "latest_top_domain": latest_domain,
            "average_readiness": average_readiness,
            "latest_readiness": latest_readiness,
        },
        "recommendation_history": [
            {
                "id": item.id,
                "skills_input": [skill for skill in item.skills_input.split(",") if skill],
                "top_domain": item.top_domain,
                "confidence": round(item.confidence, 2),
                "created_at": item.created_at.isoformat(),
            }
            for item in sessions
        ],
        "assessment_history": [
            {
                "id": item.id,
                "domain": item.domain,
                "assessment_score": round(item.assessment_score, 1),
                "skill_match": round(item.skill_match, 1),
                "readiness_score": round(item.readiness_score, 1),
                "created_at": item.created_at.isoformat(),
            }
            for item in tests
        ],
        "roadmap": roadmap,
    }


# ── GET /questions/{domain}  (new canonical path) ─────────────────────────────
@app.get("/questions/{domain:path}")
def get_questions_v2(domain: str):
    """
    Returns 10 randomly sampled questions for the domain.
    Fields: id, text, question, options (4 items), sub_topic, topic_tag.
    Uses {domain:path} to allow slashes in domain names like 'UI/UX Designer'.
    correct_index is intentionally excluded.
    """
    domain = domain.strip()
    questions = _sample_questions(domain, n=10)
    if not questions:
        raise HTTPException(
            status_code=404,
            detail=f"No questions found for '{domain}'. Available: {list(QUESTION_BANK.keys())}",
        )
    return {"domain": domain, "questions": questions, "total": len(questions)}


# ── GET /get-questions/{domain}  (legacy path — kept for backward compat) ─────
@app.get("/get-questions/{domain:path}")
def get_questions_legacy(domain: str):
    return get_questions_v2(domain)


# ── POST /evaluate  (new canonical path) ──────────────────────────────────────
@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate(data: TestSubmission, db: Session = Depends(get_db)):
    """
    Score a completed quiz.

    Request body:
      {
        "domain": "Data Scientist",
        "answers": [{"id": "ds_01", "answer": "df.dropna()"}, ...],
        "skills": ["python", "sql"]   // optional — used for readiness formula
      }

    Scoring:
      quiz_score    = correct / total × 100
      readiness     = 0.6 × skill_match + 0.4 × quiz_score
      weak_topics   = sub-topics where wrong_rate > 40%
    """
    domain = data.domain.strip()
    full_questions = QUESTION_BANK.get(domain)

    if not full_questions:
        raise HTTPException(
            status_code=404,
            detail=f"Domain '{domain}' not found. Available: {list(QUESTION_BANK.keys())}",
        )

    # Parse answers into {id: chosen_option}
    user_answer_map = _parse_answers(data.answers)

    if not user_answer_map:
        raise HTTPException(
            status_code=422,
            detail=(
                "No valid answers received. "
                "Send answers as [{\"id\": \"<question_id>\", \"answer\": <chosen_index>}]."
            ),
        )

    # Resolve which questions were actually served to this user
    served_ids       = set(user_answer_map.keys())
    served_questions = [q for q in full_questions if q["id"] in served_ids]

    if not served_questions:
        raise HTTPException(
            status_code=422,
            detail=(
                f"None of the submitted question IDs match domain '{domain}'. "
                f"Expected IDs like: {[q['id'] for q in full_questions[:3]]}..."
            ),
        )

    # ── Score ─────────────────────────────────────────────────────────────────
    correct, quiz_score, weak_area_subtopics = _score_answers(served_questions, user_answer_map)

    # ── Weak topic detection ──────────────────────────────────────────────────
    weak_sub_topics = _detect_weak_topics(served_questions, user_answer_map)

    # ── Readiness formula: Overall = (0.6 × Skill Match) + (0.4 × Quiz Score) ─
    user_skills  = normalize_skills(data.skills or [])
    gap          = compute_skill_gap(user_skills, domain)
    skill_match  = gap["match_percentage"]
    readiness    = compute_readiness_score(skill_match, quiz_score)
    readiness["domain"] = domain

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
    resources = get_resources_for_skills(gap["missing_skills"][:5])

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
        "score":           int(quiz_score),   # backward compat
        "feedback":        feedback,
        "weak_sub_topics": weak_sub_topics,
        "weak_areas":      list(dict.fromkeys(weak_area_subtopics)),  # unique sub_topics of wrong answers
        "readiness":       readiness,
        "resources":       resources,
    }


# ── POST /evaluate-test  (legacy path) ────────────────────────────────────────
@app.post("/evaluate-test", response_model=EvaluateResponse)
def evaluate_test_legacy(data: TestSubmission, db: Session = Depends(get_db)):
    return evaluate(data, db)


# ── POST /recommend-career ────────────────────────────────────────────────────
@app.post("/recommend-career", response_model=RecommendResponse)
def recommend(data: SkillsInput, db: Session = Depends(get_db)):
    user_skills  = normalize_skills(data.skills)
    input_vector = [1 if s in user_skills else 0 for s in SKILLS_LIST]

    if not any(input_vector):
        raise HTTPException(
            status_code=400,
            detail="No recognised skills. Try: python, sql, react, docker.",
        )

    probs      = model.predict_proba([input_vector])[0]
    classes    = model.classes_
    top_idx    = probs.argsort()[-3:][::-1]

    recommendations, skill_gap_list, all_missing = [], [], []

    for i in top_idx:
        domain  = classes[i]
        matched = list(set(user_skills) & set(DOMAIN_SKILLS[domain]))
        xai     = get_xai_explanation(model, SKILLS_LIST, input_vector)
        reasoning = build_fit_reasoning(user_skills, domain, round(float(probs[i]) * 100, 2))

        recommendations.append({
            "domain":     domain,
            "confidence": round(float(probs[i]) * 100, 2),
            "salary":     DOMAIN_DATA[domain]["salary"],
            "demand":     DOMAIN_DATA[domain]["demand"],
            "reason":     [f"You know {s.upper()}" for s in matched] or ["Explore this domain"],
            "top_skills": xai,
            "fit_summary": reasoning["fit_summary"],
            "growth_summary": reasoning["growth_summary"],
            "missing_priority_skills": reasoning["missing_priority_skills"],
            "project_suggestions": reasoning["project_suggestions"],
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
