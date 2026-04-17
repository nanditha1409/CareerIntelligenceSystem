"""
ML-first inference helpers with safe fallbacks.

This module intentionally never raises hard failures for user-facing flows.
If a model is missing or malformed, callers can transparently fall back to
the existing rule-based recommendation and question logic.
"""

from __future__ import annotations

import os
from typing import Any

import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from config.domain_manifest import DOMAIN_MANIFEST
from ml.preprocessing import build_skill_document, normalize_skill_phrase, normalize_skills
from ml.train_model import DIFFICULTY_MODEL_PATH, DOMAIN_MODEL_PATH, train_difficulty_model, train_domain_model


def _load_or_train(path: str, trainer):
    if os.path.exists(path):
        return joblib.load(path)
    return trainer()


def predict_domain_recommendations(skills: list[str] | dict[str, int], top_k: int = 3) -> list[dict[str, Any]]:
    """
    Return ML-based ranked domains with confidence and explainability.
    If anything fails, callers should use the legacy ranking logic.
    """
    artifact = _load_or_train(DOMAIN_MODEL_PATH, train_domain_model)
    vectorizer = artifact["vectorizer"]
    model = artifact["model"]

    skill_doc = build_skill_document(skills)
    if not skill_doc.strip():
        return []

    features = vectorizer.transform([skill_doc])
    probs = model.predict_proba(features)[0]
    feature_names = np.array(vectorizer.get_feature_names_out())
    active_indices = features.nonzero()[1]

    ranked_indices = np.argsort(probs)[::-1][:top_k]
    results: list[dict[str, Any]] = []
    normalized_skill_list = normalize_skills(skills.keys() if isinstance(skills, dict) else skills)

    for idx in ranked_indices:
        domain = model.classes_[idx]
        required_skills = DOMAIN_MANIFEST.get(domain, {}).get("required_skills", [])
        matched_skills = [skill for skill in required_skills if normalize_skill_phrase(skill) in normalized_skill_list]

        # Addition: coefficient-weighted active terms provide lightweight explainability without SHAP.
        coefs = model.coef_[idx]
        contributions = sorted(
            ((feature_names[i], coefs[i] * features[0, i]) for i in active_indices),
            key=lambda item: item[1],
            reverse=True,
        )
        explanation = [
            f"{token.replace('_', ' ').title()} contributed strongly"
            for token, weight in contributions[:3]
            if weight > 0
        ]
        if matched_skills and len(explanation) < 4:
            explanation.append(f"Matched domain skills: {', '.join(skill.upper() for skill in matched_skills[:3])}")

        results.append(
            {
                "domain": domain,
                "confidence": round(float(probs[idx]) * 100, 2),
                "matched_skills": matched_skills,
                "explanation": explanation or ["The skill profile aligned closely with this domain."],
                "top_features": [token for token, _ in contributions[:5] if token],
            }
        )

    return results


def predict_next_difficulty(
    recent_score: float,
    avg_score: float,
    weak_topic_rate: float,
    attempts: int,
) -> dict[str, Any]:
    """
    Predict the next question difficulty using a compact supervised model.
    Returns both the label and probabilities so the caller can explain the choice.
    """
    artifact = _load_or_train(DIFFICULTY_MODEL_PATH, train_difficulty_model)
    model = artifact["model"]
    feature_vector = [[recent_score, avg_score, weak_topic_rate, attempts]]
    prediction = model.predict(feature_vector)[0]
    probabilities = model.predict_proba(feature_vector)[0]

    label_probabilities = {
        label: round(float(prob) * 100, 2)
        for label, prob in zip(model.classes_, probabilities)
    }

    return {
        "difficulty": prediction,
        "probabilities": label_probabilities,
    }


def personalize_questions(
    user_profile: dict[str, Any],
    questions: list[dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Re-rank questions using cosine similarity between the user's profile text and
    question text/topic metadata. This keeps personalization data-driven.
    """
    if not questions:
        return []

    weak_topics = user_profile.get("weak_topics", [])
    skills = user_profile.get("skills", [])
    domain = user_profile.get("domain", "")

    profile_doc = " ".join(
        [
            build_skill_document(skills),
            " ".join(str(topic).lower() for topic in weak_topics),
            str(domain).lower(),
        ]
    ).strip()

    if not profile_doc:
        return questions[:limit]

    artifact = _load_or_train(DOMAIN_MODEL_PATH, train_domain_model)
    vectorizer = artifact["vectorizer"]
    question_docs = [
        " ".join(
            [
                str(question.get("text", question.get("question", ""))).lower(),
                str(question.get("sub_topic", question.get("topic_tag", ""))).lower(),
                str(question.get("topic_tag", question.get("sub_topic", ""))).lower(),
            ]
        )
        for question in questions
    ]

    matrix = vectorizer.transform([profile_doc, *question_docs])
    similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()

    ranked = []
    for question, similarity in zip(questions, similarities):
        enriched = dict(question)
        enriched["personalization_score"] = round(float(similarity), 4)
        ranked.append(enriched)

    ranked.sort(key=lambda item: item.get("personalization_score", 0.0), reverse=True)
    return ranked[:limit]


def build_learning_analytics(performance_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate practice analytics into chart-ready data structures."""
    topic_totals: dict[str, dict[str, int]] = {}
    timeline: list[dict[str, Any]] = []

    for row in performance_rows:
        topic = row.get("topic_tag") or "general"
        topic_bucket = topic_totals.setdefault(topic, {"correct": 0, "total": 0})
        topic_bucket["correct"] += int(bool(row.get("is_correct")))
        topic_bucket["total"] += 1

        timeline.append(
            {
                "date": row.get("created_at"),
                "topic": topic,
                "score": row.get("score", 0.0),
                "difficulty": row.get("difficulty", "Medium"),
            }
        )

    topic_accuracy = [
        {
            "topic": topic,
            "accuracy": round((stats["correct"] / stats["total"]) * 100, 1) if stats["total"] else 0.0,
            "attempts": stats["total"],
        }
        for topic, stats in topic_totals.items()
    ]
    topic_accuracy.sort(key=lambda item: item["accuracy"])

    strengths = [item["topic"] for item in topic_accuracy if item["accuracy"] >= 70][:5]
    weaknesses = [item["topic"] for item in topic_accuracy if item["accuracy"] < 50][:5]

    return {
        "topic_accuracy": topic_accuracy,
        "timeline": timeline[-20:],
        "strengths": strengths,
        "weaknesses": weaknesses,
    }
