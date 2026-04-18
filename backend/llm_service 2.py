"""
LLM service — Phi-3 (Ollama) backed question generation and consultant chat.
Falls back to questions.json if the call fails.
"""
import json
import os
import re
import time
from typing import AsyncIterator

import requests
from pydantic import BaseModel, ValidationError, field_validator, model_validator

# ── Config ────────────────────────────────────────────────────────────────────
# Changed: We now use local Phi-3 via Ollama instead of Gemini.
_OLLAMA_URL = "http://localhost:11434/api/generate"
_MODEL = "phi3"
_CONFIGURED = True # Assume Ollama is running if this task is requested

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

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: list[str]) -> list[str]:
        if len(value) != 4:
            raise ValueError("options must have exactly 4 items")
        cleaned = [str(v).strip() for v in value]
        if any(not option for option in cleaned):
            raise ValueError("options must not contain empty values")
        return cleaned

    @field_validator("correct_index")
    @classmethod
    def validate_correct_index(cls, value: int) -> int:
        if value < 0 or value > 3:
            raise ValueError("correct_index must be 0-3")
        return value

    @field_validator("text", "topic_tag")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError("text fields must not be empty")
        return cleaned


class GeneratedQuestionSet(BaseModel):
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

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        # Try to fix common Phi-3 JSON issues (trailing commas, etc.)
        # This is a very basic attempt.
        cleaned = re.sub(r",\s*\]", "]", match.group())
        cleaned = re.sub(r",\s*\}", "}", cleaned)
        data = json.loads(cleaned)

    if not isinstance(data, list):
        raise ValueError("LLM response is not a JSON array")

    validated = []
    for i, item in enumerate(data):
        if not item.get("id"):
            item["id"] = f"q{i+1}"
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

    return validated[:10]


async def generate_questions(domain: str, skills: dict[str, int], distribution: dict[str, int]) -> list[dict]:
    """
    Generate 10 questions via local Phi-3. Returns cached result if available.
    """
    fp  = f"{_skills_fingerprint(skills)}|dist:{_skills_fingerprint(distribution)}"
    key = (domain, fp)
    now = time.time()

    if key in _QUESTION_CACHE:
        ts, cached = _QUESTION_CACHE[key]
        if now - ts < _CACHE_TTL:
            return cached

    prompt = _build_generation_prompt(domain, skills, distribution)
    
    try:
        response = requests.post(
            _OLLAMA_URL,
            json={
                "model": _MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json", # Phi-3 supports JSON mode
            },
            timeout=60,
        )
        response.raise_for_status()
        raw_text = response.json().get("response", "")
        questions = _parse_llm_questions(raw_text)
        
        if not questions:
            raise ValueError("No valid questions generated")
            
        _QUESTION_CACHE[key] = (now, questions)
        return questions
    except Exception as e:
        print(f"Phi-3 generation failed: {e}")
        # Return empty list to trigger fallback to static questions in app.py
        return []


async def generate_with_prompt(prompt: str) -> str:
    """
    Generic prompt completion via Phi-3.
    """
    try:
        response = requests.post(
            _OLLAMA_URL,
            json={
                "model": _MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"Phi-3 generation failed: {e}")
        return ""


async def stream_chat(system_prompt: str, user_message: str) -> AsyncIterator[str]:
    """
    Stream a Phi-3 chat response token by token.
    """
    try:
        full_prompt = f"{system_prompt}\n\nUser: {user_message}" if system_prompt else user_message
        
        response = requests.post(
            _OLLAMA_URL,
            json={
                "model": _MODEL,
                "prompt": full_prompt,
                "stream": True,
            },
            stream=True,
            timeout=60,
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                text = chunk.get("response", "")
                if text:
                    yield text
                if chunk.get("done"):
                    break
    except Exception as e:
        yield f"AI service unavailable (Phi-3): {str(e)}"
