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
from pydantic import BaseModel, ValidationError, field_validator, model_validator

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

    # Change: strict per-question validation prevents malformed payloads from reaching frontend.
    @field_validator("options")
    @classmethod
    def validate_options(cls, value: list[str]) -> list[str]:
        if len(value) != 4:
            raise ValueError("options must have exactly 4 items")
        cleaned = [str(v).strip() for v in value]
        if any(not option for option in cleaned):
            raise ValueError("options must not contain empty values")
        return cleaned

    # Change: enforce frontend-compatible bounds for answer index.
    @field_validator("correct_index")
    @classmethod
    def validate_correct_index(cls, value: int) -> int:
        if value < 0 or value > 3:
            raise ValueError("correct_index must be 0-3")
        return value

    # Change: normalize text fields and block empty/whitespace-only values.
    @field_validator("text", "topic_tag")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError("text fields must not be empty")
        return cleaned


class GeneratedQuestionSet(BaseModel):
    # Change: validate the complete LLM payload shape before API response is sent.
    items: list[GeneratedQuestion]

    @model_validator(mode="after")
    def validate_exact_count(self):
        if len(self.items) != 10:
            raise ValueError("LLM must return exactly 10 questions")
        return self


def _skills_fingerprint(skills: dict[str, int]) -> str:
    """Stable string key from a skills dict for cache lookup."""
    return "|".join(f"{k}:{v}" for k, v in sorted(skills.items()))


def _build_generation_prompt(domain: str, skills: dict[str, int], distribution: dict[str, int]) -> str:
    # Change: include weighted distribution directly in prompt to enforce proportional generation.
    distribution_line = ", ".join(f"{count} {skill}" for skill, count in distribution.items())
    level_map = "\n".join(f"  - {skill}: level {skills.get(skill, 3)}/5" for skill in distribution.keys())

    return f"""Act as an expert technical interviewer.
Generate exactly 10 multiple-choice questions for domain "{domain}" based on this distribution: {distribution_line}.

Skill levels:
{level_map}

Difficulty scaling:
- Level 1: Basic Syntax / Fundamentals
- Level 2: Core Concepts
- Level 3: Problem Solving / Applied Scenarios
- Level 4: Advanced Implementation
- Level 5: System Design / Architecture

Return ONLY a JSON array (no markdown, no prose) with schema:
[{{"id":"q1","text":"...","options":["...","...","...","..."],"correct_index":0,"topic_tag":"..."}}]

Hard rules:
- Exactly 10 questions total.
- Exactly 4 options per question.
- correct_index must be 0-3.
- topic_tag should map to the relevant skill/topic.
- Keep questions domain-specific to "{domain}".
- Use IDs q1...q10 in order."""


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
        except (ValidationError, ValueError):
            continue  # skip malformed questions

    # Change: strict payload-level validation required by frontend safety requirements.
    # Change: validate only the first 10 questions to enforce exact frontend contract.
    first_ten = validated[:10]
    GeneratedQuestionSet(items=[GeneratedQuestion(**{
        "id": q["id"],
        "text": q["text"],
        "options": q["options"],
        "correct_index": q["correct_index"],
        "topic_tag": q["topic_tag"],
    }) for q in first_ten])

    return first_ten


async def generate_questions(domain: str, skills: dict[str, int], distribution: dict[str, int]) -> list[dict]:
    """
    Generate 10 questions via Gemini. Returns cached result if available.
    Raises RuntimeError if LLM is not configured.
    """
    if not _CONFIGURED:
        raise RuntimeError("GEMINI_API_KEY not set")

    # Change: cache key now includes distribution to guarantee score/evaluation consistency.
    fp  = f"{_skills_fingerprint(skills)}|dist:{_skills_fingerprint(distribution)}"
    key = (domain, fp)
    now = time.time()

    # Cache hit
    if key in _QUESTION_CACHE:
        ts, cached = _QUESTION_CACHE[key]
        if now - ts < _CACHE_TTL:
            return cached

    prompt = _build_generation_prompt(domain, skills, distribution)
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
