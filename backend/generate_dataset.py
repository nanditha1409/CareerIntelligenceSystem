"""
Generates a synthetic training dataset with binary skill features (aligned with utils.SKILLS_LIST).
Run: python generate_dataset.py
"""
import random
import pandas as pd
import os

from utils import SKILLS_LIST as SKILLS

# ── Domain → core skills (high probability) + secondary (medium probability) ─
DOMAIN_PROFILES = {
    "Data Scientist":        {"core": ["python", "ml", "sql", "tensorflow", "pytorch", "spark"],
                              "secondary": ["git", "tableau", "excel", "c", "cpp"]},
    "AI-ML Engineer":        {"core": ["python", "ml", "tensorflow", "pytorch", "fastapi"],
                              "secondary": ["docker", "git", "aws", "kubernetes", "c", "cpp"]},
    "Data Analyst":          {"core": ["sql", "excel", "powerbi", "tableau", "python"],
                              "secondary": ["git", "spark", "ruby"]},
    "Full Stack Developer":  {"core": ["html", "css", "js", "react", "node", "typescript"],
                              "secondary": ["mongodb", "graphql", "git", "docker", "ruby"]},
    "Software Engineer":     {"core": ["python", "java", "c", "cpp", "dsa", "git"],
                              "secondary": ["html", "css", "js", "rust", "go", "ruby"]},
    "DevOps Engineer":       {"core": ["docker", "linux", "aws", "kubernetes", "git"],
                              "secondary": ["python", "redis", "go", "c"]},
    "Cybersecurity Analyst": {"core": ["networking", "security", "linux"],
                              "secondary": ["python", "git", "c", "cpp"]},
    "UI/UX Designer":        {"core": ["figma", "html", "css"],
                              "secondary": ["js", "react", "typescript", "ruby"]},
    "Backend Developer":     {"core": ["python", "node", "sql", "fastapi", "django"],
                              "secondary": ["docker", "redis", "mongodb", "git", "ruby", "cpp"]},
}

SAMPLES_PER_DOMAIN = 60   # 60 × 9 = 540 rows — enough for a solid RF model

random.seed(42)
data = []

for domain, profile in DOMAIN_PROFILES.items():
    core = profile["core"]
    secondary = profile["secondary"]

    for _ in range(SAMPLES_PER_DOMAIN):
        row = {skill: 0 for skill in SKILLS}

        # Core skills: 85 % chance present
        for skill in core:
            if random.random() < 0.85:
                row[skill] = 1

        # Secondary skills: 45 % chance present
        for skill in secondary:
            if random.random() < 0.45:
                row[skill] = 1

        # Random noise: 8 % chance on any remaining skill
        for skill in SKILLS:
            if row[skill] == 0 and random.random() < 0.08:
                row[skill] = 1

        row["domain"] = domain
        data.append(row)

df = pd.DataFrame(data)
df = df[SKILLS + ["domain"]]

OUT_PATH = os.path.join(os.path.dirname(__file__), "data", "dataset.csv")
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
df.to_csv(OUT_PATH, index=False)

print(f"Dataset generated: {len(df)} rows × {len(SKILLS)} skill features")
print(f"Saved to: {OUT_PATH}")
print(f"Domain distribution:\n{df['domain'].value_counts()}")
