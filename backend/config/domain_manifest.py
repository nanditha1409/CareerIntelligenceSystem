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
    "Cloud Engineer": {
        "required_skills": ["aws", "docker", "kubernetes", "linux", "python", "git", "networking"],
        "salary": "₹8–18 LPA",
        "demand": "High",
        "keywords": ["cloud", "cloud computing", "azure", "gcp", "infrastructure as code"],
    },
    "Cybersecurity Analyst": {
        "required_skills": ["networking", "security", "linux", "python", "git"],
        "salary": "₹7–12 LPA",
        "demand": "High",
        "keywords": ["cybersecurity", "cyber security", "infosec", "threat detection", "soc"],
    },
    "Blockchain Developer": {
        "required_skills": ["solidity", "rust", "go", "js", "git", "security"],
        "salary": "₹8–20 LPA",
        "demand": "Medium",
        "keywords": ["blockchain", "web3", "smart contracts", "defi", "solidity"],
    },
    "Embedded Systems Engineer": {
        "required_skills": ["c", "c++", "python", "linux", "networking", "git"],
        "salary": "₹6–16 LPA",
        "demand": "High",
        "keywords": ["embedded", "firmware", "microcontroller", "rtos", "hardware"],
    },
    "Mobile App Developer": {
        "required_skills": ["js", "typescript", "react", "java", "git", "graphql"],
        "salary": "₹5–14 LPA",
        "demand": "High",
        "keywords": ["android", "ios", "mobile", "react native", "flutter"],
    },
    "QA Automation Engineer": {
        "required_skills": ["python", "java", "js", "git", "docker", "sql"],
        "salary": "₹5–11 LPA",
        "demand": "High",
        "keywords": ["qa", "test automation", "selenium", "cypress", "quality engineering"],
    },
    "Site Reliability Engineer": {
        "required_skills": ["linux", "python", "go", "docker", "kubernetes", "aws", "git", "networking"],
        "salary": "₹10–22 LPA",
        "demand": "High",
        "keywords": ["sre", "reliability", "observability", "incident response", "production systems"],
    },
    "Product Manager": {
        "required_skills": ["excel", "sql", "figma", "analytics", "communication", "roadmapping"],
        "salary": "₹8–20 LPA",
        "demand": "Medium",
        "keywords": ["product", "roadmap", "stakeholder management", "user stories", "prioritization"],
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
    "blockchain": "Blockchain Developer",
    "web3": "Blockchain Developer",
    "embedded": "Embedded Systems Engineer",
    "firmware": "Embedded Systems Engineer",
    "backend": "Backend Developer",
    "full stack": "Full Stack Developer",
    "fullstack": "Full Stack Developer",
    "cybersecurity": "Cybersecurity Analyst",
    "cyber security": "Cybersecurity Analyst",
    "cloud": "Cloud Engineer",
    "sre": "Site Reliability Engineer",
    "qa automation": "QA Automation Engineer",
    "mobile": "Mobile App Developer",
    "product": "Product Manager",
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
