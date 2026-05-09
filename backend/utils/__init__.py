# Re-export everything from common_utils so `from utils import X` keeps working.
from common_utils import (  # noqa: F401
    SKILLS_LIST,
    SKILL_ALIASES,
    DOMAIN_SKILLS,
    DOMAIN_DATA,
    SKILL_RESOURCES,
    DOMAIN_QUESTIONS,
    normalize_skills,
    resolve_domain_name,
    calculate_compatibility_score,
    compute_unified_score,
    rank_domains_by_compatibility,
    compute_skill_gap,
    compute_readiness_score,
    get_resources_for_skills,
    get_xai_explanation,
)
