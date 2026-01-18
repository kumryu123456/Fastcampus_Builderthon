"""
Cover Letter model for PathPilot.

Constitution Compliance:
- Principle III: User Data Privacy - Linked to user, no PII in logs
- Principle V: Code Quality - Structured data model with JSONB for generation params

T038: Cover Letter SQLAlchemy model
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from src.database import Base


class CoverLetter(Base):
    """Cover Letter model with AI generation results."""

    __tablename__ = "cover_letters"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True)

    # Job information
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_description = Column(Text, nullable=True)  # Optional job posting text

    # Generated content
    content = Column(Text, nullable=True)  # Generated cover letter text

    # Generation parameters (for regeneration/editing)
    # Structure: {
    #   "tone": "professional" | "casual" | "enthusiastic",
    #   "length": "short" | "medium" | "long",
    #   "focus_areas": ["technical skills", "leadership", ...],
    #   "custom_instructions": "user's additional notes",
    #   "resume_summary": "extracted summary from resume",
    #   "model_used": "gemini-2.0-flash",
    #   "generated_at": "ISO timestamp"
    # }
    generation_params = Column(JSONB, nullable=True)

    # Version tracking for edits
    version = Column(Integer, default=1, nullable=False)

    # Status tracking
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )  # pending, generating, generated, failed

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    generated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="cover_letters")
    resume = relationship("Resume", backref="cover_letters")

    def __repr__(self) -> str:
        return f"<CoverLetter(id={self.id}, job={self.job_title}@{self.company_name}, status={self.status})>"

    def is_generated(self) -> bool:
        """Check if cover letter has been generated."""
        return self.status == "generated" and self.content is not None

    def get_word_count(self) -> int:
        """Get word count of generated content."""
        if not self.content:
            return 0
        return len(self.content.split())

    def get_summary(self) -> dict:
        """
        Get summary of cover letter.

        Returns:
            Dictionary with cover letter summary
        """
        return {
            "id": self.id,
            "job_title": self.job_title,
            "company_name": self.company_name,
            "status": self.status,
            "version": self.version,
            "word_count": self.get_word_count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }
