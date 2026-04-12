from pydantic import BaseModel, field_validator
from typing import Any, Dict, List, Optional


class SkillsInput(BaseModel):
    # Accepts either legacy List[str] or new Dict[str, int] (skill → proficiency 1-5)
    skills: Any
    user_id: Optional[str] = None

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v):
        if isinstance(v, dict):
            if not v:
                raise ValueError("Skills dict cannot be empty")
            # Clamp proficiency values to 1-5
            return {k.strip().lower(): max(1, min(5, int(val))) for k, val in v.items() if k.strip()}
        if isinstance(v, list):
            if not v:
                raise ValueError("Skills list cannot be empty")
            if len(v) > 50:
                raise ValueError("Too many skills (max 50)")
            return [s.strip().lower() for s in v if s.strip()]
        raise ValueError("skills must be a list or dict")

    def skills_as_list(self) -> List[str]:
        if isinstance(self.skills, dict):
            return list(self.skills.keys())
        return self.skills

    def skills_as_dict(self) -> Dict[str, int]:
        if isinstance(self.skills, dict):
            return self.skills
        return {s: 3 for s in self.skills}  # default proficiency 3 for legacy list


class TestSubmission(BaseModel):
    domain: str
    answers: List[Any]
    # Accepts legacy List[str] or new Dict[str, int]
    skills: Optional[Any] = None
    user_id: Optional[str] = None

    def skills_as_dict(self) -> Dict[str, int]:
        if isinstance(self.skills, dict):
            return {k.strip().lower(): max(1, min(5, int(v))) for k, v in self.skills.items()}
        if isinstance(self.skills, list):
            return {s.strip().lower(): 3 for s in self.skills if s.strip()}
        return {}

    def skills_as_list(self) -> List[str]:
        return list(self.skills_as_dict().keys())


class ChatRequest(BaseModel):
    domain: str
    quiz_score: int
    readiness_score: float
    weak_areas: List[str]
    message: str


class RecommendationItem(BaseModel):
    domain: str
    confidence: float
    salary: str
    demand: str
    reason: List[str]
    top_skills: List[str]


class SkillGapItem(BaseModel):
    domain: str
    missing_skills: List[str]
    matched_skills: List[str]
    match_percentage: float


class ResourceItem(BaseModel):
    skill: str
    title: str
    url: str
    type: str


class ReadinessScore(BaseModel):
    domain: str
    skill_match: float
    assessment_performance: float
    readiness_score: float
    label: str


class WeakSubTopic(BaseModel):
    sub_topic: str
    wrong: int
    total: int


class RecommendResponse(BaseModel):
    recommendations: List[RecommendationItem]
    skill_gap: List[SkillGapItem]
    resources: List[ResourceItem]


class EvaluateResponse(BaseModel):
    quiz_score: int
    correct_count: int
    score: int
    feedback: str
    weak_sub_topics: List[WeakSubTopic]
    weak_areas: List[str]
    readiness: ReadinessScore
    resources: List[ResourceItem]
