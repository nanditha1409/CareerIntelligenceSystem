import json
import os
import random
from collections import defaultdict
from typing import Any

import joblib
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

load_dotenv()

from schemas import (
    SkillsInput,
    TestSubmission,
    ChatRequest,
    RecommendResponse,
    EvaluateResponse,
    UserRegister,
    UserLogin,
    AuthResponse,
    CareerIntelligenceRequest,
    AnalyticsResponse,
    ResumeAnalysisResponse,
    ResumeUploadResponse,
)
from database import (
    init_db,
    get_db,
    UserSession,
    TestResult,
    User,
    UserCareerProfile,
    RecommendationSnapshot,
    PerformanceEvent,
    ResumeSnapshot,
)
from auth_utils import hash_password, verify_password, create_access_token, get_current_user
from utils import (
    SKILLS_LIST, DOMAIN_DATA, DOMAIN_SKILLS,
    normalize_skills, compute_skill_gap,
    get_resources_for_skills,
    rank_domains_by_compatibility, resolve_domain_name,
)
from career_intelligence_service import build_career_pathways
from report_service import recommendations_to_csv, readiness_to_csv
from config.domain_manifest import DOMAIN_MANIFEST, LEGACY_DOMAIN_ALIASES
from services.company_quiz_service import generate_company_questions
from services.phi3_service import query_phi3, stream_phi3
from services.resume_parser_service import extract_text_from_upload, extract_skills_from_text, build_resume_summary
from ml.inference import (
    build_learning_analytics,
    personalize_questions,
    predict_domain_recommendations,
    predict_next_difficulty,
)
# Task 1: CSV-based RandomForest/XGBoost classifier with XAI feature importance
from ml.train_classifier import get_prediction_confidence
# Task 3: Semantic similarity engine (TF-IDF cosine + optional SBERT)
from ml.similarity import find_similar_domains
# Task 2: NLP resume parser (pdfplumber + spaCy NER)
from utils.resume_parser import build_resume_analysis
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
    # Addition: the older handcrafted model remains optional; ML-first inference has its own artifacts.
    model = None


# ── Helpers ───────────────────────────────────────────────────────────────────

DYNAMIC_DOMAINS = list(DOMAIN_MANIFEST.keys())

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
    pool = QUESTION_BANK.get(_resolve_question_bank_key(domain), [])
    if not pool:
        return []
    sampled = random.sample(pool, min(n, len(pool)))
    return _strip_correct_index(sampled)


def _resolve_question_bank_key(domain: str) -> str:
    canonical_domain = resolve_domain_name(domain)
    if canonical_domain in QUESTION_BANK:
        return canonical_domain
    for legacy_domain, current_domain in LEGACY_DOMAIN_ALIASES.items():
        if current_domain == canonical_domain and legacy_domain in QUESTION_BANK:
            return legacy_domain
    return canonical_domain


def _coerce_skills_profile(raw: Any) -> dict[str, int]:
    # Change: accepts any skill string and clamps proficiency to 1-5 for stability.
    if not isinstance(raw, dict):
        return {}
    cleaned: dict[str, int] = {}
    for key, value in raw.items():
        if isinstance(key, str) and key.strip():
            try:
                cleaned[key.strip()] = max(1, min(5, int(value)))
            except (TypeError, ValueError):
                cleaned[key.strip()] = 3
    return cleaned


def calculate_question_distribution(skills_profile: dict[str, int], total: int = 10) -> dict[str, int]:
    # Remainder-heavy proportional weighting: allocates exactly `total` questions.
    if total <= 0:
        return {}
    if not skills_profile:
        return {"General": total}

    total_units = sum(max(1, int(level)) for level in skills_profile.values())
    if total_units <= 0:
        return {"General": total}

    base_counts: dict[str, int] = {}
    remainders: list[tuple[str, float]] = []
    for skill, level in skills_profile.items():
        fraction = (max(1, int(level)) / total_units) * total
        floored = int(fraction)
        base_counts[skill] = floored
        remainders.append((skill, fraction - floored))

    current_total = sum(base_counts.values())
    remaining_slots = total - current_total

    # Remainder-heavy: assign leftover questions to largest fractional remainders.
    for skill, _ in sorted(remainders, key=lambda item: item[1], reverse=True):
        if remaining_slots <= 0:
            break
        base_counts[skill] += 1
        remaining_slots -= 1

    # Hard guard (safety for edge cases): ensure exact total count.
    while sum(base_counts.values()) < total:
        first_skill = next(iter(base_counts))
        base_counts[first_skill] += 1
    while sum(base_counts.values()) > total:
        for skill in list(base_counts.keys()):
            if base_counts[skill] > 0 and sum(base_counts.values()) > total:
                base_counts[skill] -= 1

    return base_counts


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
    required = DOMAIN_SKILLS.get(resolve_domain_name(domain), [])
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
    # Change: surface expanded domain list for dynamic question generation clients.
    return {"message": "Career Intelligence API v4.0 is running", "domains": sorted(set(list(QUESTION_BANK.keys()) + DYNAMIC_DOMAINS))}


@app.get("/api/health")
def health_check():
    # Simple non-breaking health endpoint for uptime checks/monitoring.
    return {"status": "ok", "service": "career-intelligence-api"}


def _resolve_user_id(explicit_user_id: str | None, current_user: User | None) -> str | None:
    if current_user:
        return str(current_user.id)
    return explicit_user_id


def _resolve_profile_user_id(explicit_user_id: str | None, current_user: User | None) -> int | None:
    # Persist profile for authenticated users; also supports legacy explicit user_id when numeric.
    if current_user:
        return current_user.id
    if explicit_user_id is None:
        return None
    try:
        return int(explicit_user_id)
    except (TypeError, ValueError):
        return None


# Addition: ML question adaptation relies on historical performance aggregates,
# but the endpoint still works when there is no user history.
def _get_user_performance_rows(
    db: Session,
    explicit_user_id: str | None,
    current_user: User | None,
    domain: str | None = None,
) -> list[PerformanceEvent]:
    resolved_user_id = _resolve_user_id(explicit_user_id, current_user)
    if not resolved_user_id:
        return []

    query = db.query(PerformanceEvent).filter(PerformanceEvent.user_id == str(resolved_user_id))
    if domain:
        query = query.filter(PerformanceEvent.domain == resolve_domain_name(domain))
    return query.order_by(PerformanceEvent.created_at.desc()).all()


def _compute_adaptive_difficulty(
    history_rows: list[PerformanceEvent],
) -> dict[str, Any]:
    """
    Predict the next difficulty using ML when enough telemetry exists,
    otherwise fall back to a simple stable heuristic.
    """
    if not history_rows:
        return {"difficulty": "Medium", "probabilities": {"Medium": 100.0}}

    recent_window = history_rows[:10]
    avg_score = sum(float(row.score or 0.0) for row in history_rows) / max(1, len(history_rows))
    recent_score = sum(float(row.score or 0.0) for row in recent_window) / max(1, len(recent_window))
    weak_topic_rate = sum(1 for row in recent_window if not bool(row.is_correct)) / max(1, len(recent_window))

    try:
        return predict_next_difficulty(
            recent_score=recent_score,
            avg_score=avg_score,
            weak_topic_rate=weak_topic_rate,
            attempts=len(history_rows),
        )
    except Exception:
        if recent_score >= 80 and weak_topic_rate < 0.25:
            return {"difficulty": "Hard", "probabilities": {"Hard": 100.0}}
        if recent_score < 50 or weak_topic_rate > 0.5:
            return {"difficulty": "Easy", "probabilities": {"Easy": 100.0}}
        return {"difficulty": "Medium", "probabilities": {"Medium": 100.0}}


def _apply_adaptive_difficulty(
    questions: list[dict],
    target_difficulty: str,
    limit: int = 10,
) -> list[dict]:
    """
    Approximate difficulty from question-bank content so the adaptive system
    can operate without requiring a new authoring format in the static JSON.
    """
    difficulty_map = {
        "Easy": {"what is", "which", "define", "purpose", "used for"},
        "Hard": {"architecture", "system", "optim", "design", "advanced", "distributed"},
    }

    easy_markers = difficulty_map["Easy"]
    hard_markers = difficulty_map["Hard"]

    def infer_question_difficulty(question: dict) -> str:
        return _infer_question_difficulty(question, easy_markers, hard_markers)

    matching = [question for question in questions if infer_question_difficulty(question) == target_difficulty]
    if len(matching) >= limit:
        return matching[:limit]
    return (matching + questions)[:limit]


def _infer_question_difficulty(
    question: dict,
    easy_markers: set[str] | None = None,
    hard_markers: set[str] | None = None,
) -> str:
    easy_markers = easy_markers or {"what is", "which", "define", "purpose", "used for"}
    hard_markers = hard_markers or {"architecture", "system", "optim", "design", "advanced", "distributed"}
    text = str(question.get("text", question.get("question", ""))).lower()
    if any(marker in text for marker in hard_markers):
        return "Hard"
    if any(marker in text for marker in easy_markers):
        return "Easy"
    return "Medium"


def _build_recommendation_payload(skills_list: list[str]) -> tuple[list[str], list[dict], list[dict], list[dict]]:
    normalized_skills = normalize_skills(skills_list)
    ranked_matches: list[dict[str, Any]] = []

    # Task 1: ML-first domain recommendations with coefficient-based explanations.
    try:
        ml_matches = predict_domain_recommendations(normalized_skills, top_k=3)
        for match in ml_matches:
            ranked_matches.append(
                {
                    "domain": match["domain"],
                    "matched_skills": match["matched_skills"],
                    "missing_skills": [
                        skill for skill in DOMAIN_SKILLS.get(match["domain"], [])
                        if skill not in set(normalized_skills)
                    ],
                    "compatibility_score": match["confidence"],
                    "keyword_match_count": len(match["matched_skills"]),
                    "explanation": match["explanation"],
                    "top_features": match.get("top_features", []),
                    "model_source": "ml",
                }
            )
    except Exception:
        ranked_matches = []

    # Task 1: CSV classifier confidence scores + XAI feature importance (additive layer).
    classifier_results: dict[str, dict] = {}
    try:
        clf_predictions = get_prediction_confidence(normalized_skills, top_k=5)
        for pred in clf_predictions:
            classifier_results[pred["domain"]] = pred
    except Exception:
        pass

    # Task 3: Semantic similarity scores (replaces hardcoded keyword→domain mapping).
    semantic_results: dict[str, dict] = {}
    try:
        sem_matches = find_similar_domains(normalized_skills, top_k=5)
        for sem in sem_matches:
            semantic_results[sem["domain"]] = sem
    except Exception:
        pass

    # Addition: retain the original deterministic ranking as a production fallback.
    if not ranked_matches:
        ranked_matches = rank_domains_by_compatibility(normalized_skills, limit=3)

    if not ranked_matches:
        raise HTTPException(
            status_code=400,
            detail="No recognized domain-aligned skills found. Try skills like python, sql, ml, react, docker, aws, or figma.",
        )

    recommendations: list[dict] = []
    skill_gap_list: list[dict] = []
    all_missing: list[str] = []

    for match in ranked_matches:
        domain = match["domain"]
        gap = compute_skill_gap(normalized_skills, domain)
        matched_skills = gap["matched_skills"][:5]
        fallback_skills = DOMAIN_SKILLS.get(domain, [])[:3]
        ml_reasoning = match.get("explanation", [])
        model_source = match.get("model_source", "rules")

        # Task 1 & 4: attach classifier confidence + XAI feature importance.
        clf_data = classifier_results.get(domain, {})
        confidence_score   = clf_data.get("confidence_score")
        matching_keywords  = clf_data.get("matching_keywords", [])

        # Task 4: build feature_importance list from classifier importances.
        feature_importance = []
        if matching_keywords:
            feature_importance = [
                {"skill": skill, "importance": round(1.0 / (i + 1), 3)}
                for i, skill in enumerate(matching_keywords)
            ]

        # Task 3: blend semantic similarity into the confidence score when available.
        sem_data = semantic_results.get(domain, {})
        if sem_data and confidence_score is None:
            confidence_score = sem_data.get("similarity_score")
            matching_keywords = matching_keywords or sem_data.get("matching_keywords", [])

        recommendations.append(
            {
                "domain":             domain,
                "confidence":         match["compatibility_score"],
                "salary":             DOMAIN_DATA[domain]["salary"],
                "demand":             DOMAIN_DATA[domain]["demand"],
                "reason":             ml_reasoning or [f"You match {skill.upper()}" for skill in matched_skills] or ["Keyword mapping indicates domain alignment"],
                "top_skills":         match.get("top_features", [])[:3] or matched_skills[:3] or fallback_skills,
                "model_source":       model_source,
                # Task 1 & 3 extensions (backward-compatible optional fields):
                "confidence_score":   confidence_score,
                "matching_keywords":  matching_keywords,
                "feature_importance": feature_importance,
            }
        )
        skill_gap_list.append(gap)
        all_missing.extend(gap["missing_skills"])

    resources = get_resources_for_skills(list(dict.fromkeys(all_missing))[:8])
    return normalized_skills, recommendations, skill_gap_list, resources


@app.post("/api/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    full_name = payload.full_name.strip()
    password = payload.password.strip()

    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    if not full_name:
        raise HTTPException(status_code=400, detail="Full name is required.")
    # Extra guardrail for accidental very long payloads.
    if len(full_name) > 120:
        raise HTTPException(status_code=400, detail="Full name is too long.")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(email=email, full_name=full_name, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        {"sub": str(user.id), "email": user.email, "full_name": user.full_name}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name},
    }


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(
        {"sub": str(user.id), "email": user.email, "full_name": user.full_name}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name},
    }


@app.get("/api/auth/me")
def auth_me(current_user: User | None = Depends(get_current_user)):
    # Optional profile endpoint so frontend can restore session without relogin.
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return {"id": current_user.id, "email": current_user.email, "full_name": current_user.full_name}


# ── GET /questions/{domain}  ──────────────────────────────────────────────────
@app.get("/questions/{domain:path}")
async def get_questions(
    domain: str,
    skills: str = "",
    user_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """
    Returns 10 questions for the domain.
    If GEMINI_API_KEY is set and `skills` query param is provided as JSON,
    questions are generated dynamically by the LLM.
    Otherwise falls back to the static question bank.

    ?skills={"python":4,"sql":2}
    """
    domain = resolve_domain_name(domain)

    # Change: parse raw skill profile and preserve arbitrary skill strings for LLM prompting.
    skills_dict: dict[str, int] = {}
    if skills:
        try:
            skills_dict = _coerce_skills_profile(json.loads(skills))
        except json.JSONDecodeError:
            pass

    # Addition: fetch user history and adapt the next difficulty using ML when data exists.
    performance_rows = _get_user_performance_rows(db, user_id, current_user, domain)
    adaptive_profile = _compute_adaptive_difficulty(performance_rows)
    target_difficulty = adaptive_profile["difficulty"]

    # Change: distribution is returned for frontend status text and used to drive LLM question ratios.
    distribution = calculate_question_distribution(skills_dict, total=10)
    if llm_service._CONFIGURED:
        try:
            questions = await llm_service.generate_questions(domain, skills_dict or {"General": 3}, distribution)
            personalized = personalize_questions(
                {
                    "skills": skills_dict or list(skills_dict.keys()),
                    "weak_topics": [row.topic_tag for row in performance_rows if not bool(row.is_correct)],
                    "domain": domain,
                },
                _apply_adaptive_difficulty(questions, target_difficulty, limit=10),
                limit=10,
            )
            return {
                "domain": domain,
                "questions": _strip_correct_index(personalized),
                "total": len(personalized),
                "source": "llm",
                "question_distribution": distribution,
                "adaptive_difficulty": adaptive_profile,
            }
        except Exception:
            # If LLM fails, fallback to static bank.
            pass

    # Static fallback
    static_questions = QUESTION_BANK.get(_resolve_question_bank_key(domain), [])
    personalized = personalize_questions(
        {
            "skills": skills_dict or list(skills_dict.keys()),
            "weak_topics": [row.topic_tag for row in performance_rows if not bool(row.is_correct)],
            "domain": domain,
        },
        _apply_adaptive_difficulty(static_questions, target_difficulty, limit=10),
        limit=10,
    )
    questions = _strip_correct_index(personalized)
    if not questions:
        raise HTTPException(
            status_code=404,
            detail=f"No questions found for '{domain}'. Available: {list(QUESTION_BANK.keys())}",
        )
    return {
        "domain": domain,
        "questions": questions,
        "total": len(questions),
        "source": "static",
        "question_distribution": distribution,
        "adaptive_difficulty": adaptive_profile,
    }


# ── Legacy path ───────────────────────────────────────────────────────────────
@app.get("/get-questions/{domain:path}")
async def get_questions_legacy(
    domain: str,
    skills: str = "",
    user_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    return await get_questions(domain, skills, user_id, db, current_user)


# ── POST /evaluate ────────────────────────────────────────────────────────────
@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(
    data: TestSubmission,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    domain       = resolve_domain_name(data.domain)
    if not domain:
        raise HTTPException(status_code=422, detail="Domain is required.")
    skills_dict  = data.skills_as_dict()

    # Resolve the full question pool (LLM cache first, then static)
    full_questions: list[dict] = []
    if skills_dict and llm_service._CONFIGURED:
        try:
            # Change: use exact distribution during scoring to align with question generation.
            distribution = calculate_question_distribution(skills_dict, total=10)
            full_questions = await llm_service.generate_questions(domain, skills_dict, distribution)
        except Exception:
            pass

    if not full_questions:
        full_questions = QUESTION_BANK.get(_resolve_question_bank_key(domain), [])

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
        user_id=_resolve_user_id(data.user_id, current_user),
        domain=domain,
        assessment_score=quiz_score,
        skill_match=skill_match,
        readiness_score=readiness["readiness_score"],
    ))
    # Addition: record per-question events so adaptive difficulty and analytics can learn from history.
    resolved_user_id = _resolve_user_id(data.user_id, current_user)
    for question in served_questions:
        is_correct = int(user_answer_map.get(question["id"], -1) == question["correct_index"])
        db.add(
            PerformanceEvent(
                user_id=resolved_user_id,
                domain=domain,
                question_id=question["id"],
                topic_tag=question.get("sub_topic", question.get("topic_tag", "general")),
                difficulty=_infer_question_difficulty(question),
                is_correct=is_correct,
                score=100.0 if is_correct else 0.0,
            )
        )
    # Optional profile-level persistence for future cockpit/history pages.
    profile_user_id = _resolve_profile_user_id(data.user_id, current_user)
    if profile_user_id is not None:
        db.add(UserCareerProfile(
            user_id=profile_user_id,
            target_domain=domain,
            strengths=",".join([s for s, v in skills_dict.items() if v >= 4][:5]),
            growth_areas=",".join(list(dict.fromkeys(weak_subtopics))[:5]),
            next_steps="Review weak topics and improve missing domain skills",
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
async def evaluate_test_legacy(
    data: TestSubmission,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    return await evaluate(data, db, current_user)


# ── POST /api/chat  (streaming consultant) ────────────────────────────────────
@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    Streaming endpoint for the AI Career Consultant.
    Returns text/event-stream chunks.
    Gemini remains the primary chat provider; phi3 is a chat-only fallback.
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
            if llm_service._CONFIGURED:
                async for chunk in llm_service.stream_chat(system_prompt, req.message):
                    # SSE format for the existing frontend streaming chat.
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
            else:
                # Addition: chat-only phi3 fallback when Gemini is unavailable.
                for chunk in stream_phi3(req.message, system_prompt):
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as e:
            # Addition: final safety net so chat still works if Gemini fails at runtime.
            try:
                for chunk in stream_phi3(req.message, system_prompt):
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
            except Exception:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/chat/phi3")
def phi3_chat(req: dict):
    # Addition: separate Ollama-backed chatbot endpoint so the Phi-3 feature
    # stays isolated from the existing consultant chat service.
    prompt = str(req.get("message", "")).strip()
    return {"response": query_phi3(prompt)}


# ── POST /recommend-career ────────────────────────────────────────────────────
@app.post("/recommend-career", response_model=RecommendResponse)
def recommend(
    data: SkillsInput,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    skills_list = data.skills_as_list()
    user_skills, recommendations, skill_gap_list, resources = _build_recommendation_payload(skills_list)

    db.add(UserSession(
        user_id=_resolve_user_id(data.user_id, current_user),
        skills_input=",".join(user_skills),
        top_domain=recommendations[0]["domain"],
        confidence=recommendations[0]["confidence"],
    ))
    # Optional snapshot table for export and analytics without touching old model.
    db.add(RecommendationSnapshot(
        user_id=current_user.id if current_user else None,
        top_domain=recommendations[0]["domain"],
        confidence=recommendations[0]["confidence"],
        raw_skills=",".join(user_skills),
    ))
    db.commit()

    return {"recommendations": recommendations, "skill_gap": skill_gap_list, "resources": resources}


@app.post("/api/recommend-career/match", response_model=RecommendResponse)
def recommend_match(
    data: SkillsInput,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    return recommend(data, db, current_user)


@app.post("/api/questions/company")
async def get_company_questions(
    payload: CareerIntelligenceRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    domain = resolve_domain_name(payload.domain or "")
    if not domain:
        raise HTTPException(status_code=422, detail="Domain is required.")

    skills_dict = payload.skills_as_dict()
    distribution = calculate_question_distribution(skills_dict, total=payload.question_count or 10)
    performance_rows = _get_user_performance_rows(db, payload.user_id, current_user, domain)
    adaptive_profile = _compute_adaptive_difficulty(performance_rows)

    if llm_service._CONFIGURED:
        try:
            questions = await generate_company_questions(
                domain=domain,
                skills=skills_dict or {"general": 3},
                distribution=distribution,
                company=payload.company,
                question_count=payload.question_count or 10,
            )
            personalized = personalize_questions(
                {
                    "skills": skills_dict or list(skills_dict.keys()),
                    "weak_topics": payload.weak_topics or [row.topic_tag for row in performance_rows if not bool(row.is_correct)],
                    "domain": domain,
                },
                _apply_adaptive_difficulty(questions, adaptive_profile["difficulty"], limit=payload.question_count or 10),
                limit=payload.question_count or 10,
            )
            return {
                "domain": domain,
                "company": (payload.company or "General").strip(),
                "questions": _strip_correct_index(personalized),
                "total": len(personalized),
                "source": "llm",
                "question_distribution": distribution,
                "adaptive_difficulty": adaptive_profile,
            }
        except Exception:
            pass

    questions = personalize_questions(
        {
            "skills": skills_dict or list(skills_dict.keys()),
            "weak_topics": payload.weak_topics or [row.topic_tag for row in performance_rows if not bool(row.is_correct)],
            "domain": domain,
        },
        _apply_adaptive_difficulty(QUESTION_BANK.get(_resolve_question_bank_key(domain), []), adaptive_profile["difficulty"], limit=payload.question_count or 10),
        limit=payload.question_count or 10,
    )
    questions = _strip_correct_index(questions)
    if not questions:
        raise HTTPException(status_code=404, detail=f"No questions found for '{domain}'.")

    return {
        "domain": domain,
        "company": (payload.company or "General").strip(),
        "questions": questions,
        "total": len(questions),
        "source": "static",
        "question_distribution": distribution,
        "adaptive_difficulty": adaptive_profile,
    }


@app.post("/api/career/intelligence")
def career_intelligence(
    payload: CareerIntelligenceRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    # Optional enriched recommendations endpoint (safe additive feature).
    skills = payload.skills_as_list()
    if not skills:
        raise HTTPException(status_code=422, detail="At least one skill is required.")

    top_domains = payload.top_domains or list(DOMAIN_SKILLS.keys())[:3]
    pathways = build_career_pathways(skills, top_domains)
    performance_rows = _get_user_performance_rows(db, payload.user_id, current_user, payload.domain)
    analytics = build_learning_analytics(
        [
            {
                "topic_tag": row.topic_tag,
                "is_correct": row.is_correct,
                "score": row.score,
                "difficulty": row.difficulty,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in performance_rows
        ]
    )

    personalized_domains = []
    try:
        personalized_domains = predict_domain_recommendations(payload.skills_as_dict() or skills, top_k=3)
    except Exception:
        personalized_domains = []

    next_question_suggestions = personalize_questions(
        {
            "skills": payload.skills_as_dict() or skills,
            "weak_topics": payload.weak_topics or analytics["weaknesses"],
            "domain": payload.domain or (personalized_domains[0]["domain"] if personalized_domains else ""),
        },
        QUESTION_BANK.get(_resolve_question_bank_key(payload.domain or (personalized_domains[0]["domain"] if personalized_domains else "")), []),
        limit=5,
    )

    return {
        "count": len(pathways),
        "items": pathways,
        "personalized_domains": personalized_domains,
        "analytics": analytics,
        "next_questions": _strip_correct_index(next_question_suggestions),
    }


@app.get("/api/analytics/overview")
def analytics_overview(db: Session = Depends(get_db)):
    # Lightweight chart-ready aggregates for optional data visualization pages.
    domain_counts: dict[str, int] = {}
    for row in db.query(UserSession.top_domain).all():
        domain = row[0] or "Unknown"
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    return {
        "top_domains": [{"domain": k, "count": v} for k, v in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)],
        "total_sessions": sum(domain_counts.values()),
    }


@app.get("/api/analytics/practice", response_model=AnalyticsResponse)
def practice_analytics(
    user_id: str | None = None,
    domain: str | None = None,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    # Addition: chart-ready analytics endpoint built from per-question telemetry.
    rows = _get_user_performance_rows(db, user_id, current_user, domain)
    analytics = build_learning_analytics(
        [
            {
                "topic_tag": row.topic_tag,
                "is_correct": row.is_correct,
                "score": row.score,
                "difficulty": row.difficulty,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    )
    return analytics


@app.post("/api/resume/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    # Addition: resume parsing is ML/NLP-backed but still falls back gracefully when parser deps are unavailable.
    content = await file.read()
    extracted_text = extract_text_from_upload(file.filename, content)
    extracted_skills = extract_skills_from_text(extracted_text)

    if not extracted_skills:
        raise HTTPException(status_code=422, detail="No recognizable skills were extracted from the uploaded resume.")

    _, recommendations, _, _ = _build_recommendation_payload(extracted_skills)
    top_recommendation = recommendations[0] if recommendations else None

    db.add(
        ResumeSnapshot(
            user_id=str(current_user.id) if current_user else None,
            filename=file.filename or "resume",
            extracted_text=extracted_text[:5000],
            extracted_skills=",".join(extracted_skills),
            top_domain=top_recommendation["domain"] if top_recommendation else None,
            confidence=top_recommendation["confidence"] if top_recommendation else 0.0,
        )
    )
    db.commit()

    return build_resume_summary(extracted_text, extracted_skills, recommendations)


@app.post("/api/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """
    Task 2: NLP resume upload endpoint.
    Uses pdfplumber/PyMuPDF for text extraction and spaCy NER for skill detection.
    Feeds extracted skills directly into the ML classifier pipeline.
    Also returns semantic similarity matches (Task 3).
    """
    content = await file.read()

    # Task 2: NLP extraction via the new resume_parser utility.
    analysis = build_resume_analysis(file.filename or "resume", content)
    extracted_text   = analysis["extracted_text"]
    extracted_skills = analysis["skills"]
    years_exp        = analysis["years_of_experience"]

    if not extracted_skills:
        raise HTTPException(
            status_code=422,
            detail="No recognizable skills were extracted. Ensure the resume contains technical skill keywords.",
        )

    # Feed extracted skills into the full ML recommendation pipeline.
    _, recommendations, _, _ = _build_recommendation_payload(extracted_skills)
    top_recommendation = recommendations[0] if recommendations else None

    # Task 3: semantic similarity matches as an additional signal.
    semantic_matches: list[dict] = []
    try:
        semantic_matches = find_similar_domains(extracted_skills, top_k=3)
    except Exception:
        pass

    # Persist snapshot.
    db.add(
        ResumeSnapshot(
            user_id=str(current_user.id) if current_user else None,
            filename=file.filename or "resume",
            extracted_text=extracted_text[:5000],
            extracted_skills=",".join(extracted_skills),
            top_domain=top_recommendation["domain"] if top_recommendation else None,
            confidence=top_recommendation["confidence"] if top_recommendation else 0.0,
        )
    )
    db.commit()

    return {
        "extracted_text_preview": extracted_text[:1000],
        "skills":                 extracted_skills,
        "years_of_experience":    years_exp,
        "recommendations":        recommendations,
        "semantic_matches":       semantic_matches,
    }


@app.post("/api/ml/predict")
def ml_predict(data: SkillsInput):
    """
    Task 4: ML prediction endpoint.
    Accepts a list of skills, runs the TF-IDF + RandomForest pipeline,
    and returns top domain matches with confidence scores and feature importance.

    Request:  { "skills": ["python", "pytorch", "nlp"] }
    Response: {
        "top_matches": [{"domain": "AI/ML Engineer", "confidence": 0.89}, ...],
        "feature_importance": ["python", "nlp", "pytorch"]
    }
    """
    from ml.train_model import MODEL_PATH, VECTORIZER_PATH, train

    skills_list = data.skills_as_list()
    if not skills_list:
        raise HTTPException(status_code=422, detail="At least one skill is required.")

    # Load or train artifacts
    try:
        if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
            rf_model   = joblib.load(MODEL_PATH)
            vectorizer = joblib.load(VECTORIZER_PATH)
        else:
            artifact   = train()
            rf_model   = artifact["model"]
            vectorizer = artifact["vectorizer"]
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"ML model unavailable: {exc}")

    skill_doc = " ".join(skills_list)
    try:
        features = vectorizer.transform([skill_doc])
        probs    = rf_model.predict_proba(features)[0]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}")

    # Top matches sorted by confidence
    ranked = sorted(
        zip(rf_model.classes_, probs),
        key=lambda x: x[1],
        reverse=True,
    )
    top_matches = [
        {"domain": domain, "confidence": round(float(conf), 4)}
        for domain, conf in ranked[:5]
        if conf > 0.0
    ]

    # Feature importance: RF feature importances filtered to active input tokens
    feature_names  = np.array(vectorizer.get_feature_names_out())
    importances    = rf_model.feature_importances_
    active_indices = features.nonzero()[1]

    top_features = sorted(
        ((feature_names[i], importances[i]) for i in active_indices),
        key=lambda x: x[1],
        reverse=True,
    )
    feature_importance = [name for name, _ in top_features[:10] if name]

    return {
        "top_matches":        top_matches,
        "feature_importance": feature_importance,
    }


@app.post("/api/export/recommendations")
def export_recommendations(payload: RecommendResponse):
    # Optional CSV export endpoint for downloads/reporting.
    csv_data = recommendations_to_csv([rec.model_dump() for rec in payload.recommendations])
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=recommendations.csv"},
    )


@app.post("/api/export/readiness")
def export_readiness(payload: EvaluateResponse):
    # Optional CSV export endpoint for assessment summaries.
    csv_data = readiness_to_csv(payload.readiness.model_dump())
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=readiness.csv"},
    )
