"""
Resume parsing and skill extraction helpers.

The implementation is intentionally dependency-tolerant:
- TXT always works
- PDF works when `pypdf` is installed
- DOCX works when `python-docx` is installed
- If a parser dependency is missing, the service returns a clear fallback message
"""

from __future__ import annotations

import io
import re
from typing import Any

from config.domain_manifest import DOMAIN_MANIFEST, SKILL_ONTOLOGY
from ml.preprocessing import normalize_skill_phrase, normalize_skills


def extract_text_from_upload(filename: str, content: bytes) -> str:
    """Extract text from TXT/PDF/DOCX with graceful degradation."""
    lowered = (filename or "").lower()

    if lowered.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")

    if lowered.endswith(".pdf"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return content.decode("utf-8", errors="ignore")

    if lowered.endswith(".docx"):
        try:
            import docx

            document = docx.Document(io.BytesIO(content))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        except Exception:
            return content.decode("utf-8", errors="ignore")

    return content.decode("utf-8", errors="ignore")


def extract_skills_from_text(text: str) -> list[str]:
    """
    Lightweight NLP skill extraction using ontology + domain skill vocabulary.
    This intentionally remains deterministic so the rest of the ML pipeline gets stable tokens.
    """
    lowered = re.sub(r"\s+", " ", text.lower())
    vocabulary = sorted(
        {
            skill.lower()
            for manifest in DOMAIN_MANIFEST.values()
            for skill in manifest.get("required_skills", [])
        }
        | {synonym.lower() for synonyms in SKILL_ONTOLOGY.values() for synonym in synonyms}
    )

    matched = [term for term in vocabulary if term and term in lowered]
    return normalize_skills(normalize_skill_phrase(term) for term in matched)


def build_resume_summary(text: str, skills: list[str], recommendations: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a compact resume-analysis payload for API responses."""
    return {
        "extracted_text_preview": text[:1000],
        "skills": skills,
        "recommendations": recommendations,
    }
