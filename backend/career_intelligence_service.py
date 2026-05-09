"""
Stage 4: Career Intelligence Service
=====================================
REPLACES the hardcoded utils.py skill-matching with calls to the trained
ML model (ml/artifacts/model.joblib + vectorizer.joblib).

Implements Explainable AI (XAI): returns feature_importances_ so the user
sees WHY they matched a domain (e.g. "Match based on 85% probability for
Python/NLP").

Falls back to the legacy rule-based ranking if the model artifacts are
unavailable, so the server never returns a 500.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


# ── ML-first recommendation ───────────────────────────────────────────────────

def _ml_recommend(
    skills: list[str] | dict[str, int],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Call the trained RandomForest pipeline via ml/trainer.py.
    Returns top-k domain predictions with XAI feature importance.
    """
    try:
        from ml.trainer import predict_with_xai
        return predict_with_xai(skills, top_k=top_k)
    except Exception as exc:
        log.warning("ML trainer predict failed (%s) — trying inference.py fallback", exc)

    try:
        from ml.inference import predict_domain_recommendations
        raw = predict_domain_recommendations(skills, top_k=top_k)
        # Normalise to the richer schema
        return [
            {
                "domain":             r["domain"],
                "confidence":         r["confidence"],
                "probability":        round(r["confidence"] / 100, 4),
                "feature_importance": [
                    {"skill": s, "importance": 0.0, "contribution": 0.0}
                    for s in r.get("top_features", [])
                ],
                "explanation":    r.get("explanation", []),
                "matched_skills": r.get("matched_skills", []),
            }
            for r in raw
        ]
    except Exception as exc2:
        log.warning("inference.py fallback also failed (%s)", exc2)
        return []


def _rule_based_fallback(
    skills: list[str],
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Legacy rule-based ranking — used only when all ML paths fail."""
    try:
        from utils import rank_domains_by_compatibility, normalize_skills
        normalized = normalize_skills(skills)
        ranked = rank_domains_by_compatibility(normalized, limit=top_k)
        return [
            {
                "domain":             r["domain"],
                "confidence":         r["compatibility_score"],
                "probability":        round(r["compatibility_score"] / 100, 4),
                "feature_importance": [],
                "explanation":        [f"Matched {len(r['matched_skills'])} domain skills"],
                "matched_skills":     r["matched_skills"],
            }
            for r in ranked
        ]
    except Exception as exc:
        log.error("Rule-based fallback failed: %s", exc)
        return []


# ── Public API ────────────────────────────────────────────────────────────────

def get_ml_recommendations(
    skills: list[str] | dict[str, int],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Primary entry point for domain recommendations.

    Priority:
      1. ml/trainer.py  (RandomForest + TF-IDF, full XAI)
      2. ml/inference.py (LogisticRegression fallback)
      3. rule-based utils.py (last resort)

    Each result:
        {
          "domain":             str,
          "confidence":         float,   # 0-100
          "probability":        float,   # 0-1
          "feature_importance": list[{skill, importance, contribution}],
          "explanation":        list[str],
          "matched_skills":     list[str],
        }
    """
    skill_list = list(skills.keys()) if isinstance(skills, dict) else list(skills)
    if not skill_list:
        return []

    results = _ml_recommend(skills, top_k=top_k)
    if not results:
        log.info("ML paths returned nothing — using rule-based fallback.")
        results = _rule_based_fallback(skill_list, top_k=top_k)

    return results


def build_career_pathways(
    user_skills: list[str],
    top_domains: list[str],
) -> list[dict[str, Any]]:
    """
    Enrich top domains with ML-derived confidence + XAI explanations
    and a guided career path.

    Keeps the same return shape as the original so /api/career/intelligence
    doesn't break.
    """
    from utils import DOMAIN_SKILLS, normalize_skills, resolve_domain_name

    normalized = normalize_skills(user_skills)
    skill_set  = set(normalized)

    # Get ML confidence for each requested domain
    ml_results = {r["domain"]: r for r in get_ml_recommendations(user_skills, top_k=len(top_domains) + 3)}

    pathways: list[dict[str, Any]] = []
    for domain in top_domains:
        canonical = resolve_domain_name(domain)
        required  = DOMAIN_SKILLS.get(canonical, [])
        if not required:
            continue

        strengths = [s for s in required if s in skill_set][:5]
        missing   = [s for s in required if s not in skill_set][:5]
        ml_data   = ml_results.get(canonical, {})

        next_steps = [
            f"Deepen {strengths[0] if strengths else required[0]} with real projects",
            f"Learn {missing[0] if missing else required[min(1, len(required)-1)]}",
            "Build a portfolio and attempt role-specific assessments",
        ]

        pathways.append({
            "domain":           canonical,
            "strengths":        strengths,
            "skills_to_learn":  missing,
            "career_path":      next_steps,
            # ML enrichment (additive — won't break existing consumers)
            "ml_confidence":    ml_data.get("confidence", 0.0),
            "ml_explanation":   ml_data.get("explanation", []),
            "feature_importance": ml_data.get("feature_importance", []),
        })

    return pathways
