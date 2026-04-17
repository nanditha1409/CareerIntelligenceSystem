"""
Shared ML preprocessing utilities.

This module intentionally stays framework-light so training, inference,
resume parsing, and personalization all normalize skills the same way.
"""

from __future__ import annotations

import random
import re
from typing import Iterable

import pandas as pd

from config.domain_manifest import DOMAIN_MANIFEST, KEYWORD_MAPPING, SKILL_ONTOLOGY


# Addition: reverse lookup lets the ontology collapse synonyms into a canonical token.
ONTOLOGY_LOOKUP: dict[str, str] = {}
for canonical, synonyms in SKILL_ONTOLOGY.items():
    for synonym in synonyms:
        ONTOLOGY_LOOKUP[synonym.lower().strip()] = canonical


def normalize_skill_phrase(skill: str) -> str:
    """Normalize free-form skill text into a compact canonical token."""
    cleaned = re.sub(r"[^a-z0-9+.#\s-]", " ", str(skill).lower()).replace("-", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return ""
    if cleaned in ONTOLOGY_LOOKUP:
        return ONTOLOGY_LOOKUP[cleaned]
    for phrase, domain in KEYWORD_MAPPING.items():
        phrase_clean = phrase.lower().strip()
        if cleaned == phrase_clean:
            return ONTOLOGY_LOOKUP.get(phrase_clean, cleaned)
        if phrase_clean and phrase_clean in cleaned:
            return ONTOLOGY_LOOKUP.get(phrase_clean, cleaned)
    return cleaned


def normalize_skills(skills: Iterable[str]) -> list[str]:
    """Normalize, deduplicate, and preserve stable ordering for skill tokens."""
    seen: set[str] = set()
    normalized: list[str] = []
    for skill in skills:
        token = normalize_skill_phrase(skill)
        if token and token not in seen:
            seen.add(token)
            normalized.append(token)
    return normalized


def build_skill_document(skills: list[str] | dict[str, int]) -> str:
    """
    Convert skills into a text document for TF-IDF.
    Proficiency-weighted inputs repeat tokens so stronger skills influence the vector.
    """
    if isinstance(skills, dict):
        tokens: list[str] = []
        for raw_skill, level in skills.items():
            token = normalize_skill_phrase(raw_skill)
            if not token:
                continue
            repeat = max(1, min(5, int(level)))
            tokens.extend([token] * repeat)
        return " ".join(tokens)
    return " ".join(normalize_skills(skills))


def build_domain_training_frame(samples_per_domain: int = 80, random_state: int = 42) -> pd.DataFrame:
    """
    Generate a synthetic-but-structured corpus for domain classification.
    The goal is stable supervised behavior with enough variation for TF-IDF + linear models.
    """
    rng = random.Random(random_state)
    rows: list[dict[str, str]] = []
    all_domains = list(DOMAIN_MANIFEST.keys())
    all_skills = sorted({skill for manifest in DOMAIN_MANIFEST.values() for skill in manifest["required_skills"]})

    for domain, manifest in DOMAIN_MANIFEST.items():
        required = manifest["required_skills"]
        keywords = manifest.get("keywords", [])
        domain_peers = [name for name in all_domains if name != domain]

        for _ in range(samples_per_domain):
            active_tokens: list[str] = []

            # Addition: most core skills appear often to teach the classifier domain identity.
            for skill in required:
                if rng.random() < 0.82:
                    active_tokens.append(normalize_skill_phrase(skill))

            # Addition: keywords and ontology synonyms give the model realistic free-form language.
            for keyword in keywords:
                if rng.random() < 0.55:
                    active_tokens.append(normalize_skill_phrase(keyword))

            # Addition: controlled noise prevents the classifier from overfitting to perfect inputs.
            for noisy_skill in rng.sample(all_skills, min(4, len(all_skills))):
                if noisy_skill not in required and rng.random() < 0.14:
                    active_tokens.append(normalize_skill_phrase(noisy_skill))

            # Addition: occasional domain-name tokens help resume-style text map correctly.
            if rng.random() < 0.65:
                active_tokens.append(domain.lower())

            # Addition: sparse cross-domain terms make the ML model more robust to mixed profiles.
            if rng.random() < 0.18 and domain_peers:
                peer_manifest = DOMAIN_MANIFEST[rng.choice(domain_peers)]
                peer_skill = rng.choice(peer_manifest["required_skills"])
                active_tokens.append(normalize_skill_phrase(peer_skill))

            rows.append({"text": " ".join(token for token in active_tokens if token), "domain": domain})

    return pd.DataFrame(rows)


def build_difficulty_training_frame(random_state: int = 42) -> pd.DataFrame:
    """
    Create a lightweight supervised dataset for adaptive difficulty.
    Inputs are historical performance aggregates; output is the next recommended difficulty.
    """
    rng = random.Random(random_state)
    rows: list[dict[str, float | str]] = []

    for _ in range(240):
        recent_score = rng.uniform(0, 100)
        avg_score = max(0.0, min(100.0, recent_score + rng.uniform(-18, 18)))
        weak_topic_rate = rng.uniform(0, 1)
        attempts = rng.randint(1, 40)

        if recent_score >= 80 and avg_score >= 72 and weak_topic_rate <= 0.25:
            label = "Hard"
        elif recent_score <= 45 or weak_topic_rate >= 0.55:
            label = "Easy"
        else:
            label = "Medium"

        rows.append(
            {
                "recent_score": recent_score,
                "avg_score": avg_score,
                "weak_topic_rate": weak_topic_rate,
                "attempts": attempts,
                "next_difficulty": label,
            }
        )

    return pd.DataFrame(rows)
