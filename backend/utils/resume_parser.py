"""
Task 2: NLP Resume Parser
=========================
Extracts text from PDF/DOCX/TXT uploads and uses spaCy NER + ontology
matching to isolate technical skills and years of experience.

Dependency priority (graceful degradation):
  PDF:  pdfplumber  →  PyMuPDF (fitz)  →  pypdf  →  raw bytes
  NLP:  spaCy en_core_web_md           →  regex ontology fallback
  DOCX: python-docx                    →  raw bytes

Install optional deps:
    pip install pdfplumber pymupdf spacy
    python -m spacy download en_core_web_md
"""

from __future__ import annotations

import io
import re
from typing import Any

# ── Internal imports ──────────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.domain_manifest import DOMAIN_MANIFEST, SKILL_ONTOLOGY
from ml.preprocessing import normalize_skill_phrase, normalize_skills


# ── PDF text extraction ───────────────────────────────────────────────────────

def _extract_pdf_pdfplumber(content: bytes) -> str:
    """Primary PDF extractor — pdfplumber preserves layout well."""
    import pdfplumber
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        return "\n".join(
            page.extract_text() or "" for page in pdf.pages
        )


def _extract_pdf_fitz(content: bytes) -> str:
    """Secondary PDF extractor — PyMuPDF (fitz)."""
    import fitz  # PyMuPDF
    doc = fitz.open(stream=content, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def _extract_pdf_pypdf(content: bytes) -> str:
    """Tertiary PDF extractor — pypdf (already in requirements)."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_file(filename: str, content: bytes) -> str:
    """
    Extract plain text from an uploaded file.
    Tries the best available library for each format.
    """
    lowered = (filename or "").lower()

    if lowered.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")

    if lowered.endswith(".pdf"):
        for extractor in (_extract_pdf_pdfplumber, _extract_pdf_fitz, _extract_pdf_pypdf):
            try:
                text = extractor(content)
                if text.strip():
                    return text
            except Exception:
                continue
        # Last resort: decode raw bytes
        return content.decode("utf-8", errors="ignore")

    if lowered.endswith(".docx"):
        try:
            import docx
            document = docx.Document(io.BytesIO(content))
            return "\n".join(p.text for p in document.paragraphs)
        except Exception:
            return content.decode("utf-8", errors="ignore")

    return content.decode("utf-8", errors="ignore")


# ── spaCy NER skill extraction ────────────────────────────────────────────────

# Lazy-load the spaCy model once.
_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy
        _nlp = spacy.load("en_core_web_md")
    except Exception:
        _nlp = None
    return _nlp


# Build a flat vocabulary from the domain manifest + ontology for fast lookup.
_SKILL_VOCAB: set[str] = {
    skill.lower()
    for manifest in DOMAIN_MANIFEST.values()
    for skill in manifest.get("required_skills", [])
} | {
    synonym.lower()
    for synonyms in SKILL_ONTOLOGY.values()
    for synonym in synonyms
}


def _extract_skills_spacy(text: str) -> list[str]:
    """
    Use spaCy NER + noun-chunk scanning to find technical skills.
    Entities labelled ORG, PRODUCT, or LANGUAGE are strong skill candidates.
    Noun chunks are matched against the skill vocabulary.
    """
    nlp = _get_nlp()
    if nlp is None:
        return []

    doc = nlp(text[:50_000])  # cap to avoid memory issues on large resumes
    candidates: set[str] = set()

    # Named entities — ORG/PRODUCT/LANGUAGE often contain tech names.
    for ent in doc.ents:
        if ent.label_ in {"ORG", "PRODUCT", "LANGUAGE"}:
            token = ent.text.lower().strip()
            if token in _SKILL_VOCAB:
                candidates.add(token)

    # Noun chunks — match against vocabulary.
    for chunk in doc.noun_chunks:
        token = chunk.text.lower().strip()
        if token in _SKILL_VOCAB:
            candidates.add(token)
        # Also try individual tokens inside multi-word chunks.
        for word in chunk:
            w = word.text.lower().strip()
            if w in _SKILL_VOCAB:
                candidates.add(w)

    return list(candidates)


def _extract_skills_regex(text: str) -> list[str]:
    """
    Fallback skill extractor using vocabulary substring matching.
    Deterministic and dependency-free.
    """
    lowered = re.sub(r"\s+", " ", text.lower())
    # Sort by length descending so longer phrases match before substrings.
    vocab_sorted = sorted(_SKILL_VOCAB, key=len, reverse=True)
    matched: list[str] = []
    for term in vocab_sorted:
        if term and re.search(r"\b" + re.escape(term) + r"\b", lowered):
            matched.append(term)
    return matched


def extract_skills_nlp(text: str) -> list[str]:
    """
    Primary NLP skill extraction.
    Uses spaCy NER when available, falls back to regex ontology matching.
    Returns normalized, deduplicated skill tokens.
    """
    spacy_skills = _extract_skills_spacy(text)
    regex_skills = _extract_skills_regex(text)

    # Merge both sources; spaCy results take priority.
    combined = spacy_skills + [s for s in regex_skills if s not in set(spacy_skills)]
    return normalize_skills(normalize_skill_phrase(s) for s in combined)


# ── Years of experience extraction ───────────────────────────────────────────

_EXPERIENCE_PATTERNS = [
    r"(\d+)\+?\s*years?\s+of\s+experience",
    r"(\d+)\+?\s*yrs?\s+of\s+experience",
    r"experience\s+of\s+(\d+)\+?\s*years?",
    r"(\d+)\+?\s*years?\s+experience",
]

def extract_years_of_experience(text: str) -> int | None:
    """
    Extract the most prominent years-of-experience figure from resume text.
    Returns None if no match is found.
    """
    lowered = text.lower()
    for pattern in _EXPERIENCE_PATTERNS:
        match = re.search(pattern, lowered)
        if match:
            return int(match.group(1))
    return None


# ── Summary builder ───────────────────────────────────────────────────────────

def build_resume_analysis(
    filename: str,
    content: bytes,
) -> dict[str, Any]:
    """
    Full pipeline: extract text → NLP skill extraction → years of experience.
    Returns a structured dict ready for the API response.
    """
    text   = extract_text_from_file(filename, content)
    skills = extract_skills_nlp(text)
    years  = extract_years_of_experience(text)

    return {
        "extracted_text": text,
        "skills":         skills,
        "years_of_experience": years,
        "text_preview":   text[:1000],
    }
