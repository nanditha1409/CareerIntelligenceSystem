"""
Stage 1: Data Engine
====================
Generates a high-quality synthetic training dataset of 2,000 samples.

Columns:
  - skills_text     : raw comma-separated skill string (mimics resume text)
  - domain_label    : one of the 15 canonical career domains
  - difficulty_level: Easy / Medium / Hard (based on skill depth)

Design principles:
  - Domain-specific skill clusters ensure "Keras, CNN, OpenCV" → "AI/ML Engineer"
  - Synonym injection (e.g. "PyTorch" → "torch", "deep learning") adds realism
  - Controlled cross-domain noise prevents overfitting
  - Difficulty is derived from skill seniority, not random

Run from backend/:
    python ml/data_generator.py
"""

from __future__ import annotations

import os
import random
import sys

import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

BASE_DIR   = os.path.dirname(os.path.dirname(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")
OUTPUT_CSV = os.path.join(DATA_DIR, "training_data.csv")

# ── Domain skill taxonomy ─────────────────────────────────────────────────────
# Each domain has: core (always present), secondary (often present), advanced (senior signals)

DOMAIN_TAXONOMY: dict[str, dict[str, list[str]]] = {
    "AI/ML Engineer": {
        "core":     ["python", "machine learning", "scikit-learn", "numpy", "pandas"],
        "secondary":["tensorflow", "keras", "pytorch", "deep learning", "neural networks",
                     "CNN", "RNN", "LSTM", "OpenCV", "NLP", "transformers", "huggingface",
                     "computer vision", "feature engineering", "model evaluation"],
        "advanced": ["LLM", "RLHF", "diffusion models", "MLOps", "kubeflow", "triton",
                     "CUDA", "distributed training", "model quantization", "ONNX"],
        "synonyms": {"pytorch": ["torch", "PyTorch"], "tensorflow": ["TF", "TensorFlow"],
                     "NLP": ["natural language processing", "text mining"],
                     "CNN": ["convolutional neural network", "image classification"]},
    },
    "Data Scientist": {
        "core":     ["python", "statistics", "pandas", "numpy", "SQL"],
        "secondary":["scikit-learn", "matplotlib", "seaborn", "hypothesis testing",
                     "A/B testing", "regression", "classification", "clustering",
                     "feature selection", "data wrangling", "Jupyter"],
        "advanced": ["Spark", "Hadoop", "Airflow", "dbt", "causal inference",
                     "Bayesian statistics", "time series", "forecasting", "R"],
        "synonyms": {"SQL": ["MySQL", "PostgreSQL", "database queries"],
                     "Spark": ["PySpark", "Apache Spark"]},
    },
    "Data Analyst": {
        "core":     ["SQL", "Excel", "data visualization", "reporting"],
        "secondary":["Power BI", "Tableau", "Google Sheets", "pivot tables",
                     "dashboard design", "KPI tracking", "business intelligence",
                     "data cleaning", "ETL", "Python"],
        "advanced": ["Looker", "Metabase", "dbt", "Snowflake", "BigQuery",
                     "advanced SQL", "window functions", "data modeling"],
        "synonyms": {"Power BI": ["PowerBI", "Microsoft Power BI"],
                     "Tableau": ["Tableau Desktop", "Tableau Server"]},
    },
    "Full Stack Developer": {
        "core":     ["JavaScript", "HTML", "CSS", "React", "Node.js"],
        "secondary":["TypeScript", "Express", "MongoDB", "REST API", "Git",
                     "Redux", "Next.js", "GraphQL", "PostgreSQL", "Docker"],
        "advanced": ["microservices", "WebSockets", "OAuth", "JWT", "CI/CD",
                     "Kubernetes", "AWS", "performance optimization", "SSR"],
        "synonyms": {"Node.js": ["Node", "NodeJS"], "React": ["ReactJS", "React.js"],
                     "MongoDB": ["Mongo", "NoSQL"]},
    },
    "Backend Developer": {
        "core":     ["Python", "REST API", "SQL", "Git", "server-side development"],
        "secondary":["FastAPI", "Django", "Flask", "PostgreSQL", "Redis",
                     "Docker", "authentication", "JWT", "MongoDB", "Node.js"],
        "advanced": ["microservices", "message queues", "RabbitMQ", "Kafka",
                     "gRPC", "database optimization", "caching strategies", "Go"],
        "synonyms": {"FastAPI": ["fast api", "Python API"], "Django": ["Django REST framework"]},
    },
    "Software Engineer": {
        "core":     ["data structures", "algorithms", "OOP", "Git", "problem solving"],
        "secondary":["Python", "Java", "C++", "system design", "design patterns",
                     "unit testing", "code review", "debugging", "Linux", "SQL"],
        "advanced": ["distributed systems", "concurrency", "memory management",
                     "compiler design", "Rust", "Go", "performance profiling"],
        "synonyms": {"OOP": ["object-oriented programming", "object oriented"],
                     "DSA": ["data structures and algorithms"]},
    },
    "DevOps Engineer": {
        "core":     ["Docker", "Linux", "CI/CD", "Git", "automation"],
        "secondary":["Kubernetes", "Jenkins", "Ansible", "Terraform", "AWS",
                     "monitoring", "Prometheus", "Grafana", "Bash scripting", "Python"],
        "advanced": ["GitOps", "ArgoCD", "Helm", "service mesh", "Istio",
                     "chaos engineering", "SRE practices", "FinOps"],
        "synonyms": {"CI/CD": ["continuous integration", "continuous deployment", "pipeline"],
                     "Kubernetes": ["K8s", "container orchestration"]},
    },
    "Cybersecurity Analyst": {
        "core":     ["network security", "Linux", "firewalls", "threat detection"],
        "secondary":["penetration testing", "SIEM", "vulnerability assessment",
                     "incident response", "Wireshark", "Nmap", "Python",
                     "cryptography", "SOC", "compliance", "OWASP"],
        "advanced": ["red teaming", "malware analysis", "forensics", "zero trust",
                     "CVE research", "exploit development", "threat intelligence"],
        "synonyms": {"SIEM": ["security information and event management"],
                     "penetration testing": ["pen testing", "ethical hacking"]},
    },
    "UI/UX Designer": {
        "core":     ["Figma", "wireframing", "prototyping", "user research"],
        "secondary":["design systems", "usability testing", "Adobe XD", "Sketch",
                     "interaction design", "accessibility", "HTML", "CSS",
                     "information architecture", "user flows"],
        "advanced": ["motion design", "design tokens", "component libraries",
                     "A/B testing", "eye tracking", "service design", "Framer"],
        "synonyms": {"Figma": ["Figma design", "UI design tool"],
                     "wireframing": ["wireframes", "low-fidelity design"]},
    },
}

NOISE_POOL = ["communication", "teamwork", "agile", "scrum", "Jira", "Confluence",
              "documentation", "presentation", "time management", "leadership"]

DIFFICULTY_ADVANCED_SKILLS = {
    skill
    for taxonomy in DOMAIN_TAXONOMY.values()
    for skill in taxonomy["advanced"]
}


def _infer_difficulty(skills: list[str]) -> str:
    """Derive difficulty from how many advanced/senior skills appear."""
    advanced_count = sum(1 for s in skills if s in DIFFICULTY_ADVANCED_SKILLS)
    if advanced_count >= 3:
        return "Hard"
    if advanced_count >= 1:
        return "Medium"
    return "Easy"


def _expand_synonyms(skill: str, taxonomy: dict) -> list[str]:
    """Return the skill plus any configured synonyms."""
    synonyms = taxonomy.get("synonyms", {})
    return [skill] + synonyms.get(skill, [])


def generate(n: int = 2000, random_state: int = 42) -> pd.DataFrame:
    """
    Generate n high-quality labeled samples.
    Distribution is balanced: ~222 samples per domain (9 domains).
    """
    rng = random.Random(random_state)
    rows: list[dict] = []
    domains = list(DOMAIN_TAXONOMY.keys())
    per_domain = n // len(domains)
    remainder  = n % len(domains)

    for i, domain in enumerate(domains):
        count    = per_domain + (1 if i < remainder else 0)
        taxonomy = DOMAIN_TAXONOMY[domain]
        core     = taxonomy["core"]
        secondary = taxonomy["secondary"]
        advanced  = taxonomy["advanced"]

        for _ in range(count):
            selected: list[str] = []

            # Always include 2-4 core skills
            selected += rng.sample(core, min(rng.randint(2, 4), len(core)))

            # 3-6 secondary skills
            selected += rng.sample(secondary, min(rng.randint(3, 6), len(secondary)))

            # 0-3 advanced skills (drives difficulty label)
            adv_count = rng.choices([0, 1, 2, 3], weights=[0.35, 0.35, 0.20, 0.10])[0]
            if adv_count:
                selected += rng.sample(advanced, min(adv_count, len(advanced)))

            # Synonym expansion for 30% of skills (adds realism)
            expanded: list[str] = []
            for skill in selected:
                if rng.random() < 0.30:
                    expanded += _expand_synonyms(skill, taxonomy)
                else:
                    expanded.append(skill)

            # 0-2 noise skills
            noise_count = rng.randint(0, 2)
            expanded += rng.sample(NOISE_POOL, noise_count)

            rng.shuffle(expanded)
            skills_text = ", ".join(dict.fromkeys(expanded))  # deduplicate, preserve order

            rows.append({
                "skills_text":      skills_text,
                "domain_label":     domain,
                "difficulty_level": _infer_difficulty(selected),
            })

    rng.shuffle(rows)
    return pd.DataFrame(rows)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print("Generating 2,000-sample training dataset ...")
    df = generate(2000)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved {len(df)} rows → {OUTPUT_CSV}")
    print(f"Domain distribution:\n{df['domain_label'].value_counts().to_string()}")
    print(f"Difficulty distribution:\n{df['difficulty_level'].value_counts().to_string()}")


if __name__ == "__main__":
    main()
