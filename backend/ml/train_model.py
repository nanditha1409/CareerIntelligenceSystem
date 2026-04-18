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

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
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
    """
    Full training pipeline:
      1. Load CSV
      2. TF-IDF vectorize the 'skills' column
      3. Train RandomForestClassifier
      4. Evaluate and persist artifacts
    Returns the artifact dict.
    """
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    os.makedirs(LEGACY_MODEL_DIR, exist_ok=True)

    df = load_training_data()
    print(f"Loaded {len(df)} training rows across {df['job_role'].nunique()} domains.")

    X_train, X_test, y_train, y_test = train_test_split(
        df["skills"],
        df["job_role"],
        test_size=0.2,
        random_state=random_state,
        stratify=df["job_role"],
    )

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_features=5000,
        sublinear_tf=True,
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec  = vectorizer.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)
    print("=== ML Pipeline Evaluation ===")
    print(classification_report(y_test, y_pred))

    artifact = {
        "vectorizer": vectorizer,
        "model":      model,
        "labels":     list(model.classes_),
        "feature_names": list(vectorizer.get_feature_names_out()),
    }

    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(model,      MODEL_PATH)
    print(f"Saved vectorizer → {VECTORIZER_PATH}")
    print(f"Saved model      → {MODEL_PATH}")

    # Also persist as the legacy domain recommender so existing inference.py keeps working
    legacy_artifact = {"vectorizer": vectorizer, "model": model, "labels": list(model.classes_)}
    joblib.dump(legacy_artifact, DOMAIN_MODEL_PATH)
    print(f"Saved legacy domain model → {DOMAIN_MODEL_PATH}")

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
    clf = RFC(n_estimators=160, random_state=42)
    clf.fit(X, y)
    artifact = {"model": clf, "feature_names": list(X.columns)}
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
