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


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserPublic(BaseModel):
    id: int
    email: str
    full_name: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


# Optional request model for intelligence endpoint.
class CareerIntelligenceRequest(BaseModel):
    skills: Any
    top_domains: Optional[List[str]] = None
    domain: Optional[str] = None
    company: Optional[str] = None
    question_count: Optional[int] = 10
    user_id: Optional[str] = None
    weak_topics: Optional[List[str]] = None

    @field_validator("skills")
    @classmethod
    def validate_skills_payload(cls, v):
        # Keep compatibility with both historical list input and dict input.
        if isinstance(v, list):
            return [s.strip().lower() for s in v if isinstance(s, str) and s.strip()]
        if isinstance(v, dict):
            cleaned = {}
            for k, value in v.items():
                if isinstance(k, str) and k.strip():
                    cleaned[k.strip().lower()] = max(1, min(5, int(value)))
            return cleaned
        raise ValueError("skills must be a list or dict")

    def skills_as_list(self) -> List[str]:
        if isinstance(self.skills, dict):
            return list(self.skills.keys())
        return self.skills

    def skills_as_dict(self) -> Dict[str, int]:
        if isinstance(self.skills, dict):
            return self.skills
        return {s: 3 for s in self.skills}


# Addition: lightweight response models for additive ML endpoints.
class AnalyticsTopicItem(BaseModel):
    topic: str
    accuracy: float
    attempts: int


class AnalyticsResponse(BaseModel):
    topic_accuracy: List[AnalyticsTopicItem]
    timeline: List[Dict[str, Any]]
    strengths: List[str]
    weaknesses: List[str]


class ResumeAnalysisResponse(BaseModel):
    extracted_text_preview: str
    skills: List[str]
    recommendations: List[RecommendationItem]
