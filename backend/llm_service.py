"""
LLM service — Gemini-backed question generation and consultant chat.
Falls back to questions.json if the API key is missing or the call fails.
"""
import json
import os
import re
import time
from typing import AsyncIterator

import google.generativeai as genai
from pydantic import BaseModel, ValidationError

# ── Config ────────────────────────────────────────────────────────────────────
_API_KEY = os.getenv("GEMINI_API_KEY", "")
_CONFIGURED = False

if _API_KEY and _API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=_API_KEY)
    _CONFIGURED = True

_GEN_MODEL  = "gemini-1.5-flash"
_CHAT_MODEL = "gemini-1.5-flash"

# ── In-memory question cache  {(domain, skills_fingerprint): (timestamp, questions)} ──
_QUESTION_CACHE: dict[tuple, tuple[float, list]] = {}
_CACHE_TTL = 3600  # 1 hour


# ── Pydantic schema for LLM-generated questions ───────────────────────────────
class GeneratedQuestion(BaseModel):
    id: str
    text: str
    options: list[str]
    correct_index: int
    topic_tag: str

    def model_post_init(self, __context):
        assert len(self.options) == 4,          "options must have exactly 4 items"
        assert 0 <= self.correct_index <= 3,    "correct_index must be 0-3"
        assert self.text.strip(),               "text must not be empty"


def _skills_fingerprint(skills: dict[str, int]) -> str:
    """Stable string key from a skills dict for cache lookup."""
    return "|".join(f"{k}:{v}" for k, v in sorted(skills.items()))


def _build_generation_prompt(domain: str, skills: dict[str, int]) -> str:
    skill_lines = "\n".join(
        f"  - {skill}: {'Beginner (1-2)' if lvl <= 2 else 'Intermediate (3)' if lvl == 3 else 'Expert (4-5)'} (level {lvl}/5)"
        for skill, lvl in skills.items()
    )
    difficulty_note = (
        "Most skills are beginner level — focus on fundamental conceptual questions."
        if sum(skills.values()) / max(len(skills), 1) <= 2.5
        else "Skills are mixed/advanced — include scenario-based and architectural questions for expert-level skills."
    )

    return f"""You are a senior technical interviewer. Generate exactly 10 multiple-choice questions for a **{domain}** role.

Candidate skill proficiencies (1=Beginner, 5=Expert):
{skill_lines}

Difficulty guidance: {difficulty_note}
- For skills rated 1-2: ask fundamental conceptual questions.
- For skills rated 4-5: ask scenario-based or architectural questions.

Return ONLY a valid JSON array (no markdown, no explanation) with exactly this schema:
[
  {{
    "id": "q1",
    "text": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "topic_tag": "Topic Name"
  }}
]

Rules:
- Exactly 10 questions, each with exactly 4 options.
- correct_index is 0-3 (index of the correct option in the options array).
- topic_tag is a short subject label (e.g. "Cryptography", "React Hooks", "System Design").
- Questions must be specific to {domain} — no generic trivia.
- Do NOT include the answer in the question text."""


def _parse_llm_questions(raw: str) -> list[dict]:
    """Extract and validate JSON array from LLM response."""
    # Strip markdown code fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip()

    # Find the JSON array
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in LLM response")

    data = json.loads(match.group())
    if not isinstance(data, list):
        raise ValueError("LLM response is not a JSON array")

    validated = []
    for i, item in enumerate(data):
        # Ensure id is set
        if not item.get("id"):
            item["id"] = f"q{i+1}"
        # Normalise sub_topic alias
        if "sub_topic" in item and "topic_tag" not in item:
            item["topic_tag"] = item["sub_topic"]
        try:
            q = GeneratedQuestion(**item)
            validated.append({
                "id":            q.id,
                "text":          q.text,
                "question":      q.text,       # alias
                "options":       q.options,
                "correct_index": q.correct_index,
                "sub_topic":     q.topic_tag,
                "topic_tag":     q.topic_tag,
            })
        except (ValidationError, AssertionError):
            continue  # skip malformed questions

    if len(validated) < 5:
        raise ValueError(f"Only {len(validated)} valid questions parsed — too few")

    return validated[:10]


async def generate_questions(domain: str, skills: dict[str, int]) -> list[dict]:
    """
    Generate 10 questions via Gemini. Returns cached result if available.
    Raises RuntimeError if LLM is not configured.
    """
    if not _CONFIGURED:
        raise RuntimeError("GEMINI_API_KEY not set")

    fp  = _skills_fingerprint(skills)
    key = (domain, fp)
    now = time.time()

    # Cache hit
    if key in _QUESTION_CACHE:
        ts, cached = _QUESTION_CACHE[key]
        if now - ts < _CACHE_TTL:
            return cached

    prompt = _build_generation_prompt(domain, skills)
    model  = genai.GenerativeModel(_GEN_MODEL)

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            max_output_tokens=4096,
        ),
    )

    questions = _parse_llm_questions(response.text)
    _QUESTION_CACHE[key] = (now, questions)
    return questions


async def stream_chat(system_prompt: str, user_message: str) -> AsyncIterator[str]:
    """
    Stream a Gemini chat response token by token.
    Yields text chunks as they arrive.
    """
    if not _CONFIGURED:
        yield "AI consultant is unavailable — GEMINI_API_KEY not configured."
        return

    model = genai.GenerativeModel(
        _CHAT_MODEL,
        system_instruction=system_prompt,
    )
    response = model.generate_content(
        user_message,
        generation_config=genai.GenerationConfig(temperature=0.6, max_output_tokens=1024),
        stream=True,
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text
