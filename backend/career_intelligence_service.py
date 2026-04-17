"""
Optional intelligence service:
- Keeps existing recommendation flow untouched.
- Adds explainable career-path enrichment payloads for new endpoints.
"""

from utils import DOMAIN_SKILLS, normalize_skills, resolve_domain_name


def build_career_pathways(user_skills: list[str], top_domains: list[str]) -> list[dict]:
    # Defensive normalization so endpoint behavior stays stable across legacy/new inputs.
    normalized = normalize_skills(user_skills)
    skill_set = set(normalized)
    pathways: list[dict] = []

    for domain in top_domains:
        canonical_domain = resolve_domain_name(domain)
        required = DOMAIN_SKILLS.get(canonical_domain, [])
        if not required:
            # Skip unknown domains quietly to remain backward-compatible.
            continue

        strengths = [s for s in required if s in skill_set][:5]
        missing = [s for s in required if s not in skill_set][:5]

        # Small deterministic sequence to help frontend render a guided path.
        next_steps = [
            f"Deepen {strengths[0] if strengths else required[0]} with projects",
            f"Learn {missing[0] if missing else required[min(1, len(required) - 1)]}",
            "Build portfolio and attempt role-specific assessments",
        ]

        pathways.append(
            {
                "domain": canonical_domain,
                "strengths": strengths,
                "skills_to_learn": missing,
                "career_path": next_steps,
            }
        )
    return pathways
