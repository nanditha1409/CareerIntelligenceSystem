"""
Lightweight SQLite persistence via SQLAlchemy.
Stores user sessions, skill snapshots, and test results.
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


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
