"""
Task 2: ML Pipeline — TF-IDF + RandomForestClassifier
======================================================
Loads training_data.csv (or generates it via setup_data.py),
trains a TfidfVectorizer + RandomForestClassifier pipeline,
and exports artifacts to backend/ml/artifacts/.

Artifacts produced:
  - ml/artifacts/model.joblib       (fitted RandomForestClassifier)
  - ml/artifacts/vectorizer.joblib  (fitted TfidfVectorizer)

Run from the backend/ directory:
    python ml/train_model.py
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
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# Support running as a script from backend/
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

BASE_DIR        = os.path.dirname(os.path.dirname(__file__))
DATA_DIR        = os.path.join(BASE_DIR, "data")
TRAINING_CSV    = os.path.join(DATA_DIR, "training_data.csv")
ARTIFACTS_DIR   = os.path.join(BASE_DIR, "ml", "artifacts")
MODEL_PATH      = os.path.join(ARTIFACTS_DIR, "model.joblib")
VECTORIZER_PATH = os.path.join(ARTIFACTS_DIR, "vectorizer.joblib")

# Legacy paths (kept for backward compatibility with existing inference.py)
LEGACY_MODEL_DIR        = os.path.join(BASE_DIR, "models")
DOMAIN_MODEL_PATH       = os.path.join(LEGACY_MODEL_DIR, "ml_domain_recommender.joblib")
DIFFICULTY_MODEL_PATH   = os.path.join(LEGACY_MODEL_DIR, "ml_difficulty_model.joblib")

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def _ensure_training_data() -> None:
    """Run setup_data.py if training_data.csv is missing."""
    if not os.path.exists(TRAINING_CSV):
        print("training_data.csv not found — running setup_data.py ...")
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "setup_data",
            os.path.join(BASE_DIR, "scripts", "setup_data.py"),
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.main()


def load_training_data() -> pd.DataFrame:
    """Load the CSV. Falls back to dataset.csv if training_data.csv is absent."""
    _ensure_training_data()

    if os.path.exists(TRAINING_CSV):
        df = pd.read_csv(TRAINING_CSV)
    else:
        # Last-resort fallback: use the existing binary-vector dataset
        fallback = os.path.join(DATA_DIR, "dataset.csv")
        if not os.path.exists(fallback):
            raise FileNotFoundError(f"No training data found at {TRAINING_CSV} or {fallback}")
        df = pd.read_csv(fallback)
        # Reshape binary-vector CSV into skills/job_role format
        skill_cols = [c for c in df.columns if c != "domain"]
        rows = []
        for _, row in df.iterrows():
            active = [col for col in skill_cols if row[col] == 1]
            rows.append({"skills": ", ".join(active), "job_role": row["domain"]})
        df = pd.DataFrame(rows)

    # Normalise column names
    df.columns = [c.strip().lower() for c in df.columns]
    if "job_role" not in df.columns and "domain" in df.columns:
        df = df.rename(columns={"domain": "job_role"})

    df = df.dropna(subset=["skills", "job_role"])
    df["skills"]   = df["skills"].astype(str).str.strip()
    df["job_role"] = df["job_role"].astype(str).str.strip()
    df = df[df["skills"] != ""]
    return df


def train(random_state: int = 42) -> dict:
    """Delegates to ml/trainer.py which is the canonical training pipeline."""
    from ml.trainer import train as canonical_train
    artifact = canonical_train(random_state=random_state)
    # Also save to legacy paths so inference.py keeps working
    os.makedirs(LEGACY_MODEL_DIR, exist_ok=True)
    legacy = {"vectorizer": artifact["vectorizer"], "model": artifact["model"], "labels": artifact["labels"]}
    joblib.dump(legacy, DOMAIN_MODEL_PATH)
    return artifact


# ── Difficulty model (kept for backward compatibility) ────────────────────────

def _build_difficulty_frame() -> pd.DataFrame:
    """Minimal synthetic difficulty training frame."""
    import random as _rng
    rows = []
    for _ in range(800):
        recent = _rng.uniform(0, 100)
        avg    = _rng.uniform(0, 100)
        weak   = _rng.uniform(0, 1)
        att    = _rng.randint(1, 30)
        if recent >= 80 and weak < 0.25:
            label = "Hard"
        elif recent < 50 or weak > 0.5:
            label = "Easy"
        else:
            label = "Medium"
        rows.append({"recent_score": recent, "avg_score": avg, "weak_topic_rate": weak, "attempts": att, "next_difficulty": label})
    return pd.DataFrame(rows)


def train_difficulty_model() -> dict:
    from sklearn.ensemble import RandomForestClassifier as RFC
    frame = _build_difficulty_frame()
    X = frame[["recent_score", "avg_score", "weak_topic_rate", "attempts"]]
    y = frame["next_difficulty"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    clf = RFC(n_estimators=160, random_state=42)
    clf.fit(X_train, y_train)

    report = ""
    matrix_list: list[list[int]] = []
    feature_importances = {}
    try:
        y_pred = clf.predict(X_test)
        report = classification_report(y_test, y_pred)
        matrix = confusion_matrix(y_test, y_pred, labels=list(clf.classes_))
        matrix_list = matrix.tolist()
        feature_importances = {
            feature_name: round(float(importance), 6)
            for feature_name, importance in zip(X.columns, clf.feature_importances_)
        }

        log.info("=== Difficulty Model Hold-out Classification Report ===")
        log.info("\n%s", report)
        log.info("=== Difficulty Model Confusion Matrix ===")
        log.info("%s", matrix_list)
    except Exception as exc:
        log.warning("Difficulty model evaluation metrics failed: %s", exc)

    artifact = {
        "model": clf,
        "feature_names": list(X.columns),
        "eval_report": report,
        "confusion_matrix": matrix_list,
        "feature_importances": feature_importances,
    }
    os.makedirs(LEGACY_MODEL_DIR, exist_ok=True)
    joblib.dump(artifact, DIFFICULTY_MODEL_PATH)
    return artifact


def train_domain_model() -> dict:
    """Alias used by existing inference.py — delegates to train()."""
    return train()


def main():
    train()
    # Ensure difficulty model exists too
    if not os.path.exists(DIFFICULTY_MODEL_PATH):
        train_difficulty_model()
        print(f"Saved difficulty model → {DIFFICULTY_MODEL_PATH}")


if __name__ == "__main__":
    main()
