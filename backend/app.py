import json
import os
import random
import re
from collections import defaultdict
from typing import Any

import joblib
import numpy as np
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
try:
    import ollama
except Exception:
    ollama = None

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
    SKILL_ALIASES,
    normalize_skills, compute_skill_gap,
    calculate_compatibility_score, compute_unified_score,
    get_resources_for_skills,
    rank_domains_by_compatibility, resolve_domain_name,
)
from career_intelligence_service import build_career_pathways, get_ml_recommendations
from services.market_rate_service import compute_market_rate, ALLOWED_DOMAINS as SUPPORTED_DOMAINS
from report_service import recommendations_to_csv, readiness_to_csv
from config.domain_manifest import DOMAIN_MANIFEST, LEGACY_DOMAIN_ALIASES
from coding_question_bank import CODING_QUESTION_BANK
from services.company_quiz_service import generate_company_questions
from services.code_execution_service import execute_code_submission
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
PROFILE_DOMAINS = [
    "AI/ML Engineer",
    "Data Scientist",
    "Data Analyst",
    "Full Stack Developer",
    "Software Engineer",
    "DevOps Engineer",
    "Cybersecurity Analyst",
    "UI/UX Designer",
    "Backend Developer",
]
EXPERIENCE_SIGNAL_WEIGHTS = {
    "no_experience": 0.7,
    "intern": 0.85,
    "intermediate": 1.0,
    "advance": 1.15,
}
MARKET_DEMAND_WEIGHT = {
    "Very High": 1.20,
    "High": 1.10,
    "Medium": 1.00,
    "Low": 0.90,
}
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:latest")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_OPTIONS = {
    "temperature": 0.3,
    "num_predict": 140,
    "num_ctx": 1536,
}
CHATBOT_SYSTEM_PROMPT = """You are NextStep AI, an expert career counsellor specialising exclusively in the following 9 tech career domains:

1. AI/ML Engineer
2. Data Scientist
3. Data Analyst
4. Full Stack Developer
5. Software Engineer
6. DevOps Engineer
7. Cybersecurity Analyst
8. UI/UX Designer
9. Backend Developer

You help users with:
- Career path guidance and roadmaps for these 9 domains
- Skill gap analysis and learning resources
- Salary expectations and market demand in India
- Interview preparation tips and common questions
- Technology stack recommendations
- Project ideas to build portfolio

STRICT RULES:
- Only answer questions related to these 9 tech career domains and career guidance
- If asked about anything unrelated (politics, cooking, general knowledge, etc.), respond: "I'm NextStep AI, your career intelligence assistant. I can only help with questions about tech careers in AI/ML, Data Science, Data Analytics, Full Stack, Software Engineering, DevOps, Cybersecurity, UI/UX Design, or Backend Development."
- Always be specific, actionable, and encouraging
- Reference current market trends (2024-2025 Indian tech market)
- Keep responses concise but complete
"""


def _rule_based_chat_fallback(user_message: str) -> str:
    message = (user_message or "").strip().lower()
    domains = [
        "AI/ML Engineer",
        "Data Scientist",
        "Data Analyst",
        "Full Stack Developer",
        "Software Engineer",
        "DevOps Engineer",
        "Cybersecurity Analyst",
        "UI/UX Designer",
        "Backend Developer",
    ]

    selected_domain = None
    for domain in domains:
        if domain.lower() in message:
            selected_domain = domain
            break

    if not selected_domain and not any(
        token in message
        for token in [
            "career",
            "roadmap",
            "salary",
            "interview",
            "skills",
            "domain",
            "developer",
            "engineer",
            "analyst",
            "design",
        ]
    ):
        return (
            "I'm NextStep AI, your career intelligence assistant. I can only help with questions about tech careers in "
            "AI/ML, Data Science, Data Analytics, Full Stack, Software Engineering, DevOps, Cybersecurity, UI/UX Design, "
            "or Backend Development."
        )

    if selected_domain:
        demand = DOMAIN_DATA.get(selected_domain, {}).get("demand", "Medium")
        salary = DOMAIN_DATA.get(selected_domain, {}).get("salary", "N/A")
        top_skills = DOMAIN_SKILLS.get(selected_domain, [])[:5]
        return (
            f"Great choice: {selected_domain}.\n"
            f"- Market demand (India, 2024-2025): {demand}\n"
            f"- Typical salary band: {salary}\n"
            f"- Core skills to focus now: {', '.join(top_skills)}\n"
            "- 30-day plan: Week 1 fundamentals, Week 2 hands-on mini project, Week 3 interview prep, Week 4 portfolio polish.\n"
            "- Project idea: Build one production-style project and publish code + README + demo."
        )

    return (
        "Here is a practical way to choose among the 9 supported domains:\n"
        "1) Pick your strongest skills (coding, data, infra, or design).\n"
        "2) Match them to one target domain and learn its top 5 core skills.\n"
        "3) Build 2 portfolio projects and start interview prep.\n"
        "If you share your current skills, I can suggest the best-fit domain and a 4-week roadmap."
    )


def _stream_ollama_http(messages: list[dict[str, str]]):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
        "options": OLLAMA_OPTIONS,
        "keep_alive": "20m",
    }
    with requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json=payload,
        stream=True,
        timeout=(3.0, 120.0),
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = (chunk.get("message") or {}).get("content", "")
            if text:
                yield text


def _serialize_questions_for_frontend(questions: list[dict]) -> list[dict]:
    """Return questions safe for the frontend — no answer key exposed."""
    safe_questions: list[dict] = []
    for question in questions:
        payload = {
            "id": question["id"],
            "text": question.get("text", question.get("question", "")),
            "question": question.get("text", question.get("question", "")),
            "sub_topic": question.get("sub_topic", question.get("topic_tag", "")),
            "topic_tag": question.get("topic_tag", question.get("sub_topic", "")),
            "type": question.get("type", "mcq"),
        }
        if payload["type"] == "coding":
            payload["supported_languages"] = ["python", "java"]
            payload["starter_code_map"] = question.get("starter_code", {})
        else:
            payload["options"] = question["options"]
        safe_questions.append(payload)
    return safe_questions


def _sample_static(domain: str, n: int = 10) -> list[dict]:
    pool = QUESTION_BANK.get(_resolve_question_bank_key(domain), [])
    if not pool:
        return []
    sampled = random.sample(pool, min(n, len(pool)))
    return _serialize_questions_for_frontend(sampled)


def _resolve_question_bank_key(domain: str) -> str:
    canonical_domain = resolve_domain_name(domain)

    # 1. Exact match
    if canonical_domain in QUESTION_BANK:
        return canonical_domain

    # 2. Case-insensitive match
    for key in QUESTION_BANK:
        if key.lower() == canonical_domain.lower():
            return key

    # 3. Slash ↔ hyphen normalisation (e.g. "AI/ML Engineer" ↔ "AI-ML Engineer")
    normalised = canonical_domain.replace("/", "-").replace(" ", " ")
    for key in QUESTION_BANK:
        if key.replace("/", "-").lower() == normalised.lower():
            return key

    # 4. Legacy alias table
    for legacy_domain, current_domain in LEGACY_DOMAIN_ALIASES.items():
        if current_domain.lower() == canonical_domain.lower() and legacy_domain in QUESTION_BANK:
            return legacy_domain

    # 5. Partial / substring match as last resort
    for key in QUESTION_BANK:
        key_core = key.lower().replace("/", "").replace("-", "").replace(" ", "")
        dom_core = canonical_domain.lower().replace("/", "").replace("-", "").replace(" ", "")
        if key_core == dom_core:
            return key

    return canonical_domain


def _get_coding_questions(domain: str) -> list[dict]:
    canonical_domain = resolve_domain_name(domain)
    if canonical_domain in CODING_QUESTION_BANK:
        return CODING_QUESTION_BANK[canonical_domain]

    for key in CODING_QUESTION_BANK:
        if key.lower() == canonical_domain.lower():
            return CODING_QUESTION_BANK[key]

    for legacy_domain, current_domain in LEGACY_DOMAIN_ALIASES.items():
        if current_domain.lower() == canonical_domain.lower() and legacy_domain in CODING_QUESTION_BANK:
            return CODING_QUESTION_BANK[legacy_domain]

    return []


def _enforce_domain_restriction(domain: str) -> str:
    """
    Resolve to canonical domain name and verify it is one of the 9 supported domains.
    Raises HTTP 422 if the resolved domain is not in SUPPORTED_DOMAINS.
    """
    canonical = resolve_domain_name(domain)
    if canonical not in SUPPORTED_DOMAINS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"'{domain}' is not a supported domain. Supported domains: "
                + ", ".join(sorted(SUPPORTED_DOMAINS))
            ),
        )
    return canonical


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
        parsed: dict[str, Any] = {}
        for key, value in raw_answers.items():
            if isinstance(value, int) or str(value).lstrip("-").isdigit():
                parsed[str(key)] = int(value)
            elif isinstance(value, str):
                parsed[str(key)] = value
        return parsed
    for item in raw_answers:
        if isinstance(item, dict):
            qid = str(item.get("id", item.get("question_id", "")))
            val = item.get("answer", item.get("selected", None))
            if qid and val is not None:
                try:
                    result[qid] = int(val)
                except (ValueError, TypeError):
                    if isinstance(val, str):
                        result[qid] = val
    return result


def _normalize_code_answer(answer: Any) -> str:
    return re.sub(r"\s+", "", str(answer or "").strip().lower())


def _is_coding_answer_correct(question: dict, answer: Any) -> bool:
    normalized_answer = _normalize_code_answer(answer)
    if not normalized_answer:
        return False
    groups = question.get("validation", {}).get("groups", [])
    if not groups:
        return False
    for group in groups:
        alternatives = [_normalize_code_answer(option) for option in group]
        if not any(option and option in normalized_answer for option in alternatives):
            return False
    return True


def _score_answers(
    served_questions: list[dict],
    user_answer_map: dict[str, Any],
) -> tuple[int, float, list[str]]:
    correct, weak = 0, []
    for q in served_questions:
        answer = user_answer_map.get(q["id"], -1)
        is_correct = (
            _is_coding_answer_correct(q, answer)
            if q.get("type") == "coding"
            else answer == q["correct_index"]
        )
        if is_correct:
            correct += 1
        else:
            weak.append(q.get("sub_topic", q.get("topic_tag", "")))
    total = len(served_questions)
    return correct, round((correct / total) * 100, 1) if total else 0.0, weak


def _detect_weak_topics(served_questions: list[dict], user_answer_map: dict[str, Any]) -> list[dict]:
    stats: dict[str, dict] = defaultdict(lambda: {"wrong": 0, "total": 0})
    for q in served_questions:
        tag = q.get("sub_topic", q.get("topic_tag", ""))
        stats[tag]["total"] += 1
        answer = user_answer_map.get(q["id"], -1)
        is_correct = (
            _is_coding_answer_correct(q, answer)
            if q.get("type") == "coding"
            else answer == q["correct_index"]
        )
        if not is_correct:
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


@app.post("/api/market-rate")
def get_market_rate(payload: dict):
    """
    GBM-inspired market rate prediction endpoint.
    Computes salary range + confidence score based on:
      domain demand, experience level, skill proficiency,
      readiness_score (optional), quiz_score (optional).
    No hardcoded salary values — all outputs derived from input signals.
    """
    domain           = str(payload.get("domain", "")).strip()
    experience_level = str(payload.get("experience_level", "no_experience")).strip()
    skills_raw       = payload.get("skills", {})

    # Optional assessment signals — elevate prediction accuracy when provided
    readiness_raw = payload.get("readiness_score")
    quiz_raw      = payload.get("quiz_score")

    readiness_score: float | None = None
    quiz_score:      float | None = None
    try:
        if readiness_raw is not None:
            readiness_score = max(0.0, min(100.0, float(readiness_raw)))
    except (TypeError, ValueError):
        pass
    try:
        if quiz_raw is not None:
            quiz_score = max(0.0, min(100.0, float(quiz_raw)))
    except (TypeError, ValueError):
        pass

    if not domain:
        raise HTTPException(status_code=422, detail="domain is required.")

    canonical = resolve_domain_name(domain)
    if canonical not in SUPPORTED_DOMAINS:
        raise HTTPException(
            status_code=422,
            detail=f"'{domain}' is not a supported domain. Supported: {sorted(SUPPORTED_DOMAINS)}",
        )

    skills: dict[str, int] = {}
    if isinstance(skills_raw, dict):
        for k, v in skills_raw.items():
            if isinstance(k, str) and k.strip():
                try:
                    skills[k.strip()] = max(1, min(5, int(v)))
                except (TypeError, ValueError):
                    skills[k.strip()] = 3

    result = compute_market_rate(
        canonical, experience_level, skills,
        readiness_score=readiness_score,
        quiz_score=quiz_score,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Market data not available for '{canonical}'.")
    return result


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


def _extract_project_signals(project_text: str) -> tuple[list[str], dict[str, float], dict[str, list[str]]]:
    blob = (project_text or "").lower()
    if not blob.strip():
        return [], {}, {}

    derived_skills: list[str] = []
    for skill in SKILLS_LIST:
        aliases = {skill, skill.replace("-", " "), skill.replace("/", " ")}
        if any(alias and alias in blob for alias in aliases):
            derived_skills.append(skill)
    for alias, canonical in SKILL_ALIASES.items():
        if alias in blob and canonical not in derived_skills:
            derived_skills.append(canonical)

    project_domain_bonus: dict[str, float] = {}
    project_reasons: dict[str, list[str]] = {}
    for domain in PROFILE_DOMAINS:
        manifest = DOMAIN_MANIFEST.get(domain, {})
        matched_terms: list[str] = []
        for keyword in manifest.get("keywords", []) + manifest.get("required_skills", []):
            key = str(keyword).lower().strip()
            if key and key in blob:
                matched_terms.append(str(keyword))
        if matched_terms:
            unique_terms = list(dict.fromkeys(matched_terms))
            project_domain_bonus[domain] = min(16.0, len(unique_terms) * 2.5)
            project_reasons[domain] = unique_terms[:3]

    return list(dict.fromkeys(derived_skills)), project_domain_bonus, project_reasons


def _build_recommendation_payload(
    skills_list: list[str],
    preferred_domain: str | None = None,
    experience_level: str | None = None,
    project_text: str = "",
) -> tuple[list[str], list[dict], list[dict], list[dict]]:
    normalized_skills = normalize_skills(skills_list)
    derived_skills, project_domain_bonus, project_reasons = _extract_project_signals(project_text)
    effective_skills = list(dict.fromkeys(normalized_skills + derived_skills))
    experience_weight = EXPERIENCE_SIGNAL_WEIGHTS.get((experience_level or "").strip().lower(), 1.0)
    preferred_domain = resolve_domain_name(preferred_domain or "") if preferred_domain else None
    ranked_matches: list[dict[str, Any]] = []

    # Task 1: ML-first domain recommendations with coefficient-based explanations.
    try:
        ml_matches = predict_domain_recommendations(effective_skills, top_k=9)
        for match in ml_matches:
            match["confidence"] = round(min(99.0, match["confidence"] * experience_weight), 1)
        for match in ml_matches:
            ranked_matches.append(
                {
                    "domain": match["domain"],
                    "matched_skills": match["matched_skills"],
                    "missing_skills": [
                        skill for skill in DOMAIN_SKILLS.get(match["domain"], [])
                        if skill not in set(effective_skills)
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
        clf_predictions = get_prediction_confidence(effective_skills, top_k=9)
        for pred in clf_predictions:
            classifier_results[pred["domain"]] = pred
    except Exception:
        pass

    # Task 3: Semantic similarity scores (replaces hardcoded keyword→domain mapping).
    semantic_results: dict[str, dict] = {}
    try:
        sem_matches = find_similar_domains(effective_skills, top_k=9)
        for sem in sem_matches:
            semantic_results[sem["domain"]] = sem
    except Exception:
        pass

    # Addition: retain the original deterministic ranking as a production fallback.
    if not ranked_matches:
        ranked_matches = rank_domains_by_compatibility(effective_skills, limit=9)

    if not ranked_matches:
        raise HTTPException(
            status_code=400,
            detail="No recognized domain-aligned skills found. Try skills like python, sql, ml, react, docker, aws, or figma.",
        )

    for match in ranked_matches:
        domain = match["domain"]
        compat_pct = calculate_compatibility_score(effective_skills, domain)
        clf_data = classifier_results.get(domain, {})
        sem_data = semantic_results.get(domain, {})
        base_score = compute_unified_score(
            {
                "ml": match.get("confidence"),
                "clf": clf_data.get("confidence_score"),
                "sem": sem_data.get("similarity_score"),
                "compat": compat_pct,
            }
        )
        bonus = 0.0
        explanation = list(match.get("explanation", []))

        if preferred_domain and domain == preferred_domain:
            bonus += 8.0
            explanation.append("Your selected target domain aligns with this path.")

        project_bonus = project_domain_bonus.get(domain, 0.0) * experience_weight
        if project_bonus:
            bonus += project_bonus
            reasons = ", ".join(project_reasons.get(domain, [])[:3])
            explanation.append(f"Project experience signals align here ({reasons}).")

        if derived_skills:
            explanation.append(f"Project details added signals like {', '.join(derived_skills[:3])}.")

        match["unified_score"] = base_score
        match["compatibility_score"] = round(min(99.0, base_score + bonus), 1)
        match["base_compatibility_pct"] = compat_pct
        match["explanation"] = list(dict.fromkeys(explanation))[:4]

    for match in ranked_matches:
        demand_str = DOMAIN_DATA.get(match["domain"], {}).get("demand", "Medium")
        demand_mult = MARKET_DEMAND_WEIGHT.get(demand_str, 1.0)
        match["compatibility_score"] = round(min(99.0, match["compatibility_score"] * demand_mult), 1)
        match["market_weight_applied"] = demand_mult

    ranked_matches.sort(
        key=lambda item: (
            item["compatibility_score"],
            len(item.get("matched_skills", [])),
            item.get("keyword_match_count", 0),
        ),
        reverse=True,
    )
    ranked_matches = ranked_matches[:3]

    recommendations: list[dict] = []
    skill_gap_list: list[dict] = []
    all_missing: list[str] = []

    for match in ranked_matches:
        domain = match["domain"]
        gap = compute_skill_gap(effective_skills, domain)
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
                "compatibility_score": match["compatibility_score"],
                "unified_score":      match["unified_score"],
                "salary":             DOMAIN_DATA[domain]["salary"],
                "demand":             DOMAIN_DATA[domain]["demand"],
                "reason":             ml_reasoning or [f"You match {skill.upper()}" for skill in matched_skills] or ["Keyword mapping indicates domain alignment"],
                "top_skills":         match.get("top_features", [])[:3] or matched_skills[:3] or fallback_skills,
                "model_source":       model_source,
                "market_weight_applied": match.get("market_weight_applied", 1.0),
                "experience_weight_applied": experience_weight,
                # Task 1 & 3 extensions (backward-compatible optional fields):
                "confidence_score":   confidence_score,
                "matching_keywords":  matching_keywords,
                "feature_importance": feature_importance,
            }
        )
        skill_gap_list.append(gap)
        all_missing.extend(gap["missing_skills"])

    resources = get_resources_for_skills(list(dict.fromkeys(all_missing))[:8])
    return effective_skills, recommendations, skill_gap_list, resources


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
    level: str = "easy",
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
    level = (level or "easy").strip().lower()
    if level not in {"easy", "medium"}:
        raise HTTPException(status_code=422, detail="Assessment level must be easy or medium.")

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

    if level == "medium":
        coding_questions = _get_coding_questions(domain)
        if not coding_questions:
            raise HTTPException(status_code=404, detail=f"No medium coding questions found for '{domain}'.")
        return {
            "domain": domain,
            "questions": _serialize_questions_for_frontend(coding_questions),
            "total": len(coding_questions),
            "source": "coding-static",
            "assessment_level": "medium",
            "question_distribution": calculate_question_distribution(skills_dict, total=len(coding_questions)),
            "adaptive_difficulty": adaptive_profile,
        }

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
                "questions": _serialize_questions_for_frontend(personalized),
                "total": len(personalized),
                "source": "llm",
                "assessment_level": "easy",
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
    questions = _serialize_questions_for_frontend(personalized)
    if not questions:
        # Last resort: pick questions from any available domain
        for fallback_key, fallback_questions in QUESTION_BANK.items():
            if fallback_questions:
                sampled = _serialize_questions_for_frontend(random.sample(fallback_questions, min(10, len(fallback_questions))))
                return {
                    "domain": domain,
                    "questions": sampled,
                    "total": len(sampled),
                    "source": "fallback",
                    "assessment_level": "easy",
                    "question_distribution": distribution,
                    "adaptive_difficulty": adaptive_profile,
                    "warning": f"No questions found for '{domain}', showing general questions.",
                }
        raise HTTPException(status_code=404, detail=f"No questions found for '{domain}'.")
    return {
        "domain": domain,
        "questions": questions,
        "total": len(questions),
        "source": "static",
        "assessment_level": "easy",
        "question_distribution": distribution,
        "adaptive_difficulty": adaptive_profile,
    }


# ── Legacy path ───────────────────────────────────────────────────────────────
@app.get("/get-questions/{domain:path}")
async def get_questions_legacy(
    domain: str,
    skills: str = "",
    level: str = "easy",
    user_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    return await get_questions(domain, skills, level, user_id, db, current_user)


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
    assessment_level = (data.assessment_level or "easy").strip().lower()
    programming_language = (data.programming_language or "").strip().lower() or None

    # Resolve the full question pool (LLM cache first, then static)
    full_questions: list[dict] = []
    if assessment_level == "medium":
        full_questions = _get_coding_questions(domain)
    elif skills_dict and llm_service._CONFIGURED:
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
    execution_results: list[dict[str, Any]] = []
    if assessment_level == "medium":
        if programming_language not in {"python", "java"}:
            raise HTTPException(status_code=422, detail="Select Python or Java for medium-level assessments.")

        weak_subtopics: list[str] = []
        correct = 0
        for question in served_questions:
            submitted_code = str(user_answer_map.get(question["id"], "")).strip()
            if not submitted_code:
                execution_results.append(
                    {
                        "question_id": question["id"],
                        "sub_topic": question.get("sub_topic", question.get("topic_tag", "general")),
                        "language": programming_language,
                        "passed": False,
                        "passed_tests": 0,
                        "total_tests": len(question.get("test_cases", [])),
                        "error_message": "No code submitted.",
                    }
                )
                weak_subtopics.append(question.get("sub_topic", question.get("topic_tag", "general")))
                continue

            execution_result = execute_code_submission(question, submitted_code, programming_language)
            passed = bool(execution_result.get("passed"))
            if passed:
                correct += 1
            else:
                weak_subtopics.append(question.get("sub_topic", question.get("topic_tag", "general")))

            execution_results.append(
                {
                    "question_id": question["id"],
                    "sub_topic": question.get("sub_topic", question.get("topic_tag", "general")),
                    "language": programming_language,
                    "passed": passed,
                    "passed_tests": int(execution_result.get("passed_tests", 0)),
                    "total_tests": int(execution_result.get("total_tests", len(question.get("test_cases", [])))),
                    "error_message": execution_result.get("error_message"),
                }
            )

        quiz_score = round((correct / len(served_questions)) * 100, 1) if served_questions else 0.0
        topic_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"wrong": 0, "total": 0})
        for item in execution_results:
            topic = item["sub_topic"]
            topic_stats[topic]["total"] += 1
            if not item["passed"]:
                topic_stats[topic]["wrong"] += 1
        weak_sub_topics = [
            {"sub_topic": topic, "wrong": stats["wrong"], "total": stats["total"]}
            for topic, stats in topic_stats.items()
            if stats["total"] > 0 and (stats["wrong"] / stats["total"]) > 0.4
        ]
        weak_sub_topics.sort(key=lambda item: item["wrong"] / item["total"], reverse=True)
    else:
        correct, quiz_score, weak_subtopics = _score_answers(served_questions, user_answer_map)
        weak_sub_topics = _detect_weak_topics(served_questions, user_answer_map)

    # ── Weighted readiness: (0.6 × weighted_skill_match) + (0.4 × quiz_score) ─
    skill_match = _weighted_skill_match(skills_dict, domain) if skills_dict else 0.0
    readiness   = _compute_readiness(skill_match, quiz_score, domain)

    # ── Feedback ──────────────────────────────────────────────────────────────
    if quiz_score >= 80:
        feedback = "Excellent — your assessment performance is strong."
    elif quiz_score >= 60:
        feedback = "Good progress. Review the flagged sub-topics to level up."
    elif quiz_score >= 40:
        feedback = "Keep going — focus on the weak areas identified below."
    else:
        feedback = "Start with the fundamentals. Use the resources below to build a solid base."

    if assessment_level == "medium":
        failed_runs = [item for item in execution_results if not item["passed"] and item.get("error_message")]
        if failed_runs:
            feedback += " Some coding challenges returned execution errors, so review the messages in the results panel."

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
        raw_answer = user_answer_map.get(question["id"], -1)
        is_correct = int(
            _is_coding_answer_correct(question, raw_answer)
            if question.get("type") == "coding"
            else raw_answer == question["correct_index"]
        )
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
        "total_questions": len(served_questions),
        "assessment_level": assessment_level,
        "feedback":        feedback,
        "weak_sub_topics": weak_sub_topics,
        "weak_areas":      list(dict.fromkeys(weak_subtopics)),
        "readiness":       readiness,
        "resources":       resources,
        "programming_language": programming_language,
        "execution_results": execution_results or None,
    }


# ── POST /evaluate-test  (legacy) ─────────────────────────────────────────────
@app.post("/evaluate-test", response_model=EvaluateResponse)
async def evaluate_test_legacy(
    data: TestSubmission,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    return await evaluate(data, db, current_user)


@app.post("/api/chat")
async def chat_with_phi3(payload: dict):
    user_message = str(payload.get("message", "")).strip()
    history = payload.get("history", [])

    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")

    weak_areas = payload.get("weak_areas") or []
    domain = str(payload.get("domain", "")).strip()
    quiz_score = payload.get("quiz_score")
    readiness_score = payload.get("readiness_score")
    if domain:
        weak_str = ", ".join(weak_areas) if isinstance(weak_areas, list) and weak_areas else "none identified"
        chatbot_prompt = (
            f"{CHATBOT_SYSTEM_PROMPT}\n\n"
            f"Assessment context: Domain={domain}, Quiz score={quiz_score}, "
            f"Readiness score={readiness_score}, Weak areas={weak_str}."
        )
    else:
        chatbot_prompt = CHATBOT_SYSTEM_PROMPT

    messages = [{"role": "system", "content": chatbot_prompt}]
    if isinstance(history, list):
        for h in history[-6:]:
            role = h.get("role")
            content = h.get("content")
            if role in {"user", "assistant", "system"} and isinstance(content, str):
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    async def generate():
        try:
            if ollama is not None:
                stream = ollama.chat(
                    model=OLLAMA_MODEL,
                    messages=messages,
                    stream=True,
                    options=OLLAMA_OPTIONS,
                    keep_alive="20m",
                )
                for chunk in stream:
                    text = chunk.get("message", {}).get("content", "")
                    if text:
                        yield f"data: {json.dumps({'text': text})}\n\n"
            else:
                for text in _stream_ollama_http(messages):
                    yield f"data: {json.dumps({'text': text})}\n\n"
        except Exception:
            try:
                async for token in llm_service.stream_chat(chatbot_prompt, user_message):
                    yield f"data: {json.dumps({'text': token})}\n\n"
            except Exception:
                fallback_text = _rule_based_chat_fallback(user_message)
                yield f"data: {json.dumps({'text': fallback_text})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/chat/phi3")
def phi3_chat(req: dict):
    return {"response": "Phi-3 is not available. Use the main consultant chat which is powered by Gemini."}


# ── POST /recommend-career ────────────────────────────────────────────────────
@app.post("/recommend-career", response_model=RecommendResponse)
def recommend(
    data: SkillsInput,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    skills_list = data.skills_as_list()
    user_skills, recommendations, skill_gap_list, resources = _build_recommendation_payload(
        skills_list,
        preferred_domain=data.preferred_domain,
        experience_level=data.experience_level,
        project_text=data.project_text(),
    )

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
                "questions": _serialize_questions_for_frontend(personalized),
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
    questions = _serialize_questions_for_frontend(questions)
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
        "next_questions": _serialize_questions_for_frontend(next_question_suggestions),
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


@app.post("/api/v1/ml/recommend")
def ml_recommend_v1(data: SkillsInput):
    """
    Stage 4 — ML-native domain recommendation.
    Uses the trained RandomForest + TF-IDF pipeline (ml/artifacts/).
    Returns the same JSON shape as /recommend-career so the UI works unchanged.
    Falls back to llm_service logic if the model artifacts are unavailable.
    """
    skills_list = data.skills_as_list()
    if not skills_list:
        raise HTTPException(status_code=422, detail="At least one skill is required.")

    # ML-first path
    ml_results = get_ml_recommendations(data.skills if isinstance(data.skills, dict) else skills_list, top_k=5)

    if not ml_results:
        # Fallback: reuse the existing full recommendation pipeline
        try:
            _, recommendations, skill_gap_list, resources = _build_recommendation_payload(skills_list)
            return {"recommendations": recommendations, "skill_gap": skill_gap_list, "resources": resources, "source": "fallback"}
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Recommendation unavailable: {exc}")

    # Shape ML results into the existing RecommendResponse schema
    recommendations: list[dict] = []
    skill_gap_list:  list[dict] = []
    all_missing:     list[str]  = []

    for r in ml_results[:3]:
        domain = r["domain"]
        gap    = compute_skill_gap(skills_list, domain)
        recommendations.append({
            "domain":             domain,
            "confidence":         r["confidence"],
            "compatibility_score": r["confidence"],
            "unified_score":      r["confidence"],
            "salary":             DOMAIN_DATA.get(domain, {}).get("salary", "N/A"),
            "demand":             DOMAIN_DATA.get(domain, {}).get("demand", "N/A"),
            "reason":             r["explanation"],
            "top_skills":         r["matched_skills"][:3] or DOMAIN_SKILLS.get(domain, [])[:3],
            "model_source":       "ml_trainer",
            "confidence_score":   r["confidence"],
            "matching_keywords":  r["matched_skills"],
            "feature_importance": [
                {"skill": fi["skill"], "importance": fi["importance"]}
                for fi in r["feature_importance"][:5]
            ],
        })
        skill_gap_list.append(gap)
        all_missing.extend(gap["missing_skills"])

    resources = get_resources_for_skills(list(dict.fromkeys(all_missing))[:8])
    return {
        "recommendations": recommendations,
        "skill_gap":       skill_gap_list,
        "resources":       resources,
        "source":          "ml_trainer",
    }


@app.post("/api/v1/ml/parse-resume")
async def ml_parse_resume_v1(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """
    Stage 4 — NLP resume parsing endpoint.
    Uses spaCy NER + cosine similarity (nlp_engine.py) to extract skills
    and score them against domain centroids.
    Returns the same JSON shape as /api/upload-resume so the UI works unchanged.
    Falls back to the existing resume_parser if nlp_engine is unavailable.
    """
    content = await file.read()

    # Primary: Stage 3 NLP engine
    try:
        from services.nlp_engine import parse_resume_nlp
        from utils.resume_parser import extract_text_from_file
        text     = extract_text_from_file(file.filename or "resume", content)
        nlp_data = parse_resume_nlp(text)
        extracted_skills = nlp_data["skills"]
        domain_scores    = nlp_data["domain_scores"]
        years_exp        = nlp_data["years_experience"]
    except Exception:
        # Fallback: existing NLP parser
        analysis         = build_resume_analysis(file.filename or "resume", content)
        extracted_skills = analysis["skills"]
        domain_scores    = []
        years_exp        = analysis.get("years_of_experience")
        text             = analysis.get("extracted_text", "")

    if not extracted_skills:
        raise HTTPException(
            status_code=422,
            detail="No recognizable skills extracted. Ensure the resume contains technical keywords.",
        )

    # Feed into ML recommendation pipeline
    ml_results = get_ml_recommendations(extracted_skills, top_k=3)
    if not ml_results:
        _, recommendations, _, _ = _build_recommendation_payload(extracted_skills)
    else:
        recommendations = [
            {
                "domain":             r["domain"],
                "confidence":         r["confidence"],
                "salary":             DOMAIN_DATA.get(r["domain"], {}).get("salary", "N/A"),
                "demand":             DOMAIN_DATA.get(r["domain"], {}).get("demand", "N/A"),
                "reason":             r["explanation"],
                "top_skills":         r["matched_skills"][:3],
                "model_source":       "ml_trainer",
                "confidence_score":   r["confidence"],
                "matching_keywords":  r["matched_skills"],
                "feature_importance": [
                    {"skill": fi["skill"], "importance": fi["importance"]}
                    for fi in r["feature_importance"][:5]
                ],
            }
            for r in ml_results
        ]

    top = recommendations[0] if recommendations else {}

    # Persist snapshot
    db.add(ResumeSnapshot(
        user_id=str(current_user.id) if current_user else None,
        filename=file.filename or "resume",
        extracted_text=text[:5000],
        extracted_skills=",".join(extracted_skills),
        top_domain=top.get("domain"),
        confidence=top.get("confidence", 0.0),
    ))
    db.commit()

    return {
        "extracted_text_preview": text[:1000],
        "skills":                 extracted_skills,
        "years_of_experience":    years_exp,
        "recommendations":        recommendations,
        "domain_scores":          domain_scores,
        "source":                 "nlp_engine",
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
