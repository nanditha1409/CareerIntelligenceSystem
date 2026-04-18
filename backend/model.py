"""
Train and persist the career recommendation model (RandomForest + hyperparameter search).
Run from backend/:  python generate_dataset.py && python model.py
"""
import os
import logging

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import RandomizedSearchCV, cross_val_score, train_test_split

from utils import SKILLS_LIST

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data", "dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "career_model.pkl")


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    if list(df.columns[:-1]) != SKILLS_LIST:
        raise ValueError(
            "Dataset columns do not match utils.SKILLS_LIST. Regenerate with: python generate_dataset.py"
        )

    X = df[SKILLS_LIST]
    y = df["domain"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    base = RandomForestClassifier(random_state=42, class_weight="balanced")

    param_distributions = {
        "n_estimators": [200, 400, 600, 800],
        "max_depth": [None, 16, 24, 32, 40],
        "min_samples_split": [2, 4, 8, 12],
        "min_samples_leaf": [1, 2, 4],
    }

    search = RandomizedSearchCV(
        base,
        param_distributions=param_distributions,
        n_iter=24,
        cv=5,
        scoring="accuracy",
        random_state=42,
        n_jobs=-1,
        verbose=1,
    )
    search.fit(X_train, y_train)
    best = search.best_estimator_

    logger.info("Best params: %s", search.best_params_)
    logger.info("Best CV score (train subset): %.4f", search.best_score_)

    cv_mean = cross_val_score(best, X, y, cv=5, scoring="accuracy").mean()
    logger.info("5-fold CV mean accuracy (full data, same estimator): %.4f", cv_mean)

    y_pred = best.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logger.info("Hold-out test accuracy: %.4f", acc)
    logger.info("Confusion matrix (rows=true, cols=pred):\n%s", confusion_matrix(y_test, y_pred))
    logger.info("Classification report:\n%s", classification_report(y_test, y_pred))

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    if os.path.isfile(MODEL_PATH):
        os.remove(MODEL_PATH)
    joblib.dump(best, MODEL_PATH)
    logger.info("Model saved to %s (features=%s)", MODEL_PATH, len(SKILLS_LIST))


if __name__ == "__main__":
    main()
