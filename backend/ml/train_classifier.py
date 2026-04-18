"""
Task 1: Core ML Pipeline — CSV-based MultiLabel Classifier
===========================================================
Trains a RandomForestClassifier (with XGBoost fallback) on the binary skill
vectors in data/dataset.csv.  Produces two artifacts:
  - models/skill_classifier.pkl   (the fitted pipeline)
  - models/skill_encoder.pkl      (the MultiLabelBinarizer for input encoding)

Run from the backend/ directory:
    python ml/train_classifier.py
"""

from __future__ import annotations

import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer

# Support running as a script from backend/
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

BASE_DIR   = os.path.dirname(os.path.dirname(__file__))
DATA_PATH  = os.path.join(BASE_DIR, "data", "dataset.csv")
MODEL_DIR  = os.path.join(BASE_DIR, "models")
CLASSIFIER_PATH = os.path.join(MODEL_DIR, "skill_classifier.pkl")
ENCODER_PATH    = os.path.join(MODEL_DIR, "skill_encoder.pkl")


def load_dataset() -> tuple[pd.DataFrame, list[str]]:
    """Load the binary skill-vector CSV.  Returns (df, skill_columns)."""
    df = pd.read_csv(DATA_PATH)
    skill_cols = [c for c in df.columns if c != "domain"]
    return df, skill_cols


def build_encoder(skill_cols: list[str]) -> MultiLabelBinarizer:
    """
    Fit a MultiLabelBinarizer over the known skill vocabulary.
    This lets inference encode arbitrary skill lists into the same binary space
    the classifier was trained on.
    """
    mlb = MultiLabelBinarizer(classes=skill_cols)
    # Fit on the full vocabulary so all columns are always present.
    mlb.fit([skill_cols])
    return mlb


def train(random_state: int = 42) -> dict:
    """
    Full training pipeline:
      1. Load CSV
      2. Fit MultiLabelBinarizer on skill vocabulary
      3. Train RandomForestClassifier (XGBoost if available)
      4. Evaluate and persist artifacts
    """
    df, skill_cols = load_dataset()

    X = df[skill_cols].values.astype(float)
    y = df["domain"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )

    # Try XGBoost first; fall back to RandomForest if not installed.
    try:
        from xgboost import XGBClassifier
        from sklearn.preprocessing import LabelEncoder

        le = LabelEncoder()
        y_train_enc = le.fit_transform(y_train)
        y_test_enc  = le.transform(y_test)

        clf = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=random_state,
        )
        clf.fit(X_train, y_train_enc)
        y_pred_enc = clf.predict(X_test)
        y_pred = le.inverse_transform(y_pred_enc)

        # Wrap so predict/predict_proba always return domain strings.
        artifact = {
            "model": clf,
            "label_encoder": le,
            "skill_columns": skill_cols,
            "model_type": "xgboost",
            "feature_importances": dict(zip(skill_cols, clf.feature_importances_)),
        }
        print("=== XGBoost Classifier Evaluation ===")
    except ImportError:
        clf = RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1,
        )
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

        artifact = {
            "model": clf,
            "label_encoder": None,
            "skill_columns": skill_cols,
            "model_type": "random_forest",
            "feature_importances": dict(zip(skill_cols, clf.feature_importances_)),
        }
        print("=== RandomForest Classifier Evaluation ===")

    print(classification_report(y_test, y_pred))

    # Fit and save the MultiLabelBinarizer encoder.
    encoder = build_encoder(skill_cols)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(artifact, CLASSIFIER_PATH)
    joblib.dump(encoder,  ENCODER_PATH)

    print(f"Saved classifier  → {CLASSIFIER_PATH}")
    print(f"Saved encoder     → {ENCODER_PATH}")
    return artifact


def get_prediction_confidence(
    skills: list[str],
    top_k: int = 3,
) -> list[dict]:
    """
    Task 1 — inference entry point.
    Encodes a skill list with the saved MultiLabelBinarizer, runs the classifier,
    and returns the top-k domains with probability scores and the 3 skills that
    contributed most (feature_importances_ × input vector).

    Returns a list of dicts:
        {
          "domain": str,
          "confidence_score": float,          # 0-100
          "matching_keywords": list[str],     # top contributing skills
        }
    """
    if not os.path.exists(CLASSIFIER_PATH) or not os.path.exists(ENCODER_PATH):
        train()

    artifact: dict = joblib.load(CLASSIFIER_PATH)
    encoder: MultiLabelBinarizer = joblib.load(ENCODER_PATH)

    model      = artifact["model"]
    skill_cols = artifact["skill_columns"]
    le         = artifact.get("label_encoder")
    importances: dict[str, float] = artifact.get("feature_importances", {})

    # Encode: transform the skill list into a binary row vector.
    # MultiLabelBinarizer.transform expects an iterable of iterables.
    # Filter to only known classes to suppress UserWarning for unknown skills.
    known_classes = set(encoder.classes_)
    skill_set = {s.strip().lower() for s in skills} & known_classes
    X = encoder.transform([skill_set])          # shape (1, n_features)
    x_row = X[0]                                # 1-D binary array

    # Predict probabilities.
    if le is not None:
        # XGBoost path — classes are integer-encoded.
        probs = model.predict_proba(X)[0]
        classes = le.inverse_transform(np.arange(len(probs)))
    else:
        probs   = model.predict_proba(X)[0]
        classes = model.classes_

    ranked_idx = np.argsort(probs)[::-1][:top_k]

    results = []
    for idx in ranked_idx:
        domain = classes[idx]
        confidence = round(float(probs[idx]) * 100, 2)

        # XAI: multiply feature importance by the input indicator to surface
        # only skills the user actually has that drove this prediction.
        skill_contributions = {
            col: importances.get(col, 0.0) * float(x_row[i])
            for i, col in enumerate(skill_cols)
        }
        top_skills = sorted(
            skill_contributions, key=skill_contributions.get, reverse=True
        )[:3]
        top_skills = [s for s in top_skills if skill_contributions[s] > 0]

        results.append({
            "domain":            domain,
            "confidence_score":  confidence,
            "matching_keywords": top_skills,
        })

    return results


if __name__ == "__main__":
    train()
