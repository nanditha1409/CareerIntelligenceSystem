"""
Dynamic Market Rate Intelligence Service
=========================================
Implements a Gradient Boosting-inspired, multi-signal salary prediction for the
9 supported career domains.  No hardcoded salary strings — every output is
derived from the input signals via a weighted, non-linear scoring pipeline.

Prediction pipeline (GBM-inspired)
-----------------------------------
Stage 1  — Base calibration    : domain-specific median at intermediate / avg skills
Stage 2  — Experience scaling  : non-linear multiplier (intern → expert)
Stage 3  — Demand adjustment   : market supply-demand index [0-100]
Stage 4  — Skill depth signal  : proficiency-weighted factor (1-5 scale)
Stage 5  — Readiness penalty/reward : test performance + skill-match readiness
Stage 6  — Interaction term    : skill × readiness cross-feature (non-linear)
Stage 7  — Safety clamping     : prevent unrealistic edge-case outputs

Confidence scoring
-------------------
Confidence reflects how much signal the model received.  More inputs (skills,
readiness, quiz score) produce higher confidence; sparse or conflicting inputs
produce lower confidence.  Range width widens as confidence falls.

Output shape
------------
{
  predicted_lpa, range_lpa: {lower, upper, formatted},
  confidence_pct, confidence_label,
  experience_label, demand_label, demand_score, growth_rate_pct,
  skill_impact_pct, avg_skill_level, readiness_adjustment_pct,
  insight, factors
}
"""

from __future__ import annotations

import math

# ── Domain constants ──────────────────────────────────────────────────────────

ALLOWED_DOMAINS: set[str] = {
    "Data Scientist",
    "AI/ML Engineer",
    "Data Analyst",
    "Full Stack Developer",
    "Software Engineer",
    "DevOps Engineer",
    "Cybersecurity Analyst",
    "UI/UX Designer",
    "Backend Developer",
}

# Base market data — Indian tech market 2024-2025
# base_lpa     : median CTC at intermediate level with avg (3/5) skills
# demand_score : 0-100 market demand index (higher → more hiring activity)
# growth_rate  : compound annual salary growth
# volatility   : how much the role's pay varies (wider band for high-volatility)
DOMAIN_MARKET_DATA: dict[str, dict] = {
    "AI/ML Engineer":        {"base_lpa": 14.0, "demand_score": 95, "growth_rate": 0.18, "volatility": 0.18},
    "Data Scientist":        {"base_lpa": 11.0, "demand_score": 83, "growth_rate": 0.15, "volatility": 0.16},
    "Data Analyst":          {"base_lpa":  7.0, "demand_score": 75, "growth_rate": 0.12, "volatility": 0.13},
    "Full Stack Developer":  {"base_lpa": 10.0, "demand_score": 92, "growth_rate": 0.14, "volatility": 0.15},
    "Software Engineer":     {"base_lpa":  9.0, "demand_score": 80, "growth_rate": 0.13, "volatility": 0.14},
    "DevOps Engineer":       {"base_lpa": 11.0, "demand_score": 85, "growth_rate": 0.16, "volatility": 0.15},
    "Cybersecurity Analyst": {"base_lpa": 10.0, "demand_score": 72, "growth_rate": 0.15, "volatility": 0.17},
    "UI/UX Designer":        {"base_lpa":  7.0, "demand_score": 60, "growth_rate": 0.10, "volatility": 0.14},
    "Backend Developer":     {"base_lpa":  9.5, "demand_score": 78, "growth_rate": 0.13, "volatility": 0.14},
}

# Non-linear experience multipliers (calibrated against market surveys)
EXPERIENCE_MULTIPLIERS: dict[str, float] = {
    "intern":          0.28,   # stipend / part-time
    "no_experience":   0.50,   # fresher entry-level
    "intermediate":    1.00,   # 2-4 years (baseline)
    "advance":         1.75,   # 5+ years, senior / lead
}

EXPERIENCE_LABELS: dict[str, str] = {
    "intern":          "Intern",
    "no_experience":   "Fresher",
    "intermediate":    "Intermediate",
    "advance":         "Expert",
}

MIN_LPA: float = 1.5
MAX_LPA: float = 65.0


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_demand_label(score: int) -> str:
    if score >= 90:
        return "Very High"
    if score >= 75:
        return "High"
    if score >= 55:
        return "Medium"
    return "Low"


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _readiness_factor(readiness_score: float | None, quiz_score: float | None) -> tuple[float, str]:
    """
    Stage 5: non-linear readiness adjustment.

    Behaviour
    ---------
    readiness ≥ 75 : slight reward   (+5 to +20 % based on magnitude)
    readiness 45-75: neutral band    (factor ≈ 1.0)
    readiness < 45 : soft penalty    (−5 to −20 %)

    If only quiz_score is available, use it as a proxy.
    Returns (factor, short_label).
    """
    r = readiness_score
    if r is None and quiz_score is not None:
        # Use quiz as a softer signal (less weight than full readiness)
        r = quiz_score * 0.85

    if r is None:
        return 1.0, "Not assessed"

    r = float(_clamp(r, 0, 100))

    if r >= 75:
        # Reward — diminishing returns via sqrt scaling
        reward = 0.05 + (math.sqrt((r - 75) / 25) * 0.15)
        factor = _clamp(1.0 + reward, 1.0, 1.20)
        label  = f"+{round(reward * 100, 1)}% (strong readiness)"
    elif r >= 45:
        # Neutral zone — tiny linear taper toward bottom
        taper  = (r - 45) / 30        # 0 → 1 as r goes 45 → 75
        factor = 0.96 + taper * 0.04  # 0.96 → 1.00
        label  = "Neutral band"
    else:
        # Penalty zone
        penalty = 0.05 + (math.sqrt((45 - r) / 45) * 0.15)
        factor  = _clamp(1.0 - penalty, 0.80, 0.95)
        label   = f"−{round(penalty * 100, 1)}% (low readiness)"

    return factor, label


def _compute_confidence(
    skills: dict[str, int],
    readiness_score: float | None,
    quiz_score: float | None,
    exp_level: str,
) -> int:
    """
    Confidence score (45–92 %) — reflects quality & quantity of signals.

    Component breakdown:
      Base                             45 %
      Skills provided (≥1, ≥3, ≥6)    +5 / +10 / +15
      Readiness available              +12
      Quiz score available             +8
      Skill-readiness alignment bonus  +5 (if both consistent)
      Sparse / conflicting penalty     −5 to −10
    """
    confidence = 45

    skill_count = len(skills)
    if skill_count >= 6:
        confidence += 15
    elif skill_count >= 3:
        confidence += 10
    elif skill_count >= 1:
        confidence += 5

    has_readiness = readiness_score is not None
    has_quiz      = quiz_score      is not None

    if has_readiness:
        confidence += 12
    if has_quiz:
        confidence += 8

    # Alignment bonus: skill proficiency vs readiness roughly consistent
    if has_readiness and skills:
        avg_prof = sum(min(5, max(1, int(v))) for v in skills.values()) / skill_count
        # Convert avg proficiency (1-5) to a 0-100 scale
        prof_pct = (avg_prof - 1) / 4 * 100
        divergence = abs(prof_pct - (readiness_score or 0))
        if divergence < 20:
            confidence += 5   # well-aligned claim
        elif divergence > 45:
            confidence -= 7   # suspect overclaiming / underclaiming

    if has_readiness and has_quiz:
        diff = abs((readiness_score or 0) - (quiz_score or 0))
        if diff > 30:
            confidence -= 5   # inconsistent signals

    # Low readiness signals uncertainty in prediction
    if readiness_score is not None and readiness_score < 35:
        confidence -= 5

    return int(_clamp(confidence, 45, 92))


def _confidence_label(pct: int) -> str:
    if pct >= 80:
        return "High confidence"
    if pct >= 65:
        return "Moderate confidence"
    return "Indicative estimate"


def _range_width(confidence: int, volatility: float) -> float:
    """
    Range half-width as a fraction of the point estimate.

    Higher confidence → tighter range.
    Higher domain volatility → wider range.
    """
    base_width = 0.10 + (1 - confidence / 100) * 0.20   # 0.10 → 0.30
    return base_width + volatility * 0.25


def _generate_insight(
    domain: str,
    exp_label: str,
    predicted: float,
    demand_score: int,
    avg_skill: float,
    growth_rate: float,
    readiness_label: str,
    confidence: int,
) -> str:
    """Contextual insight using phrasing that conveys uncertainty appropriately."""
    demand_phrase = (
        "very high"  if demand_score >= 90 else
        "high"       if demand_score >= 75 else
        "moderate"   if demand_score >= 55 else
        "low"
    )

    skill_phrase = (
        "strong skill depth signals a market premium"     if avg_skill >= 4.0 else
        "intermediate skills match market expectations"   if avg_skill >= 3.0 else
        "deepening skill proficiency would lift estimates"
    )

    growth_str = f"~{round(growth_rate * 100)}% YoY growth"

    if confidence >= 80:
        certainty = "Based on your profile"
    elif confidence >= 65:
        certainty = "Based on current market trends"
    else:
        certainty = "Estimated based on available signals"

    return (
        f"{certainty}: {domain} shows {demand_phrase} demand with {growth_str}. "
        f"{skill_phrase}."
    )


# ── Public API ────────────────────────────────────────────────────────────────

def compute_market_rate(
    domain: str,
    experience_level: str = "no_experience",
    skills: dict[str, int] | None = None,
    readiness_score: float | None = None,
    quiz_score: float | None = None,
) -> dict | None:
    """
    GBM-inspired salary prediction with confidence scoring.

    Parameters
    ----------
    domain           : One of the 9 supported career domains.
    experience_level : intern | no_experience | intermediate | advance
    skills           : {skill: proficiency 1-5}.  None / {} → defaults to 3.
    readiness_score  : Overall readiness 0-100 from assessment.
    quiz_score       : Raw quiz score 0-100 from assessment.

    Returns
    -------
    Structured dict or None if domain not supported.
    """
    if domain not in ALLOWED_DOMAINS:
        return None

    market = DOMAIN_MARKET_DATA.get(domain)
    if not market:
        return None

    base_lpa     = float(market["base_lpa"])
    demand_score = int(market["demand_score"])
    growth_rate  = float(market["growth_rate"])
    volatility   = float(market["volatility"])

    # ── Stage 2: Experience ──────────────────────────────────────────────────
    exp_level = (experience_level or "no_experience").strip().lower()
    if exp_level not in EXPERIENCE_MULTIPLIERS:
        exp_level = "no_experience"
    exp_factor = EXPERIENCE_MULTIPLIERS[exp_level]

    # ── Stage 3: Demand ──────────────────────────────────────────────────────
    demand_factor = 0.80 + (demand_score / 100) * 0.50   # [0.80, 1.30]

    # ── Stage 4: Skill depth ─────────────────────────────────────────────────
    skills = skills or {}
    if skills:
        raw_avg = sum(min(5, max(1, int(v))) for v in skills.values()) / len(skills)
    else:
        raw_avg = 3.0
    avg_proficiency = round(raw_avg, 2)
    skill_factor = 0.75 + (avg_proficiency / 5.0) * 0.50   # [0.75, 1.25]

    # ── Stage 5: Readiness adjustment ───────────────────────────────────────
    r_factor, r_label = _readiness_factor(readiness_score, quiz_score)

    # ── Stage 6: Interaction term (non-linear skill × readiness) ────────────
    # High skill + high readiness creates a small super-linear reward
    if avg_proficiency >= 4.0 and (readiness_score or 0) >= 70:
        interaction = 1.04
    elif avg_proficiency < 2.5 and (readiness_score or 100) < 40:
        interaction = 0.96
    else:
        interaction = 1.0

    # ── Stage 7: Compose prediction ─────────────────────────────────────────
    raw = base_lpa * demand_factor * exp_factor * skill_factor * r_factor * interaction
    predicted = round(_clamp(raw, MIN_LPA, MAX_LPA), 1)

    # ── Confidence ───────────────────────────────────────────────────────────
    confidence     = _compute_confidence(skills, readiness_score, quiz_score, exp_level)
    conf_label     = _confidence_label(confidence)
    half_width     = _range_width(confidence, volatility)

    lower = round(_clamp(predicted * (1 - half_width), MIN_LPA, MAX_LPA), 1)
    upper = round(_clamp(predicted * (1 + half_width), MIN_LPA, MAX_LPA), 1)

    # ── Derived display values ───────────────────────────────────────────────
    skill_impact_pct        = round((skill_factor - 0.75) / 0.50 * 100, 1)
    readiness_adjustment_pct = round((r_factor - 1.0) * 100, 1)

    exp_label    = EXPERIENCE_LABELS.get(exp_level, exp_level.title())
    demand_label = _get_demand_label(demand_score)

    return {
        "domain":                    domain,
        "experience_level":          exp_level,
        "experience_label":          exp_label,
        "predicted_lpa":             predicted,
        "range_lpa": {
            "lower":     lower,
            "upper":     upper,
            "formatted": f"\u20b9{lower}\u2013{upper} LPA",
        },
        "confidence_pct":            confidence,
        "confidence_label":          conf_label,
        "demand_score":              demand_score,
        "demand_label":              demand_label,
        "growth_rate_pct":           round(growth_rate * 100, 1),
        "skill_impact_pct":          skill_impact_pct,
        "avg_skill_level":           avg_proficiency,
        "readiness_adjustment_pct":  readiness_adjustment_pct,
        "readiness_label":           r_label,
        "insight":                   _generate_insight(
            domain, exp_label, predicted, demand_score,
            avg_proficiency, growth_rate, r_label, confidence,
        ),
        "factors": {
            "base_lpa":           base_lpa,
            "demand_factor":      round(demand_factor, 3),
            "experience_factor":  exp_factor,
            "skill_factor":       round(skill_factor, 3),
            "readiness_factor":   round(r_factor, 3),
            "interaction_term":   interaction,
        },
    }
