import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# Load dataset
df = pd.read_csv("data/dataset.csv")

# DEBUG: print columns
print("Columns in dataset:", df.columns.tolist())

# Separate features and target
X = df.drop("domain", axis=1)
y = df["domain"]

print("Number of features used:", X.shape[1])

# Train model
model = RandomForestClassifier()
model.fit(X, y)

# Save model
import os

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "models", "career_model.pkl")

joblib.dump(model, MODEL_PATH)

print("Model trained and saved successfully!")