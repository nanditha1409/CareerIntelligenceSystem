"""
Task 3: NLP Integration — Resume Parsing with spaCy + Cosine Similarity
========================================================================
Uses spaCy (en_core_web_sm) to parse uploaded resume text.
Extracts skills by matching NER entities and noun chunks against
master_skills_list.json, then scores the user's skill vector against
each domain using cosine similarity.

Public API
----------
    extract_skills_nlp(text)                    → list[str]
    score_skills_against_domains(skills)        → list[dict]
    parse_resume(text)                          → dict
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR            = os.path.dirname(os.path.dirname(__file__))
MASTER_SKILLS_PATH  = os.path.join(BASE_DIR, "data", "master_skills_list.json")

# ── Load master skills list ───────────────────────────────────────────────────

def _load_master_skills() -> list[str]:
    if os.path.exists(MASTER_SKILLS_PATH):
        with open(MASTER_SKILLS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [s.lower().strip() for s in data.get("skills", [])]
    # Minimal fallback if file is missing
    return [
        "python", "java", "javascript", "typescript", "sql", "html", "css",
        "react", "node", "docker", "kubernetes", "aws", "git", "linux",
        "tensorflow", "pytorch", "ml", "nlp", "deep learning", "spark",
        "pandas", "numpy", "tableau", "powerbi", "figma", "solidity",
        "security", "networking", "flutter", "kotlin", "swift",
    ]

MASTER_SKILLS: list[str] = _load_master_skills()
MASTER_SKILLS_SET: set[str] = set(MASTER_SKILLS)

# ── spaCy loader (graceful fallback) ─────────────────────────────────────────

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Model not downloaded yet — try en_core_web_md as fallback
            try:
                _nlp = spacy.load("en_core_web_md")
            except OSError:
                _nlp = None
    except ImportError:
        _nlp = None
    return _nlp


# ── Domain corpus for cosine similarity ──────────────────────────────────────

def _build_domain_corpus() -> dict[str, str]:
    try:
        from config.domain_manifest import DOMAIN_MANIFEST
        corpus: dict[str, str] = {}
        for domain, manifest in DOMAIN_MANIFEST.items():
            skills = manifest.get("required_skills", [])
            keywords = manifest.get("keywords", [])
            corpus[domain] = " ".join(skills + keywords)
        return corpus
    except ImportError:
        return {}

_DOMAIN_CORPUS: dict[str, str] = _build_domain_corpus()


# ── Skill extraction ──────────────────────────────────────────────────────────

def _regex_extract(text: str) -> list[str]:
    """Fast regex-based skill extraction against the master list."""
    text_lower = text.lower()
    found: list[str] = []
    for skill in MASTER_SKILLS:
        # Use word-boundary matching for short tokens to avoid false positives
        if len(skill) <= 3:
            pattern = r"\b" + re.escape(skill) + r"\b"
        else:
            pattern = re.escape(skill)
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


def _spacy_extract(text: str) -> list[str]:
    """
    Use spaCy NER + noun chunks to extract candidate skill phrases,
    then filter against the master skills list.
    """
    nlp = _get_nlp()
    if nlp is None:
        return []

    doc = nlp(text[:50000])  # cap to avoid memory issues on large docs
    candidates: set[str] = set()

    # Named entities (ORG, PRODUCT often capture tech names)
    for ent in doc.ents:
        candidates.add(ent.text.lower().strip())

    # Noun chunks (captures "machine learning", "deep learning", etc.)
    for chunk in doc.noun_chunks:
        candidates.add(chunk.text.lower().strip())

    # Individual tokens that look like tech terms
    for token in doc:
        if not token.is_stop and not token.is_punct and len(token.text) > 1:
            candidates.add(token.text.lower().strip())

    # Filter against master list
    matched: list[str] = []
    for candidate in candidates:
        if candidate in MASTER_SKILLS_SET:
            matched.append(candidate)
        else:
            # Partial match for multi-word skills
            for skill in MASTER_SKILLS:
                if " " in skill and skill in candidate:
                    matched.append(skill)
                    break

    return list(set(matched))


def extract_skills_nlp(text: str) -> list[str]:
    """
    Extract skills from resume text.
    Combines spaCy NER (when available) with regex matching against master_skills_list.json.
    Returns a deduplicated, sorted list of matched skills.
    """
    regex_skills = _regex_extract(text)
    spacy_skills = _spacy_extract(text)

    combined = list(dict.fromkeys(regex_skills + spacy_skills))  # preserve order, deduplicate
    return sorted(combined)


# ── Cosine similarity scoring ─────────────────────────────────────────────────

def score_skills_against_domains(skills: list[str], top_k: int = 5) -> list[dict[str, Any]]:
    """
    Compute cosine similarity between the user's skill vector and each domain corpus.
    Returns top_k domains sorted by similarity score descending.

    Each result:
        {
            "domain": str,
            "similarity_score": float,   # 0.0 – 1.0
            "matching_keywords": list[str],
        }
    """
    if not skills or not _DOMAIN_CORPUS:
        return []

    user_doc = " ".join(skills)
    domains  = list(_DOMAIN_CORPUS.keys())
    corpus   = [_DOMAIN_CORPUS[d] for d in domains]

    # Fit TF-IDF on domain corpus + user doc together
    all_docs = corpus + [user_doc]
    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        matrix     = vectorizer.fit_transform(all_docs)
    except ValueError:
        return []

    domain_matrix = matrix[:-1]
    user_vector   = matrix[-1]

    scores = cosine_similarity(user_vector, domain_matrix)[0]

    results: list[dict[str, Any]] = []
    for i, domain in enumerate(domains):
        domain_skills = _DOMAIN_CORPUS[domain].split()
        matching = [s for s in skills if s in domain_skills or any(s in ds for ds in domain_skills)]
        results.append({
            "domain":           domain,
            "similarity_score": round(float(scores[i]), 4),
            "matching_keywords": list(dict.fromkeys(matching))[:8],
        })

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:top_k]


# ── Full resume parse ─────────────────────────────────────────────────────────

def parse_resume(text: str) -> dict[str, Any]:
    """
    Full NLP resume parse:
      1. Extract skills via spaCy + regex
      2. Score against domains via cosine similarity
      3. Return structured result

    Returns:
        {
            "skills": list[str],
            "domain_scores": list[dict],
            "top_domain": str | None,
            "top_similarity": float,
        }
    """
    skills       = extract_skills_nlp(text)
    domain_scores = score_skills_against_domains(skills, top_k=5)
    top           = domain_scores[0] if domain_scores else {}

    return {
        "skills":         skills,
        "domain_scores":  domain_scores,
        "top_domain":     top.get("domain"),
        "top_similarity": top.get("similarity_score", 0.0),
    }
