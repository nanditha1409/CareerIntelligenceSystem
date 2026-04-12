"""
Generates a synthetic training dataset with 30+ binary skill features.
Run: python generate_dataset.py
"""
import random
import pandas as pd
import os

# ── 30 canonical skills ──────────────────────────────────────────────────────
SKILLS = [
    "python", "sql", "ml", "html", "css", "js",
    "docker", "linux", "figma", "react", "node",
    "java", "dsa", "aws", "excel", "powerbi",
    "tensorflow", "networking", "security",
    "git", "typescript", "mongodb", "redis",
    "kubernetes", "graphql", "rust", "go",
    "spark", "tableau", "pytorch",
    "fastapi", "django",
]

# ── Domain → core skills (high probability) + secondary (medium probability) ─
DOMAIN_PROFILES = {
    "Data Scientist":        {"core": ["python", "ml", "sql", "tensorflow", "pytorch", "spark"],
                              "secondary": ["git", "tableau", "excel"]},
    "AI-ML Engineer":        {"core": ["python", "ml", "tensorflow", "pytorch", "fastapi"],
                              "secondary": ["docker", "git", "aws", "kubernetes"]},
    "Data Analyst":          {"core": ["sql", "excel", "powerbi", "tableau", "python"],
                              "secondary": ["git", "spark"]},
    "Full Stack Developer":  {"core": ["html", "css", "js", "react", "node", "typescript"],
                              "secondary": ["mongodb", "graphql", "git", "docker"]},
    "Software Engineer":     {"core": ["python", "java", "dsa", "git"],
                              "secondary": ["html", "css", "js", "rust", "go"]},
    "DevOps Engineer":       {"core": ["docker", "linux", "aws", "kubernetes", "git"],
                              "secondary": ["python", "redis", "go"]},
    "Cybersecurity Analyst": {"core": ["networking", "security", "linux"],
                              "secondary": ["python", "git"]},
    "UI/UX Designer":        {"core": ["figma", "html", "css"],
                              "secondary": ["js", "react", "typescript"]},
    "Backend Developer":     {"core": ["python", "node", "sql", "fastapi", "django"],
                              "secondary": ["docker", "redis", "mongodb", "git"]},
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

OUT_PATH = os.path.join(os.path.dirname(__file__), "data", "dataset.csv")
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
df.to_csv(OUT_PATH, index=False)

print(f"Dataset generated: {len(df)} rows × {len(SKILLS)} skill features")
print(f"Saved to: {OUT_PATH}")
print(f"Domain distribution:\n{df['domain'].value_counts()}")
