from pydantic import BaseModel, field_validator
from typing import Any, Dict, List, Optional


class ProjectInput(BaseModel):
    title: str = ""
    summary: str = ""


class SkillsInput(BaseModel):
    # Accepts either legacy List[str] or new Dict[str, int] (skill → proficiency 1-5)
    skills: Any
    preferred_domain: Optional[str] = None
    experience_level: Optional[str] = None
    projects: List[ProjectInput] = []
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

    @field_validator("experience_level")
    @classmethod
    def validate_experience_level(cls, v):
        if v is None:
            return v
        allowed = {"no_experience", "intern", "intermediate", "advance"}
        cleaned = v.strip().lower()
        if cleaned not in allowed:
            raise ValueError("experience_level must be one of no_experience, intern, intermediate, advance")
        return cleaned

    def skills_as_list(self) -> List[str]:
        if isinstance(self.skills, dict):
            return list(self.skills.keys())
        return self.skills

    def skills_as_dict(self) -> Dict[str, int]:
        if isinstance(self.skills, dict):
            return self.skills
        return {s: 3 for s in self.skills}  # default proficiency 3 for legacy list

    def project_text(self) -> str:
        parts: List[str] = []
        for project in self.projects:
            parts.extend([project.title, project.summary])
        return " ".join(part for part in parts if part).strip()


class TestSubmission(BaseModel):
    domain: str
    answers: Any
    assessment_level: Optional[str] = "easy"
    programming_language: Optional[str] = None
    # Accepts legacy List[str] or new Dict[str, int]
    skills: Optional[Any] = None
    user_id: Optional[str] = None

    @field_validator("assessment_level")
    @classmethod
    def validate_assessment_level(cls, v):
        if v is None:
            return "easy"
        cleaned = v.strip().lower()
        if cleaned not in {"easy", "medium"}:
            raise ValueError("assessment_level must be easy or medium")
        return cleaned

    @field_validator("programming_language")
    @classmethod
    def validate_programming_language(cls, v):
        if v is None:
            return v
        cleaned = v.strip().lower()
        if cleaned not in {"python", "java"}:
            raise ValueError("programming_language must be python or java")
        return cleaned

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
    compatibility_score: Optional[float] = None
    unified_score: Optional[float] = None
    salary: str
    demand: str
    reason: List[str]
    top_skills: List[str]
    # Task 1 & 4: ML classifier confidence and XAI feature contributions
    confidence_score: Optional[float] = None       # 0-100 from skill_classifier
    matching_keywords: Optional[List[str]] = None  # top skills that drove the prediction
    feature_importance: Optional[List[dict]] = None  # [{skill, importance}] for XAI panel


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


class ChallengeResult(BaseModel):
    question_id: str
    sub_topic: str
    language: str
    passed: bool
    passed_tests: int
    total_tests: int
    error_message: Optional[str] = None


class RecommendResponse(BaseModel):
    recommendations: List[RecommendationItem]
    skill_gap: List[SkillGapItem]
    resources: List[ResourceItem]


class EvaluateResponse(BaseModel):
    quiz_score: int
    correct_count: int
    score: int
    total_questions: Optional[int] = None
    assessment_level: Optional[str] = "easy"
    feedback: str
    weak_sub_topics: List[WeakSubTopic]
    weak_areas: List[str]
    readiness: ReadinessScore
    resources: List[ResourceItem]
    programming_language: Optional[str] = None
    execution_results: Optional[List[ChallengeResult]] = None


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


# Task 2: NLP resume upload response — extends the base with experience + semantic matches
class ResumeUploadResponse(BaseModel):
    extracted_text_preview: str
    skills: List[str]
    years_of_experience: Optional[int] = None
    recommendations: List[RecommendationItem]
    semantic_matches: Optional[List[dict]] = None  # from similarity.py
