"""
Train and persist ML artifacts for the career intelligence system.

Run manually:
    python ml/train_model.py
"""

from __future__ import annotations

import os
import sys

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

if __package__ in (None, ""):
    # Addition: support `python ml/train_model.py` from the backend directory.
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ml.preprocessing import build_difficulty_training_frame, build_domain_training_frame


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
DOMAIN_MODEL_PATH = os.path.join(MODEL_DIR, "ml_domain_recommender.joblib")
DIFFICULTY_MODEL_PATH = os.path.join(MODEL_DIR, "ml_difficulty_model.joblib")


def train_domain_model() -> dict:
    """Train the main TF-IDF + multinomial logistic regression recommendation model."""
    frame = build_domain_training_frame()
    X_train, X_test, y_train, y_test = train_test_split(
        frame["text"],
        frame["domain"],
        test_size=0.2,
        random_state=42,
        stratify=frame["domain"],
    )

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(max_iter=3000, multi_class="multinomial")
    model.fit(X_train_vec, y_train)

    print("=== ML Domain Model Evaluation ===")
    print(classification_report(y_test, model.predict(X_test_vec)))

    artifact = {"vectorizer": vectorizer, "model": model, "labels": list(model.classes_)}
    joblib.dump(artifact, DOMAIN_MODEL_PATH)
    return artifact


def train_difficulty_model() -> dict:
    """Train the adaptive difficulty selector from performance aggregates."""
    frame = build_difficulty_training_frame()
    X = frame[["recent_score", "avg_score", "weak_topic_rate", "attempts"]]
    y = frame["next_difficulty"]

    model = RandomForestClassifier(n_estimators=160, random_state=42)
    model.fit(X, y)

    artifact = {"model": model, "feature_names": list(X.columns)}
    joblib.dump(artifact, DIFFICULTY_MODEL_PATH)
    return artifact


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    train_domain_model()
    train_difficulty_model()
    print(f"Saved ML domain model to {DOMAIN_MODEL_PATH}")
    print(f"Saved ML difficulty model to {DIFFICULTY_MODEL_PATH}")


if __name__ == "__main__":
    main()
