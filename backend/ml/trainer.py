"""
Stage 2: The Brain — Local Model Training
==========================================
Loads the generated dataset, trains a TF-IDF + RandomForestClassifier pipeline,
logs a full classification report, and saves artifacts to ml/artifacts/.

Artifacts:
  - ml/artifacts/model.joblib       (RandomForestClassifier)
  - ml/artifacts/vectorizer.joblib  (TfidfVectorizer)
  - ml/artifacts/label_meta.joblib  (domain list + feature names for XAI)

Run from backend/:
    python ml/trainer.py
"""

from __future__ import annotations

import os
import sys
import logging

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ml.similarity import evaluate_similarity_engine
from ml.train_model import train_difficulty_model
from services.nlp_engine import evaluate_skill_extractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

BASE_DIR        = os.path.dirname(os.path.dirname(__file__))
DATA_DIR        = os.path.join(BASE_DIR, "data")
ARTIFACTS_DIR   = os.path.join(BASE_DIR, "ml", "artifacts")
TRAINING_CSV    = os.path.join(DATA_DIR, "training_data.csv")

MODEL_PATH      = os.path.join(ARTIFACTS_DIR, "model.joblib")
VECTORIZER_PATH = os.path.join(ARTIFACTS_DIR, "vectorizer.joblib")
META_PATH       = os.path.join(ARTIFACTS_DIR, "label_meta.joblib")

# Legacy path — keeps inference.py working without changes
LEGACY_MODEL_DIR  = os.path.join(BASE_DIR, "models")
DOMAIN_MODEL_PATH = os.path.join(LEGACY_MODEL_DIR, "ml_domain_recommender.joblib")


# ── Data loading ──────────────────────────────────────────────────────────────

def _ensure_data() -> None:
    """Auto-generate training data if the CSV is missing."""
    if not os.path.exists(TRAINING_CSV):
        log.info("training_data.csv not found — running data_generator ...")
        from ml.data_generator import main as gen_main
        gen_main()


def load_data() -> pd.DataFrame:
    """
    Load training_data.csv.
    Accepts both the new schema (skills_text / domain_label) and the legacy
    schema (skills / job_role) so this trainer works with any existing CSV.
    """
    _ensure_data()
    df = pd.read_csv(TRAINING_CSV)
    df.columns = [c.strip().lower() for c in df.columns]

    # Normalise column names to skills_text / domain_label
    if "skills_text" not in df.columns:
        for alias in ("skills", "skill_text", "text"):
            if alias in df.columns:
                df = df.rename(columns={alias: "skills_text"})
                break
    if "domain_label" not in df.columns:
        for alias in ("domain", "job_role", "label"):
            if alias in df.columns:
                df = df.rename(columns={alias: "domain_label"})
                break

    df = df.dropna(subset=["skills_text", "domain_label"])
    df["skills_text"]  = df["skills_text"].astype(str).str.strip()
    df["domain_label"] = df["domain_label"].astype(str).str.strip()
    df = df[df["skills_text"] != ""]
    log.info("Loaded %d rows across %d domains.", len(df), df["domain_label"].nunique())
    return df


# ── Training pipeline ─────────────────────────────────────────────────────────

def train(random_state: int = 42) -> dict:
    """
    Full supervised training pipeline:
      1. Load & validate data
      2. TF-IDF vectorization  (ngram_range=(1,2), sublinear_tf)
      3. RandomForestClassifier with probability=True
      4. Stratified 5-fold cross-validation
      5. Hold-out classification report
      6. Persist artifacts

    Returns the artifact dict (vectorizer, model, labels, feature_names).
    """
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    os.makedirs(LEGACY_MODEL_DIR, exist_ok=True)

    df = load_data()

    X_train, X_test, y_train, y_test = train_test_split(
        df["skills_text"],
        df["domain_label"],
        test_size=0.20,
        random_state=random_state,
        stratify=df["domain_label"],
    )

    # ── Vectorizer ────────────────────────────────────────────────────────────
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_features=8000,
        sublinear_tf=True,       # log(1+tf) dampens very frequent tokens
        strip_accents="unicode",
        analyzer="word",
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec  = vectorizer.transform(X_test)

    # ── Model ─────────────────────────────────────────────────────────────────
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",
        random_state=random_state,
        n_jobs=-1,
        # probability=True is implicit in RandomForest (predict_proba always available)
    )
    model.fit(X_train_vec, y_train)

    # ── Validation ────────────────────────────────────────────────────────────
    log.info("=== Hold-out Classification Report ===")
    y_pred = model.predict(X_test_vec)
    report = classification_report(y_test, y_pred)
    log.info("\n%s", report)

    # 5-fold cross-validation accuracy
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    cv_scores = cross_val_score(model, X_train_vec, y_train, cv=cv, scoring="accuracy", n_jobs=1)
    log.info("5-fold CV accuracy: %.3f ± %.3f", cv_scores.mean(), cv_scores.std())

    # ── Artifacts ─────────────────────────────────────────────────────────────
    feature_names = list(vectorizer.get_feature_names_out())
    artifact = {
        "vectorizer":    vectorizer,
        "model":         model,
        "labels":        list(model.classes_),
        "feature_names": feature_names,
    }
    meta = {
        "labels":        list(model.classes_),
        "feature_names": feature_names,
        "cv_mean":       float(cv_scores.mean()),
        "cv_std":        float(cv_scores.std()),
    }

    try:
        similarity_eval = evaluate_similarity_engine(df)
        meta["similarity_eval"] = similarity_eval
        log.info(
            "Similarity engine eval: accuracy@1=%.4f accuracy@3=%.4f mean_sim_correct=%.4f mean_sim_incorrect=%.4f n=%d",
            similarity_eval["accuracy_at_1"],
            similarity_eval["accuracy_at_3"],
            similarity_eval["mean_sim_correct"],
            similarity_eval["mean_sim_incorrect"],
            similarity_eval["n_samples"],
        )
    except Exception as exc:
        log.warning("Similarity engine evaluation failed: %s", exc)

    try:
        extractor_eval = evaluate_skill_extractor(df)
        meta["extractor_eval"] = extractor_eval
        log.info(
            "Extractor eval: precision=%.4f recall=%.4f f1=%.4f n=%d",
            extractor_eval["mean_precision"],
            extractor_eval["mean_recall"],
            extractor_eval["mean_f1"],
            extractor_eval["n_evaluated"],
        )
    except Exception as exc:
        log.warning("Skill extractor evaluation failed: %s", exc)

    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(model,      MODEL_PATH)
    joblib.dump(meta,       META_PATH)
    log.info("Saved vectorizer  → %s", VECTORIZER_PATH)
    log.info("Saved model       → %s", MODEL_PATH)
    log.info("Saved label meta  → %s", META_PATH)

    # Keep legacy path in sync so inference.py / app.py don't break
    legacy = {"vectorizer": vectorizer, "model": model, "labels": list(model.classes_)}
    joblib.dump(legacy, DOMAIN_MODEL_PATH)
    log.info("Synced legacy model → %s", DOMAIN_MODEL_PATH)

    return artifact


# ── Inference helpers (used by career_intelligence_service.py) ────────────────

def _load_artifacts() -> tuple:
    """Load (vectorizer, model, meta) — train on-demand if missing."""
    if not (os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH)):
        log.info("Artifacts missing — training now ...")
        train()
    vectorizer = joblib.load(VECTORIZER_PATH)
    model      = joblib.load(MODEL_PATH)
    meta       = joblib.load(META_PATH) if os.path.exists(META_PATH) else {}
    return vectorizer, model, meta


def predict_with_xai(
    skills: list[str] | dict[str, int],
    top_k: int = 5,
) -> list[dict]:
    """
    Run the RF pipeline and return top-k domain predictions with XAI.

    Each result:
        {
          "domain":            str,
          "confidence":        float,   # 0-100
          "probability":       float,   # 0-1 raw
          "feature_importance": list[dict],  # [{skill, importance, contribution}]
          "explanation":       list[str],    # human-readable reasons
          "matched_skills":    list[str],
        }
    """
    from ml.preprocessing import build_skill_document, normalize_skill_phrase, normalize_skills
    from config.domain_manifest import DOMAIN_MANIFEST

    vectorizer, model, _ = _load_artifacts()

    # Build skill document (proficiency-weighted if dict)
    if isinstance(skills, dict):
        skill_doc = build_skill_document(skills)
        skill_list = list(skills.keys())
    else:
        skill_doc = " ".join(skills)
        skill_list = list(skills)

    if not skill_doc.strip():
        return []

    features       = vectorizer.transform([skill_doc])
    probs          = model.predict_proba(features)[0]
    feature_names  = np.array(vectorizer.get_feature_names_out())
    importances    = model.feature_importances_
    active_indices = features.nonzero()[1]

    ranked_idx = np.argsort(probs)[::-1][:top_k]
    normalized  = set(normalize_skills(skill_list))
    results: list[dict] = []

    for idx in ranked_idx:
        domain     = model.classes_[idx]
        prob       = float(probs[idx])
        confidence = round(prob * 100, 2)

        # XAI: feature_importances_ × TF-IDF weight for active tokens
        contributions = sorted(
            [
                {
                    "skill":        feature_names[i],
                    "importance":   round(float(importances[i]), 5),
                    "contribution": round(float(importances[i] * features[0, i]), 5),
                }
                for i in active_indices
                if importances[i] > 0
            ],
            key=lambda x: x["contribution"],
            reverse=True,
        )[:8]

        top_skill_names = [c["skill"] for c in contributions[:3]]

        # Human-readable explanation
        required = DOMAIN_MANIFEST.get(domain, {}).get("required_skills", [])
        matched  = [s for s in required if normalize_skill_phrase(s) in normalized]
        explanation = [
            f"{c['skill'].replace('_', ' ').title()} drove {round(c['contribution']*100, 1)}% of the match"
            for c in contributions[:3]
            if c["contribution"] > 0
        ]
        if matched:
            explanation.append(
                f"Matched {len(matched)} domain skill(s): {', '.join(s.upper() for s in matched[:3])}"
            )
        if confidence >= 50:
            explanation.append(
                f"Match based on {confidence:.0f}% probability for {'/'.join(top_skill_names[:2])}"
            )

        results.append({
            "domain":             domain,
            "confidence":         confidence,
            "probability":        round(prob, 4),
            "feature_importance": contributions,
            "explanation":        explanation or ["Skill profile aligned with this domain."],
            "matched_skills":     matched,
        })

    return results


if __name__ == "__main__":
    train()
    try:
        train_difficulty_model()
    except Exception as exc:
        log.warning("Difficulty model evaluation failed: %s", exc)
