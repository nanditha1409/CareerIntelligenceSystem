"""
Train and persist the career recommendation model.
Run: python model.py
"""
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data", "dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "career_model.pkl")

df = pd.read_csv(DATA_PATH)

X = df.drop("domain", axis=1)
y = df["domain"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.1,
    random_state=42,
)
model.fit(X_train, y_train)

print("=== Model Evaluation ===")
print(classification_report(y_test, model.predict(X_test)))

os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
joblib.dump(model, MODEL_PATH)
print(f"Model saved to {MODEL_PATH}")
print(f"Feature count: {len(X.columns)}")
