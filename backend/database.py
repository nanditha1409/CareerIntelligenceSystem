"""
Lightweight SQLite persistence via SQLAlchemy.
Stores users, user sessions, skill snapshots, and test results.
No external DB required — file is created automatically.
"""
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "career_intelligence.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=True)
    skills_input = Column(Text)           # comma-separated
    top_domain = Column(String)
    confidence = Column(Float)
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


class CompanyPracticeResult(Base):
    __tablename__ = "company_practice_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=True)
    company = Column(String, index=True)
    role = Column(String)
    level = Column(String, index=True)
    score = Column(Float)                  # 0-100
    correct_count = Column(Integer)
    total_questions = Column(Integer)
    difficulty_breakdown = Column(Text)    # JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class GitHubProject(Base):
    __tablename__ = "github_projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    repo_name = Column(String, nullable=False)
    repo_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
