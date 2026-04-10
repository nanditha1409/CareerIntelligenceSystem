import random
import pandas as pd

skills = [
    "python","sql","ml","html","css","js","docker","linux",
    "figma","react","node","java","dsa","aws","excel","powerbi",
    "tensorflow","networking","security"
]

domains = {
    "Data Scientist": ["python","ml","sql","tensorflow"],
    "AI-ML Engineer": ["python","ml","tensorflow"],
    "Data Analyst": ["sql","excel","powerbi","python"],
    "Full Stack Developer": ["html","css","js","react","node"],
    "Software Engineer": ["python","java","dsa"],
    "DevOps Engineer": ["docker","linux","aws"],
    "Cybersecurity Analyst": ["networking","security","linux"],
    "UI/UX Designer": ["figma"],
    "Backend Developer": ["python","node","sql"]
}

data = []

for domain, core_skills in domains.items():
    for _ in range(30):  # 30 samples per domain

        row = {skill: 0 for skill in skills}

        # Add core skills (80% chance)
        for skill in core_skills:
            if random.random() > 0.2:
                row[skill] = 1

        # Add random noise (10%)
        for skill in skills:
            if random.random() < 0.1:
                row[skill] = 1

        row["domain"] = domain
        data.append(row)

df = pd.DataFrame(data)
df.to_csv("data/dataset.csv", index=False)

print("🔥 Dataset generated with", len(df), "rows")