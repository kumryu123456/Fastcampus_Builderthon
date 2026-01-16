"""
Resume model for PathPilot.

Constitution Compliance:
- Principle III: User Data Privacy - Secure file storage with UUID filenames
- Principle V: Code Quality - Structured data model with JSONB for analysis results

T022: Resume SQLAlchemy model with analysis_result JSONB field
"""

import hashlib
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from src.database import Base


class Resume(Base):
    """Resume model with AI analysis results."""

    __tablename__ = "resumes"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # File metadata
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, unique=True)
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=False)  # application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for deduplication (T026)

    # Extracted content
    extracted_text = Column(Text, nullable=True)  # Resume text content

    # AI Analysis results (T022: JSONB for structured analysis)
    # Structure: {
    #   "strengths": ["..."],
    #   "weaknesses": ["..."],
    #   "recommendations": ["..."],
    #   "suitable_roles": ["..."],
    #   "skills": ["..."],
    #   "experience_years": int,
    #   "analyzed_at": "ISO timestamp",
    #   "model_used": "gemini-1.5-pro"
    # }
    analysis_result = Column(JSONB, nullable=True)

    # Status tracking
    status = Column(
        String(50),
        nullable=False,
        default="uploaded",
        index=True,
    )  # uploaded, processing, analyzed, failed

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    analyzed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="resumes")

    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, filename={self.original_filename}, status={self.status})>"

    @staticmethod
    def compute_file_hash(file_content: bytes) -> str:
        """
        Compute SHA-256 hash of file content for deduplication (T026).

        Args:
            file_content: File bytes

        Returns:
            SHA-256 hex digest
        """
        return hashlib.sha256(file_content).hexdigest()

    def is_analyzed(self) -> bool:
        """Check if resume has been analyzed."""
        return self.status == "analyzed" and self.analysis_result is not None

    def get_analysis_summary(self) -> dict:
        """
        Get summary of analysis results.

        Returns:
            Dictionary with analysis summary
        """
        if not self.analysis_result:
            return {}

        return {
            "strengths_count": len(self.analysis_result.get("strengths", [])),
            "weaknesses_count": len(self.analysis_result.get("weaknesses", [])),
            "recommendations_count": len(self.analysis_result.get("recommendations", [])),
            "suitable_roles": self.analysis_result.get("suitable_roles", []),
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }
