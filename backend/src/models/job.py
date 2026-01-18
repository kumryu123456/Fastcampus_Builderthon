"""
Job model for PathPilot.

Constitution Compliance:
- Principle III: User Data Privacy - Job data linked to user
- Principle V: Code Quality - Structured data model

T053: Job SQLAlchemy model for job discovery and recommendations
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from src.database import Base


class Job(Base):
    """Job listing model for discovery and matching."""

    __tablename__ = "jobs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to user (who saved/searched this job)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Job details
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    job_type = Column(String(50), nullable=True)  # full-time, part-time, contract, internship
    experience_level = Column(String(50), nullable=True)  # entry, mid, senior, executive

    # Job description and requirements
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    salary_range = Column(String(100), nullable=True)

    # Application details
    url = Column(String(1000), nullable=True)
    application_deadline = Column(DateTime(timezone=True), nullable=True)

    # AI matching results
    # Structure: {
    #   "match_score": float (0-100),
    #   "matching_skills": ["skill1", "skill2"],
    #   "missing_skills": ["skill3"],
    #   "strengths_match": ["strength1"],
    #   "recommendation_reason": "...",
    #   "resume_id": int,
    #   "analyzed_at": timestamp,
    #   "model_used": "gemini-2.0-flash"
    # }
    match_analysis = Column(JSONB, nullable=True)

    # Match score for quick sorting (0-100)
    match_score = Column(Float, nullable=True, index=True)

    # User interaction
    is_saved = Column(Boolean, default=False, index=True)
    is_applied = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    # Source tracking
    source = Column(String(100), nullable=True)  # manual, ai_recommended, search

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="jobs")

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title={self.title}@{self.company}, score={self.match_score})>"

    def get_summary(self) -> dict:
        """Get job summary for list view."""
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "job_type": self.job_type,
            "experience_level": self.experience_level,
            "match_score": self.match_score,
            "is_saved": self.is_saved,
            "is_applied": self.is_applied,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_matching_skills(self) -> list:
        """Get skills that match between job and resume."""
        if not self.match_analysis:
            return []
        return self.match_analysis.get("matching_skills", [])

    def get_missing_skills(self) -> list:
        """Get skills required by job but not in resume."""
        if not self.match_analysis:
            return []
        return self.match_analysis.get("missing_skills", [])
