"""
Interview model for PathPilot Mock Interview feature.

Constitution Compliance:
- Principle III: User Data Privacy - Linked to user, no PII in logs
- Principle V: Code Quality - Structured data model with JSONB for questions/answers

T068: Interview SQLAlchemy model
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from src.database import Base


class Interview(Base):
    """Interview session model with questions and evaluations."""

    __tablename__ = "interviews"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)

    # Job context (can be provided directly without saved job)
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)
    job_description = Column(Text, nullable=True)

    # Interview configuration
    # Structure: {
    #   "interview_type": "behavioral" | "technical" | "mixed",
    #   "difficulty": "entry" | "mid" | "senior",
    #   "question_count": 5,
    #   "focus_areas": ["problem solving", "teamwork", ...],
    #   "language": "ko" | "en"
    # }
    config = Column(JSONB, nullable=True, default={})

    # Generated questions
    # Structure: [
    #   {
    #     "id": 1,
    #     "question": "...",
    #     "type": "behavioral" | "technical" | "situational",
    #     "difficulty": 1-5,
    #     "expected_topics": ["leadership", "problem-solving"],
    #     "time_limit_seconds": 120
    #   }, ...
    # ]
    questions = Column(JSONB, nullable=True, default=[])

    # User answers and evaluations
    # Structure: [
    #   {
    #     "question_id": 1,
    #     "answer_text": "...",
    #     "answer_audio_url": "...",  # Optional audio recording
    #     "answered_at": "ISO timestamp",
    #     "duration_seconds": 90,
    #     "evaluation": {
    #       "score": 85,
    #       "strengths": ["clear structure", ...],
    #       "improvements": ["add specific examples", ...],
    #       "feedback": "detailed feedback...",
    #       "model_answer": "ideal answer example..."
    #     }
    #   }, ...
    # ]
    answers = Column(JSONB, nullable=True, default=[])

    # Overall session stats
    total_score = Column(Float, nullable=True)  # Average of all answer scores
    completed_questions = Column(Integer, default=0)

    # Status tracking
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )  # pending, generating, ready, in_progress, completed, failed

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)  # When user started answering
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="interviews")
    resume = relationship("Resume", backref="interviews")
    job = relationship("Job", backref="interviews")

    def __repr__(self) -> str:
        return f"<Interview(id={self.id}, job={self.job_title}, status={self.status})>"

    def is_ready(self) -> bool:
        """Check if interview questions are ready."""
        return self.status == "ready" and self.questions

    def is_completed(self) -> bool:
        """Check if interview is completed."""
        return self.status == "completed"

    def get_question_count(self) -> int:
        """Get total number of questions."""
        return len(self.questions) if self.questions else 0

    def get_unanswered_questions(self) -> list:
        """Get questions that haven't been answered yet."""
        if not self.questions:
            return []
        answered_ids = {a.get("question_id") for a in (self.answers or [])}
        return [q for q in self.questions if q.get("id") not in answered_ids]

    def get_progress(self) -> dict:
        """Get interview progress."""
        total = self.get_question_count()
        answered = len(self.answers) if self.answers else 0
        return {
            "total_questions": total,
            "answered": answered,
            "remaining": total - answered,
            "progress_percent": round((answered / total * 100) if total > 0 else 0, 1),
        }

    def calculate_total_score(self) -> float:
        """Calculate average score from all evaluations."""
        if not self.answers:
            return 0.0
        scores = [
            a.get("evaluation", {}).get("score", 0)
            for a in self.answers
            if a.get("evaluation")
        ]
        return round(sum(scores) / len(scores), 1) if scores else 0.0

    def get_summary(self) -> dict:
        """Get summary of interview session."""
        progress = self.get_progress()
        return {
            "id": self.id,
            "job_title": self.job_title,
            "company_name": self.company_name,
            "status": self.status,
            "question_count": progress["total_questions"],
            "answered_count": progress["answered"],
            "progress_percent": progress["progress_percent"],
            "total_score": self.total_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
