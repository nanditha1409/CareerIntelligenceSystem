"""
Lightweight SQLite persistence via SQLAlchemy.
Stores user sessions, skill snapshots, and test results.
No external DB required — file is created automatically.
"""
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "career_intelligence.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=True)
    skills_input = Column(Text)           # comma-separated
    top_domain = Column(String)
    confidence = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=True)
    domain = Column(String)
    assessment_score = Column(Float)      # 0-100
    skill_match = Column(Float)           # 0-100
    readiness_score = Column(Float)       # weighted composite
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# New optional table for storing richer profile-level intelligence snapshots.
# This extends schema safely without changing existing tables/endpoints.
class UserCareerProfile(Base):
    __tablename__ = "user_career_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    target_domain = Column(String, index=True, nullable=False)
    strengths = Column(Text, default="")
    growth_areas = Column(Text, default="")
    next_steps = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


# New optional table for recommendation export/history use-cases.
# This keeps old persistence intact and enables future reporting dashboards.
class RecommendationSnapshot(Base):
    __tablename__ = "recommendation_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    top_domain = Column(String, index=True, nullable=False)
    confidence = Column(Float, nullable=False)
    raw_skills = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


# Addition: fine-grained performance history powers adaptive difficulty,
# personalization, and analytics without changing existing assessment tables.
class PerformanceEvent(Base):
    __tablename__ = "performance_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=True)
    domain = Column(String, index=True, nullable=False)
    question_id = Column(String, index=True, nullable=False)
    topic_tag = Column(String, index=True, default="general")
    difficulty = Column(String, index=True, default="Medium")
    is_correct = Column(Integer, default=0)
    score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


# Addition: resume-analysis snapshots keep parsed text and extracted skills auditable.
class ResumeSnapshot(Base):
    __tablename__ = "resume_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=True)
    filename = Column(String, nullable=False)
    extracted_text = Column(Text, default="")
    extracted_skills = Column(Text, default="")
    top_domain = Column(String, index=True, nullable=True)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
