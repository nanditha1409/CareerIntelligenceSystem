"""
Task 1: Data Acquisition
========================
Downloads the IT Job Roles & Skills dataset from GitHub.
Falls back to generating a synthetic 1,000-row CSV if the download fails.

Run from the backend/ directory:
    python scripts/setup_data.py
"""

from __future__ import annotations

import os
import sys
import random
import csv

# Support running as a script from backend/
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

BASE_DIR   = os.path.dirname(os.path.dirname(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")
OUTPUT_CSV = os.path.join(DATA_DIR, "training_data.csv")

SOURCE_URL = (
    "https://raw.githubusercontent.com/datasets/job-descriptions/master/data/job-descriptions.csv"
)

# 15 canonical domains with representative skill sets
DOMAIN_SKILLS: dict[str, list[str]] = {
    "AI/ML Engineer":           ["python", "tensorflow", "pytorch", "nlp", "ml", "deep learning", "scikit-learn", "keras", "numpy", "pandas", "docker", "aws", "git", "kubernetes", "computer vision"],
    "Data Scientist":           ["python", "ml", "sql", "statistics", "pandas", "numpy", "tableau", "spark", "r", "tensorflow", "git", "excel", "feature engineering", "pytorch", "experimentation"],
    "Data Analyst":             ["sql", "excel", "powerbi", "tableau", "python", "reporting", "dashboarding", "business intelligence", "spark", "git", "analytics", "data visualization", "mysql", "postgresql", "etl"],
    "Full Stack Developer":     ["html", "css", "javascript", "react", "node", "typescript", "mongodb", "graphql", "git", "docker", "rest api", "redux", "express", "postgresql", "aws"],
    "Backend Developer":        ["python", "node", "sql", "fastapi", "django", "docker", "redis", "mongodb", "git", "rest api", "microservices", "postgresql", "java", "go", "rabbitmq"],
    "Software Engineer":        ["python", "java", "dsa", "git", "algorithms", "oop", "c++", "rust", "go", "system design", "linux", "data structures", "design patterns", "testing", "ci/cd"],
    "DevOps Engineer":          ["docker", "linux", "aws", "kubernetes", "git", "ci/cd", "terraform", "ansible", "jenkins", "python", "monitoring", "bash", "helm", "prometheus", "grafana"],
    "Cloud Engineer":           ["aws", "docker", "kubernetes", "linux", "python", "git", "azure", "gcp", "terraform", "networking", "iam", "s3", "ec2", "cloudformation", "load balancing"],
    "Cybersecurity Analyst":    ["networking", "security", "linux", "python", "git", "penetration testing", "siem", "firewalls", "cryptography", "incident response", "soc", "vulnerability assessment", "wireshark", "nmap", "compliance"],
    "Blockchain Developer":     ["solidity", "rust", "go", "javascript", "git", "web3", "smart contracts", "ethereum", "defi", "cryptography", "hardhat", "truffle", "ipfs", "nft", "consensus algorithms"],
    "Embedded Systems Engineer":["c", "c++", "python", "linux", "networking", "git", "rtos", "microcontroller", "firmware", "uart", "spi", "i2c", "arm", "fpga", "debugging"],
    "Mobile App Developer":     ["javascript", "typescript", "react", "java", "git", "graphql", "flutter", "dart", "swift", "kotlin", "android", "ios", "react native", "firebase", "rest api"],
    "QA Automation Engineer":   ["python", "java", "javascript", "git", "docker", "sql", "selenium", "cypress", "pytest", "junit", "test automation", "ci/cd", "postman", "jira", "bdd"],
    "Site Reliability Engineer":["linux", "python", "go", "docker", "kubernetes", "aws", "git", "networking", "monitoring", "prometheus", "grafana", "incident response", "slo", "chaos engineering", "observability"],
    "Product Manager":          ["excel", "sql", "figma", "analytics", "communication", "roadmapping", "jira", "user stories", "a/b testing", "stakeholder management", "agile", "scrum", "product strategy", "market research", "okr"],
    "UI/UX Designer":           ["figma", "html", "css", "javascript", "react", "typescript", "wireframes", "prototyping", "user research", "design systems", "accessibility", "sketch", "adobe xd", "usability testing", "interaction design"],
}

NOISE_SKILLS = ["communication", "teamwork", "agile", "scrum", "jira", "confluence", "slack", "presentation", "documentation", "time management"]


def _try_download() -> list[dict] | None:
    """Attempt to download the source CSV. Returns parsed rows or None on failure."""
    try:
        import requests
        print(f"Downloading dataset from {SOURCE_URL} ...")
        resp = requests.get(SOURCE_URL, timeout=15)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        reader = csv.DictReader(lines)
        rows = list(reader)
        if rows and len(rows) > 10:
            print(f"  Downloaded {len(rows)} rows.")
            return rows
    except Exception as exc:
        print(f"  Download failed: {exc}")
    return None


def _map_downloaded_rows(rows: list[dict]) -> list[dict]:
    """
    Map downloaded job-description rows to our schema.
    Columns expected: title, description (or similar).
    We extract skills by keyword matching against our domain skill lists.
    """
    all_domain_skills = {skill for skills in DOMAIN_SKILLS.values() for skill in skills}
    mapped: list[dict] = []

    for row in rows:
        text = " ".join(str(v) for v in row.values()).lower()
        matched_skills = [s for s in all_domain_skills if s in text]

        # Assign domain by highest skill overlap
        best_domain, best_count = "Software Engineer", 0
        for domain, skills in DOMAIN_SKILLS.items():
            count = sum(1 for s in skills if s in text)
            if count > best_count:
                best_count, best_domain = count, domain

        if matched_skills:
            mapped.append({
                "skills": ", ".join(matched_skills[:12]),
                "job_role": best_domain,
            })

    return mapped


def _generate_synthetic(n: int = 1000, random_state: int = 42) -> list[dict]:
    """Generate n synthetic rows mapping skills to domains."""
    rng = random.Random(random_state)
    rows: list[dict] = []
    domains = list(DOMAIN_SKILLS.keys())

    per_domain = n // len(domains)
    remainder  = n % len(domains)

    for i, domain in enumerate(domains):
        count = per_domain + (1 if i < remainder else 0)
        core_skills = DOMAIN_SKILLS[domain]

        for _ in range(count):
            # Pick 4-8 core skills + 0-2 noise skills
            num_core  = rng.randint(4, min(8, len(core_skills)))
            num_noise = rng.randint(0, 2)
            selected  = rng.sample(core_skills, num_core)
            selected += rng.sample(NOISE_SKILLS, min(num_noise, len(NOISE_SKILLS)))
            rng.shuffle(selected)
            rows.append({"skills": ", ".join(selected), "job_role": domain})

    rng.shuffle(rows)
    return rows


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # Data precedence: use existing file if present
    if os.path.exists(OUTPUT_CSV):
        print(f"training_data.csv already exists at {OUTPUT_CSV} — skipping.")
        return

    rows = _try_download()
    if rows:
        mapped = _map_downloaded_rows(rows)
        if len(mapped) >= 100:
            print(f"  Mapped {len(mapped)} rows from downloaded data.")
            # Pad with synthetic if too few
            if len(mapped) < 1000:
                synthetic = _generate_synthetic(1000 - len(mapped))
                mapped.extend(synthetic)
                print(f"  Padded with {len(synthetic)} synthetic rows → total {len(mapped)}.")
            rows_to_write = mapped
        else:
            print("  Too few mappable rows from download — using synthetic generator.")
            rows_to_write = _generate_synthetic(1000)
    else:
        print("Generating 1,000-row synthetic dataset ...")
        rows_to_write = _generate_synthetic(1000)

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["skills", "job_role"])
        writer.writeheader()
        writer.writerows(rows_to_write)

    print(f"Saved {len(rows_to_write)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
