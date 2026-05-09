"""
Task 3: Semantic Similarity — TF-IDF Cosine + optional SBERT
=============================================================
Replaces hardcoded keyword→domain mappings with a vector-space model that
understands "Neural Networks" ≈ "ML" ≈ "Deep Learning" mathematically.

Two backends are supported:
  1. TF-IDF + cosine similarity  (always available, CPU-only, fast)
  2. Sentence-Transformers SBERT (optional; richer semantics when installed)

Public API
----------
    find_similar_domains(user_skills, top_k=3)  → list[dict]
    semantic_skill_match(skill, domain)          → float  (0-1)
    build_domain_corpus()                        → dict[str, str]
"""

from __future__ import annotations

import os
import sys
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.domain_manifest import DOMAIN_MANIFEST, SKILL_ONTOLOGY
from ml.preprocessing import normalize_skill_phrase, build_skill_document


# ── Domain corpus ─────────────────────────────────────────────────────────────

def build_domain_corpus() -> dict[str, str]:
    """
    Build a rich text document for each domain by concatenating:
      - required skills (repeated for weight)
      - domain keywords
      - ontology synonyms for each skill

    This means "neural networks" and "deep learning" both map to the AI/ML
    domain document without any hardcoded if/else.
    """
    corpus: dict[str, str] = {}
    for domain, manifest in DOMAIN_MANIFEST.items():
        tokens: list[str] = []

        # Core skills — repeated 3× so they dominate the TF-IDF vector.
        for skill in manifest.get("required_skills", []):
            normalized = normalize_skill_phrase(skill)
            tokens.extend([normalized] * 3)
            # Add ontology synonyms so "pytorch" also activates "deep learning" etc.
            for canonical, synonyms in SKILL_ONTOLOGY.items():
                if normalized == canonical or skill.lower() in [s.lower() for s in synonyms]:
                    tokens.extend([normalize_skill_phrase(s) for s in synonyms])

        # Domain keywords — single occurrence.
        for kw in manifest.get("keywords", []):
            tokens.append(normalize_skill_phrase(kw))

        corpus[domain] = " ".join(t for t in tokens if t)
    return corpus


# ── TF-IDF backend ────────────────────────────────────────────────────────────

class TFIDFSimilarityEngine:
    """
    Fits a TF-IDF vectorizer over the domain corpus and computes cosine
    similarity between a user skill document and each domain.
    """

    def __init__(self) -> None:
        self._vectorizer: TfidfVectorizer | None = None
        self._domain_matrix = None
        self._domains: list[str] = []

    def _ensure_fitted(self) -> None:
        if self._vectorizer is not None:
            return
        corpus = build_domain_corpus()
        self._domains = list(corpus.keys())
        docs = list(corpus.values())

        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,   # log-scale TF dampens very frequent tokens
        )
        self._domain_matrix = self._vectorizer.fit_transform(docs)

    def find_similar_domains(
        self,
        skills: list[str] | dict[str, int],
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Return top-k domains ranked by cosine similarity to the user's skill
        document.  Proficiency weights are respected when skills is a dict.
        """
        self._ensure_fitted()

        user_doc = build_skill_document(skills)
        if not user_doc.strip():
            return []

        user_vec = self._vectorizer.transform([user_doc])
        sims = cosine_similarity(user_vec, self._domain_matrix).flatten()

        ranked_idx = np.argsort(sims)[::-1][:top_k]
        results = []
        for idx in ranked_idx:
            domain = self._domains[idx]
            score  = round(float(sims[idx]) * 100, 2)

            # Surface which user skills drove the similarity (XAI).
            feature_names = np.array(self._vectorizer.get_feature_names_out())
            user_nonzero  = user_vec.nonzero()[1]
            domain_vec    = self._domain_matrix[idx]
            contributions = {
                feature_names[i]: float(user_vec[0, i]) * float(domain_vec[0, i])
                for i in user_nonzero
            }
            top_keywords = sorted(contributions, key=contributions.get, reverse=True)[:5]

            results.append({
                "domain":            domain,
                "similarity_score":  score,
                "matching_keywords": [k for k in top_keywords if contributions[k] > 0],
            })

        return results

    def semantic_skill_match(self, skill: str, domain: str) -> float:
        """
        Return a 0-1 cosine similarity between a single skill token and a
        domain document.  Useful for per-skill XAI explanations.
        """
        self._ensure_fitted()
        if domain not in self._domains:
            return 0.0
        skill_vec  = self._vectorizer.transform([normalize_skill_phrase(skill)])
        domain_idx = self._domains.index(domain)
        sim = cosine_similarity(skill_vec, self._domain_matrix[domain_idx]).flatten()[0]
        return round(float(sim), 4)


# ── Optional SBERT backend ────────────────────────────────────────────────────

class SBERTSimilarityEngine:
    """
    Uses sentence-transformers (all-MiniLM-L6-v2) for richer semantic matching.
    Falls back to TFIDFSimilarityEngine if the library is not installed.
    """

    def __init__(self) -> None:
        self._model = None
        self._domain_embeddings = None
        self._domains: list[str] = []
        self._available = False
        self._tfidf_fallback = TFIDFSimilarityEngine()

    def _ensure_loaded(self) -> bool:
        if self._model is not None:
            return self._available
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            corpus = build_domain_corpus()
            self._domains = list(corpus.keys())
            self._domain_embeddings = self._model.encode(
                list(corpus.values()), convert_to_numpy=True, normalize_embeddings=True
            )
            self._available = True
        except Exception:
            self._available = False
        return self._available

    def find_similar_domains(
        self,
        skills: list[str] | dict[str, int],
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        if not self._ensure_loaded():
            return self._tfidf_fallback.find_similar_domains(skills, top_k)

        user_doc = build_skill_document(skills)
        if not user_doc.strip():
            return []

        user_emb = self._model.encode([user_doc], convert_to_numpy=True, normalize_embeddings=True)
        sims = cosine_similarity(user_emb, self._domain_embeddings).flatten()

        ranked_idx = np.argsort(sims)[::-1][:top_k]
        results = []
        for idx in ranked_idx:
            results.append({
                "domain":            self._domains[idx],
                "similarity_score":  round(float(sims[idx]) * 100, 2),
                # SBERT doesn't expose token-level contributions; surface matched skills instead.
                "matching_keywords": _extract_matching_skills(skills, self._domains[idx]),
            })
        return results

    def semantic_skill_match(self, skill: str, domain: str) -> float:
        if not self._ensure_loaded():
            return self._tfidf_fallback.semantic_skill_match(skill, domain)
        if domain not in self._domains:
            return 0.0
        skill_emb  = self._model.encode([normalize_skill_phrase(skill)], normalize_embeddings=True)
        domain_idx = self._domains.index(domain)
        sim = cosine_similarity(skill_emb, self._domain_embeddings[domain_idx:domain_idx+1]).flatten()[0]
        return round(float(sim), 4)


def _extract_matching_skills(
    skills: list[str] | dict[str, int],
    domain: str,
) -> list[str]:
    """Return skills that appear in the domain's required_skills list."""
    required = {normalize_skill_phrase(s) for s in DOMAIN_MANIFEST.get(domain, {}).get("required_skills", [])}
    skill_list = list(skills.keys()) if isinstance(skills, dict) else skills
    return [s for s in skill_list if normalize_skill_phrase(s) in required][:5]


# ── Singleton — prefer SBERT, fall back to TF-IDF ────────────────────────────

_engine: TFIDFSimilarityEngine | SBERTSimilarityEngine | None = None


def _get_engine() -> TFIDFSimilarityEngine | SBERTSimilarityEngine:
    global _engine
    if _engine is None:
        _engine = SBERTSimilarityEngine()
    return _engine


# ── Public API ────────────────────────────────────────────────────────────────

def find_similar_domains(
    skills: list[str] | dict[str, int],
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    Semantic domain matching.  Understands that "neural networks" and "ml"
    are mathematically similar — no hardcoded mapping required.
    """
    return _get_engine().find_similar_domains(skills, top_k)


def semantic_skill_match(skill: str, domain: str) -> float:
    """Return 0-1 similarity between a skill token and a domain."""
    return _get_engine().semantic_skill_match(skill, domain)


def evaluate_similarity_engine(df: pd.DataFrame) -> dict[str, float]:
    """
    Proxy-evaluate the TF-IDF similarity engine with retrieval accuracy metrics.
    """
    engine = TFIDFSimilarityEngine()
    total = 0
    hits_at_1 = 0
    hits_at_3 = 0
    correct_scores: list[float] = []
    incorrect_scores: list[float] = []

    for _, row in df.iterrows():
        skills_text = str(row.get("skills_text", "")).strip()
        label = str(row.get("domain_label", "")).strip()
        if not skills_text or not label:
            continue

        results = engine.find_similar_domains(skills_text.split(), top_k=3)
        if not results:
            continue

        total += 1
        top_1 = results[0]
        top_domains = [item.get("domain") for item in results]
        top_score = float(top_1.get("similarity_score", 0.0))

        if top_1.get("domain") == label:
            hits_at_1 += 1
            correct_scores.append(top_score)
        else:
            incorrect_scores.append(top_score)

        if label in top_domains:
            hits_at_3 += 1

    return {
        "accuracy_at_1": round((hits_at_1 / total) if total else 0.0, 4),
        "accuracy_at_3": round((hits_at_3 / total) if total else 0.0, 4),
        "mean_sim_correct": round(sum(correct_scores) / len(correct_scores), 4) if correct_scores else 0.0,
        "mean_sim_incorrect": round(sum(incorrect_scores) / len(incorrect_scores), 4) if incorrect_scores else 0.0,
        "n_samples": total,
    }
