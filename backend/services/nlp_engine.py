"""
Stage 3: NLP Pipeline — Resume Parsing + Cosine Similarity
===========================================================
Uses spaCy (en_core_web_sm) to extract technical entities from raw text,
then scores the extracted skill vector against each domain centroid using
sklearn cosine similarity.

Public API
----------
    extract_skills(text)                    → list[str]
    score_against_domains(skills, top_k)    → list[dict]
    parse_resume_nlp(text)                  → dict
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

BASE_DIR           = os.path.dirname(os.path.dirname(__file__))
MASTER_SKILLS_PATH = os.path.join(BASE_DIR, "data", "master_skills_list.json")

# ── Master skills vocabulary ──────────────────────────────────────────────────

def _load_master_skills() -> list[str]:
    if os.path.exists(MASTER_SKILLS_PATH):
        with open(MASTER_SKILLS_PATH, "r", encoding="utf-8") as f:
            return [s.lower().strip() for s in json.load(f).get("skills", [])]
    # Inline fallback so the module works even without the JSON file
    return [
        "python", "java", "javascript", "typescript", "c", "c++", "go", "rust", "r",
        "sql", "mysql", "postgresql", "mongodb", "redis", "cassandra",
        "html", "css", "react", "angular", "vue", "node", "express", "django", "fastapi",
        "tensorflow", "pytorch", "keras", "scikit-learn", "xgboost", "huggingface",
        "machine learning", "deep learning", "nlp", "computer vision", "llm",
        "docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ansible", "jenkins",
        "git", "linux", "bash", "ci/cd", "devops",
        "pandas", "numpy", "spark", "hadoop", "kafka", "airflow",
        "tableau", "power bi", "excel", "figma", "sketch",
        "solidity", "web3", "ethereum", "smart contracts", "blockchain",
        "networking", "security", "cryptography", "penetration testing",
        "selenium", "cypress", "pytest", "junit", "jest",
        "flutter", "dart", "swift", "kotlin", "react native",
        "graphql", "rest api", "grpc", "microservices",
        "prometheus", "grafana", "elk", "observability",
        "dsa", "algorithms", "system design", "oop", "design patterns",
        "agile", "scrum", "jira", "figma", "wireframes", "prototyping",
        "statistics", "probability", "feature engineering",
        "rtos", "microcontroller", "firmware", "arm", "fpga",
    ]


MASTER_SKILLS: list[str] = _load_master_skills()
MASTER_SKILLS_SET: set[str] = set(MASTER_SKILLS)

# Multi-word skills sorted longest-first for greedy regex matching
_MULTI_WORD = sorted([s for s in MASTER_SKILLS if " " in s], key=len, reverse=True)
_SINGLE_WORD = [s for s in MASTER_SKILLS if " " not in s]


# ── spaCy loader ──────────────────────────────────────────────────────────────

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy
        for model_name in ("en_core_web_sm", "en_core_web_md", "en_core_web_lg"):
            try:
                _nlp = spacy.load(model_name)
                return _nlp
            except OSError:
                continue
    except ImportError:
        pass
    _nlp = None
    return _nlp


# ── Domain corpus (centroid vectors) ─────────────────────────────────────────

def _build_domain_corpus() -> dict[str, str]:
    """Build one rich text document per domain for cosine similarity scoring."""
    try:
        from config.domain_manifest import DOMAIN_MANIFEST
        return {
            domain: " ".join(
                manifest.get("required_skills", []) * 3
                + manifest.get("keywords", [])
            )
            for domain, manifest in DOMAIN_MANIFEST.items()
        }
    except ImportError:
        return {}


_DOMAIN_CORPUS: dict[str, str] = _build_domain_corpus()
log = logging.getLogger(__name__)


# ── Skill extraction ──────────────────────────────────────────────────────────

def _regex_extract(text: str) -> list[str]:
    """
    Greedy regex extraction against the master skills list.
    Multi-word phrases are matched first to avoid partial overlaps.
    """
    text_lower = re.sub(r"\s+", " ", text.lower())
    found: list[str] = []

    for phrase in _MULTI_WORD:
        if re.search(r"\b" + re.escape(phrase) + r"\b", text_lower):
            found.append(phrase)

    for skill in _SINGLE_WORD:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)

    return list(dict.fromkeys(found))  # deduplicate, preserve order


def _spacy_extract(text: str) -> list[str]:
    """
    spaCy NER + noun-chunk extraction.
    Entities labelled ORG, PRODUCT, LANGUAGE are strong tech-skill candidates.
    Noun chunks are matched against the master vocabulary.
    """
    nlp = _get_nlp()
    if nlp is None:
        return []

    doc = nlp(text[:50_000])
    candidates: set[str] = set()

    for ent in doc.ents:
        if ent.label_ in {"ORG", "PRODUCT", "LANGUAGE"}:
            candidates.add(ent.text.lower().strip())

    for chunk in doc.noun_chunks:
        candidates.add(chunk.text.lower().strip())
        for token in chunk:
            if not token.is_stop and not token.is_punct:
                candidates.add(token.text.lower().strip())

    matched: list[str] = []
    for candidate in candidates:
        if candidate in MASTER_SKILLS_SET:
            matched.append(candidate)
        else:
            for phrase in _MULTI_WORD:
                if phrase in candidate:
                    matched.append(phrase)
                    break

    return list(set(matched))


def extract_skills(text: str) -> list[str]:
    """
    Primary skill extraction entry point.
    Combines spaCy NER (when available) with regex matching.
    Returns a deduplicated, sorted list of canonical skill tokens.
    """
    regex_skills = _regex_extract(text)
    spacy_skills = _spacy_extract(text)
    combined = list(dict.fromkeys(regex_skills + [s for s in spacy_skills if s not in set(regex_skills)]))
    return sorted(combined)


def evaluate_skill_extractor(df: pd.DataFrame, sample_n: int = 200) -> dict[str, float]:
    """
    Self-evaluate extraction by reconstructing synthetic resume sentences from
    skills_text rows and comparing extracted skills against the known tokens.
    """
    try:
        if df.empty:
            return {"mean_precision": 0.0, "mean_recall": 0.0, "mean_f1": 0.0, "n_evaluated": 0}

        sample_size = min(sample_n, len(df))
        sampled = df.sample(n=sample_size, random_state=42) if sample_size else df.iloc[0:0]

        precisions: list[float] = []
        recalls: list[float] = []
        f1s: list[float] = []

        for _, row in sampled.iterrows():
            skills_text = str(row.get("skills_text", "")).strip().lower()
            true_skills = [token for token in skills_text.split() if token in MASTER_SKILLS_SET]
            true_set = set(true_skills)
            if not true_set:
                continue

            sentence = f"I have experience with {', '.join(true_skills)}"
            extracted = [skill for skill in extract_skills(sentence) if skill in MASTER_SKILLS_SET]
            extracted_set = set(extracted)
            overlap = extracted_set & true_set

            precision = (len(overlap) / len(extracted_set)) if extracted_set else 0.0
            recall = len(overlap) / len(true_set)
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

            precisions.append(precision)
            recalls.append(recall)
            f1s.append(f1)

        n_evaluated = len(f1s)
        return {
            "mean_precision": round(sum(precisions) / n_evaluated, 4) if n_evaluated else 0.0,
            "mean_recall": round(sum(recalls) / n_evaluated, 4) if n_evaluated else 0.0,
            "mean_f1": round(sum(f1s) / n_evaluated, 4) if n_evaluated else 0.0,
            "n_evaluated": n_evaluated,
        }
    except Exception as exc:
        log.warning("Skill extractor evaluation failed: %s", exc)
        return {"mean_precision": 0.0, "mean_recall": 0.0, "mean_f1": 0.0, "n_evaluated": 0}


# ── Cosine similarity scoring ─────────────────────────────────────────────────

def score_against_domains(
    skills: list[str],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Compute cosine similarity between the user's skill vector and each domain
    centroid using sklearn.metrics.pairwise.cosine_similarity.

    Each result:
        {
          "domain":            str,
          "similarity_score":  float,   # 0.0 – 1.0
          "confidence_pct":    float,   # 0 – 100
          "matching_keywords": list[str],
        }
    """
    if not skills or not _DOMAIN_CORPUS:
        return []

    user_doc = " ".join(skills)
    domains  = list(_DOMAIN_CORPUS.keys())
    corpus   = [_DOMAIN_CORPUS[d] for d in domains]

    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
        matrix     = vectorizer.fit_transform(corpus + [user_doc])
    except ValueError:
        return []

    domain_matrix = matrix[:-1]
    user_vector   = matrix[-1]

    scores = cosine_similarity(user_vector, domain_matrix)[0]

    results: list[dict[str, Any]] = []
    for i, domain in enumerate(domains):
        domain_tokens = set(_DOMAIN_CORPUS[domain].split())
        matching = [s for s in skills if s in domain_tokens
                    or any(s in tok for tok in domain_tokens)]
        results.append({
            "domain":            domain,
            "similarity_score":  round(float(scores[i]), 4),
            "confidence_pct":    round(float(scores[i]) * 100, 2),
            "matching_keywords": list(dict.fromkeys(matching))[:8],
        })

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:top_k]


# ── Years of experience ───────────────────────────────────────────────────────

_EXP_PATTERNS = [
    r"(\d+)\+?\s*years?\s+of\s+(?:professional\s+)?experience",
    r"(\d+)\+?\s*yrs?\s+(?:of\s+)?experience",
    r"experience\s+of\s+(\d+)\+?\s*years?",
    r"(\d+)\+?\s*years?\s+(?:in|working)",
]

def _extract_years(text: str) -> int | None:
    for pattern in _EXP_PATTERNS:
        m = re.search(pattern, text.lower())
        if m:
            return int(m.group(1))
    return None


# ── Full resume parse ─────────────────────────────────────────────────────────

def parse_resume_nlp(text: str) -> dict[str, Any]:
    """
    Full NLP resume parse pipeline:
      1. Extract skills via spaCy NER + regex
      2. Score against domain centroids via cosine similarity
      3. Return structured result ready for the API

    Returns:
        {
          "skills":           list[str],
          "domain_scores":    list[dict],
          "top_domain":       str | None,
          "top_similarity":   float,
          "years_experience": int | None,
          "skill_count":      int,
        }
    """
    skills        = extract_skills(text)
    domain_scores = score_against_domains(skills, top_k=5)
    top           = domain_scores[0] if domain_scores else {}

    return {
        "skills":           skills,
        "domain_scores":    domain_scores,
        "top_domain":       top.get("domain"),
        "top_similarity":   top.get("similarity_score", 0.0),
        "years_experience": _extract_years(text),
        "skill_count":      len(skills),
    }
