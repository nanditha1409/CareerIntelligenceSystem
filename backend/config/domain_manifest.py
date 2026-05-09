"""
Single source of truth for supported career domains, keyword routing,
and company-specific interviewing archetypes.
"""

from typing import Any


DOMAIN_MANIFEST: dict[str, dict[str, Any]] = {
    "AI/ML Engineer": {
        "required_skills": ["python", "ml", "tensorflow", "pytorch", "nlp", "docker", "git", "aws", "kubernetes"],
        "salary": "₹10–18 LPA",
        "demand": "Very High",
        "keywords": ["ai", "ml", "machine learning", "deep learning", "dl", "nlp", "neural networks", "llm", "computer vision"],
    },
    "Data Scientist": {
        "required_skills": ["python", "ml", "sql", "tensorflow", "pytorch", "spark", "git", "tableau", "excel"],
        "salary": "₹6–15 LPA",
        "demand": "High",
        "keywords": ["data science", "statistics", "predictive modeling", "feature engineering", "experimentation"],
    },
    "Data Analyst": {
        "required_skills": ["sql", "excel", "powerbi", "tableau", "python", "git", "spark"],
        "salary": "₹4–10 LPA",
        "demand": "High",
        "keywords": ["analytics", "dashboarding", "reporting", "business intelligence", "bi"],
    },
    "Full Stack Developer": {
        "required_skills": ["html", "css", "js", "react", "node", "typescript", "mongodb", "graphql", "git", "docker"],
        "salary": "₹5–14 LPA",
        "demand": "Very High",
        "keywords": ["full stack", "mern", "web app", "frontend and backend", "spa"],
    },
    "Backend Developer": {
        "required_skills": ["python", "node", "sql", "fastapi", "django", "docker", "redis", "mongodb", "git"],
        "salary": "₹5–13 LPA",
        "demand": "High",
        "keywords": ["backend", "apis", "microservices", "server side", "rest api"],
    },
    "Software Engineer": {
        "required_skills": ["python", "java", "dsa", "git", "html", "css", "js", "rust", "go"],
        "salary": "₹5–12 LPA",
        "demand": "High",
        "keywords": ["software engineering", "algorithms", "problem solving", "oop", "systems programming"],
    },
    "DevOps Engineer": {
        "required_skills": ["docker", "linux", "aws", "kubernetes", "git", "python", "redis", "go"],
        "salary": "₹6–15 LPA",
        "demand": "High",
        "keywords": ["devops", "cicd", "ci/cd", "infrastructure", "automation"],
    },
    "Cybersecurity Analyst": {
        "required_skills": ["networking", "security", "linux", "python", "git"],
        "salary": "₹7–12 LPA",
        "demand": "High",
        "keywords": ["cybersecurity", "cyber security", "infosec", "threat detection", "soc"],
    },
    "UI/UX Designer": {
        "required_skills": ["figma", "html", "css", "js", "react", "typescript"],
        "salary": "₹4–10 LPA",
        "demand": "Medium",
        "keywords": ["ui", "ux", "design systems", "wireframes", "prototyping"],
    },
}


KEYWORD_MAPPING: dict[str, str] = {
    "ai": "AI/ML Engineer",
    "ml": "AI/ML Engineer",
    "machine learning": "AI/ML Engineer",
    "deep learning": "AI/ML Engineer",
    "dl": "AI/ML Engineer",
    "nlp": "AI/ML Engineer",
    "neural networks": "AI/ML Engineer",
    "computer vision": "AI/ML Engineer",
    "llm": "AI/ML Engineer",
    "llmops": "AI/ML Engineer",
    "devops": "DevOps Engineer",
    "ci/cd": "DevOps Engineer",
    "cicd": "DevOps Engineer",
    "backend": "Backend Developer",
    "full stack": "Full Stack Developer",
    "fullstack": "Full Stack Developer",
    "cybersecurity": "Cybersecurity Analyst",
    "cyber security": "Cybersecurity Analyst",
    "ui": "UI/UX Designer",
    "ux": "UI/UX Designer",
    "data science": "Data Scientist",
    "analytics": "Data Analyst",
}


COMPANY_ARCHETYPES: dict[str, dict[str, str]] = {
    "google": {
        "focus_area": "ALGORITHMIC_COMPLEXITY",
        "interview_style": "data-structure heavy, optimization-focused, and reasoning-first",
    },
    "amazon": {
        "focus_area": "SYSTEM_DESIGN_LOGIC",
        "interview_style": "ownership-oriented, tradeoff-aware, and scenario-based",
    },
    "microsoft": {
        "focus_area": "TECHNICAL_SCREENING",
        "interview_style": "practical engineering, debugging-heavy, and collaborative",
    },
    "meta": {
        "focus_area": "PRODUCT_SCALABILITY",
        "interview_style": "execution-focused, fast-paced, and systems-oriented",
    },
    "netflix": {
        "focus_area": "DISTRIBUTED_SYSTEMS_DECISIONS",
        "interview_style": "senior-level judgment, resiliency, and performance tradeoffs",
    },
    "tcs": {
        "focus_area": "FOUNDATIONAL_DELIVERY_EXCELLENCE",
        "interview_style": "fundamentals-first, delivery-oriented, and process-aware",
    },
    "infosys": {
        "focus_area": "ENTERPRISE_IMPLEMENTATION_BASICS",
        "interview_style": "structured, fundamentals-driven, and service-delivery aligned",
    },
    "accenture": {
        "focus_area": "CONSULTING_PROBLEM_SOLVING",
        "interview_style": "client-scenario based, adaptable, and communication-aware",
    },
    "wipro": {
        "focus_area": "APPLICATION_SUPPORT_AND_AUTOMATION",
        "interview_style": "operations-aware, practical, and fundamentals-focused",
    },
}


LEGACY_DOMAIN_ALIASES: dict[str, str] = {
    "AI-ML Engineer": "AI/ML Engineer",
}


DEFAULT_COMPANY_ARCHETYPE = {
    "focus_area": "GENERAL_TECHNICAL_SCREENING",
    "interview_style": "balanced technical depth, practical problem solving, and clear reasoning",
}


# Addition: lightweight skill ontology and synonym graph for NLP normalization,
# resume parsing, and ML preprocessing. This keeps ontology logic centralized.
SKILL_ONTOLOGY: dict[str, list[str]] = {
    "ai": ["artificial intelligence", "ai"],
    "ml": ["machine learning", "ml"],
    "dl": ["deep learning", "dl"],
    "nlp": ["natural language processing", "nlp"],
    "js": ["javascript", "js"],
    "react": ["reactjs", "react js", "react"],
    "node": ["nodejs", "node js", "node"],
    "sql": ["mysql", "postgresql", "postgres", "sqlite", "sql"],
    "security": ["cyber security", "cybersecurity", "infosec", "security"],
    "aws": ["amazon web services", "aws cloud", "aws"],
    "kubernetes": ["k8s", "kube", "kubernetes"],
    "tensorflow": ["tensorflow", "tf"],
    "pytorch": ["pytorch", "torch", "pt"],
}
