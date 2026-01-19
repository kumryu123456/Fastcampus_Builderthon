"""
Application model for PathPilot.

Tracks job applications with status, dates, and linked documents.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
import enum

from src.database import Base


class ApplicationStatus(str, enum.Enum):
    """Application status enum."""
    SAVED = "saved"           # Saved for later
    APPLIED = "applied"       # Application submitted
    SCREENING = "screening"   # Under review
    INTERVIEW = "interview"   # Interview scheduled/in progress
    OFFER = "offer"          # Received offer
    ACCEPTED = "accepted"    # Accepted offer
    REJECTED = "rejected"    # Rejected
    WITHDRAWN = "withdrawn"  # Withdrawn by candidate


class Application(Base):
    """
    Application model - tracks job applications.

    Links Resume, CoverLetter, and Job together for tracking.
    """
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Company and position info
    company_name = Column(String(255), nullable=False)
    position = Column(String(255), nullable=False)
    job_url = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)
    salary_range = Column(String(100), nullable=True)

    # Status tracking
    status = Column(
        Enum(ApplicationStatus),
        default=ApplicationStatus.SAVED,
        nullable=False,
        index=True
    )

    # Linked documents (optional)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    cover_letter_id = Column(Integer, ForeignKey("cover_letters.id"), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)

    # Important dates
    applied_at = Column(DateTime, nullable=True)
    interview_at = Column(DateTime, nullable=True)
    offer_at = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)

    # Notes and details
    notes = Column(Text, nullable=True)
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)

    # Activity log (JSON array of events)
    activity_log = Column(JSONB, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="applications")
    resume = relationship("Resume", backref="applications")
    cover_letter = relationship("CoverLetter", backref="applications")
    job = relationship("Job", backref="applications")

    def add_activity(self, action: str, details: Optional[str] = None):
        """Add an activity log entry."""
        if self.activity_log is None:
            self.activity_log = []

        entry = {
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        }
        self.activity_log = self.activity_log + [entry]

    def update_status(self, new_status: ApplicationStatus, notes: Optional[str] = None):
        """Update status and log the change."""
        old_status = self.status
        self.status = new_status
        self.add_activity(
            action=f"Status changed: {old_status.value} → {new_status.value}",
            details=notes
        )

        # Auto-set dates based on status
        now = datetime.utcnow()
        if new_status == ApplicationStatus.APPLIED and not self.applied_at:
            self.applied_at = now
        elif new_status == ApplicationStatus.OFFER and not self.offer_at:
            self.offer_at = now

    def __repr__(self):
        return f"<Application(id={self.id}, company='{self.company_name}', position='{self.position}', status='{self.status.value}')>"
