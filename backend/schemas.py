from pydantic import BaseModel, field_validator
from typing import Any, List, Optional


class UserSignup(BaseModel):
    name: str
    email: str
    password: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        value = v.strip()
        if len(value) < 2:
            raise ValueError("Name must be at least 2 characters")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        value = v.strip().lower()
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Enter a valid email")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return v.strip().lower()


class AuthUser(BaseModel):
    user_id: str
    name: str
    email: str


class AuthResponse(BaseModel):
    message: str
    user: AuthUser


class JourneyOverview(BaseModel):
    analyses_count: int
    assessments_count: int
    latest_top_domain: Optional[str] = None
    average_readiness: float
    latest_readiness: float


class JourneySessionItem(BaseModel):
    id: int
    skills_input: List[str]
    top_domain: str
    confidence: float
    created_at: str


class JourneyAssessmentItem(BaseModel):
    id: int
    domain: str
    assessment_score: float
    skill_match: float
    readiness_score: float
    created_at: str


class CompanyPerformanceItem(BaseModel):
    company: str
    level: str
    attempts: int
    best_score: float
    average_score: float
    latest_score: float
    latest_attempt_at: str


class RoadmapStep(BaseModel):
    week: int
    title: str
    objective: str
    skills: List[str]
    checkpoint: str


class LearningRoadmap(BaseModel):
    target_domain: str
    match_percentage: float
    current_strengths: List[str]
    next_skills: List[str]
    summary: str
    weekly_plan: List[RoadmapStep]
    resources: List["ResourceItem"]


class JourneyDashboardResponse(BaseModel):
    user: AuthUser
    overview: JourneyOverview
    recommendation_history: List[JourneySessionItem]
    assessment_history: List[JourneyAssessmentItem]
    company_performance: List[CompanyPerformanceItem]
    roadmap: Optional[LearningRoadmap] = None


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


class CompanyPracticeSubmission(BaseModel):
    company: str
    role: str = "General"
    level: str = "mixed"
    answers: List[Any]
    user_id: Optional[str] = None


class CompanyPracticeQuestion(BaseModel):
    id: str
    question: str
    text: str
    options: List[str]
    company: str
    role: str
    difficulty: str
    topic_tag: str
    question_type: str


class CompanyPracticeEvaluateResponse(BaseModel):
    company: str
    role: str
    level: str
    score: int
    correct_count: int
    total_questions: int
    feedback: str
    difficulty_breakdown: dict


class DemandItem(BaseModel):
    level: str
    percentage: int


class RecommendationItem(BaseModel):
    role: str
    confidence: float
    salary: str
    demand: DemandItem
    reason: List[str]
    top_skills: List[str]  # XAI: top contributing skills
    fit_summary: str
    growth_summary: str
    missing_priority_skills: List[str]
    project_suggestions: List[str]


class GitHubProjectCreate(BaseModel):
    user_id: str
    repo_name: str
    repo_url: str

    @field_validator("repo_url")
    @classmethod
    def validate_url(cls, v):
        if "github.com" not in v.lower():
            raise ValueError("URL must be a valid GitHub link.")
        return v


class GitHubProjectResponse(BaseModel):
    id: int
    user_id: str
    repo_name: str
    repo_url: str
    created_at: str


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
    total_questions: int
    score: int                      # alias kept for backward compat
    feedback: str
    weak_sub_topics: List[WeakSubTopic]   # sub-topics where >40% wrong
    weak_areas: List[str]           # unique sub_topic strings for wrong answers
    readiness: ReadinessScore
    resources: List[ResourceItem]


LearningRoadmap.model_rebuild()
