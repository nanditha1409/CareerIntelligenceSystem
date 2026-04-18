"""
Company-aware quiz generation service.
Augments the standard LLM prompt with employer-specific interview constraints.
"""

from config.domain_manifest import COMPANY_ARCHETYPES, DEFAULT_COMPANY_ARCHETYPE
import llm_service


def _resolve_company_profile(company: str | None) -> tuple[str, dict[str, str]]:
    normalized = (company or "").lower().strip()
    if not normalized:
        return "General", DEFAULT_COMPANY_ARCHETYPE
    return normalized.title(), COMPANY_ARCHETYPES.get(normalized, DEFAULT_COMPANY_ARCHETYPE)


def build_company_quiz_prompt(
    domain: str,
    skills: dict[str, int],
    distribution: dict[str, int],
    company: str | None,
    question_count: int = 10,
) -> str:
    base_prompt = llm_service._build_generation_prompt(domain, skills, distribution)
    company_label, archetype = _resolve_company_profile(company)
    return (
        f"{base_prompt}\n\n"
        f"Company interview overlay:\n"
        f"- Generate exactly {question_count} questions.\n"
        f"- Make the tone and evaluation criteria feel like a {company_label} technical screening.\n"
        f"- Emphasize focus area: {archetype['focus_area']}.\n"
        f"- Interview style: {archetype['interview_style']}.\n"
        f"- Prefer realistic technical scenarios over trivia.\n"
        f"- Keep the output schema exactly unchanged.\n"
    )


async def generate_company_questions(
    domain: str,
    skills: dict[str, int],
    distribution: dict[str, int],
    company: str | None,
    question_count: int = 10,
) -> list[dict]:
    # Changed: uses llm_service.generate_with_prompt (Phi-3) instead of direct Gemini call.
    prompt = build_company_quiz_prompt(domain, skills, distribution, company, question_count)
    raw_text = await llm_service.generate_with_prompt(prompt)
    
    if not raw_text:
        return []

    return llm_service._parse_llm_questions(raw_text)[:question_count]
