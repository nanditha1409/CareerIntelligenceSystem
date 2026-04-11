from pydantic import BaseModel, field_validator
from typing import Any, List, Optional


class SkillsInput(BaseModel):
    skills: List[str]
    user_id: Optional[str] = None

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v):
        if not v:
            raise ValueError("Skills list cannot be empty")
        if len(v) > 50:
            raise ValueError("Too many skills (max 50)")
        return [s.strip().lower() for s in v if s.strip()]


class TestSubmission(BaseModel):
    domain: str
    # Accepts both legacy List[str] and new List[{"id": str, "answer": str}]
    answers: List[Any]
    skills: Optional[List[str]] = []
    user_id: Optional[str] = None


class RecommendationItem(BaseModel):
    domain: str
    confidence: float
    salary: str
    demand: str
    reason: List[str]
    top_skills: List[str]  # XAI: top contributing skills


class SkillGapItem(BaseModel):
    domain: str
    missing_skills: List[str]
    matched_skills: List[str]
    match_percentage: float


class ResourceItem(BaseModel):
    skill: str
    title: str
    url: str
    type: str  # "video" | "article" | "course"


class ReadinessScore(BaseModel):
    domain: str
    skill_match: float              # 0-100
    assessment_performance: float   # 0-100  (quiz score)
    readiness_score: float          # weighted composite
    label: str                      # "Job Ready" | "Developing" | "Beginner"


class WeakSubTopic(BaseModel):
    sub_topic: str
    wrong: int
    total: int


class RecommendResponse(BaseModel):
    recommendations: List[RecommendationItem]
    skill_gap: List[SkillGapItem]
    resources: List[ResourceItem]


class EvaluateResponse(BaseModel):
    quiz_score: int                 # raw % correct/total
    correct_count: int              # number of correct answers (e.g. 8 out of 10)
    score: int                      # alias kept for backward compat
    feedback: str
    weak_sub_topics: List[WeakSubTopic]   # sub-topics where >40% wrong
    weak_areas: List[str]           # unique sub_topic strings for wrong answers
    readiness: ReadinessScore
    resources: List[ResourceItem]
