"""
Application service for PathPilot.

Handles CRUD operations for job applications.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.models.application import Application, ApplicationStatus
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ApplicationService:
    """Service for managing job applications."""

    def __init__(self, db: Session):
        self.db = db

    def create_application(
        self,
        user_id: int,
        company_name: str,
        position: str,
        job_url: Optional[str] = None,
        location: Optional[str] = None,
        salary_range: Optional[str] = None,
        status: ApplicationStatus = ApplicationStatus.SAVED,
        resume_id: Optional[int] = None,
        cover_letter_id: Optional[int] = None,
        job_id: Optional[int] = None,
        notes: Optional[str] = None,
        deadline: Optional[datetime] = None,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
    ) -> Application:
        """
        Create a new job application.

        Args:
            user_id: User ID
            company_name: Company name
            position: Job position/title
            job_url: URL to job posting
            location: Job location
            salary_range: Expected salary range
            status: Initial status
            resume_id: Linked resume ID
            cover_letter_id: Linked cover letter ID
            job_id: Linked job ID
            notes: Additional notes
            deadline: Application deadline
            contact_name: Recruiter/contact name
            contact_email: Recruiter/contact email

        Returns:
            Created Application object
        """
        logger.info(
            "application_create_started",
            operation="create_application",
            user_id=f"user-{user_id}",
            company=company_name,
            position=position,
        )

        application = Application(
            user_id=user_id,
            company_name=company_name,
            position=position,
            job_url=job_url,
            location=location,
            salary_range=salary_range,
            status=status,
            resume_id=resume_id,
            cover_letter_id=cover_letter_id,
            job_id=job_id,
            notes=notes,
            deadline=deadline,
            contact_name=contact_name,
            contact_email=contact_email,
            activity_log=[],
        )

        # Add initial activity
        application.add_activity(
            action=f"Application created with status: {status.value}",
            details=f"Position: {position} at {company_name}"
        )

        # Set applied_at if status is APPLIED
        if status == ApplicationStatus.APPLIED:
            application.applied_at = datetime.utcnow()

        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)

        logger.info(
            "application_created",
            operation="create_application",
            user_id=f"user-{user_id}",
            application_id=application.id,
            company=company_name,
            position=position,
            status=status.value,
        )

        return application

    def get_application_by_id(
        self, application_id: int, user_id: int
    ) -> Optional[Application]:
        """
        Get application by ID for specific user.

        Args:
            application_id: Application ID
            user_id: User ID

        Returns:
            Application object or None
        """
        return (
            self.db.query(Application)
            .filter(
                Application.id == application_id,
                Application.user_id == user_id,
            )
            .first()
        )

    def get_user_applications(
        self,
        user_id: int,
        status: Optional[ApplicationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Application]:
        """
        Get all applications for a user.

        Args:
            user_id: User ID
            status: Filter by status (optional)
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of Application objects
        """
        query = self.db.query(Application).filter(Application.user_id == user_id)

        if status:
            query = query.filter(Application.status == status)

        return (
            query.order_by(desc(Application.updated_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def update_application(
        self,
        application_id: int,
        user_id: int,
        **kwargs
    ) -> Optional[Application]:
        """
        Update an application.

        Args:
            application_id: Application ID
            user_id: User ID
            **kwargs: Fields to update

        Returns:
            Updated Application object or None
        """
        application = self.get_application_by_id(application_id, user_id)
        if not application:
            return None

        # Track what changed for activity log
        changes = []

        for key, value in kwargs.items():
            if hasattr(application, key) and value is not None:
                old_value = getattr(application, key)
                if old_value != value:
                    setattr(application, key, value)
                    changes.append(f"{key}: {old_value} → {value}")

        if changes:
            application.add_activity(
                action="Application updated",
                details="; ".join(changes)
            )

        self.db.commit()
        self.db.refresh(application)

        logger.info(
            "application_updated",
            operation="update_application",
            user_id=f"user-{user_id}",
            application_id=application_id,
            changes=changes,
        )

        return application

    def update_status(
        self,
        application_id: int,
        user_id: int,
        new_status: ApplicationStatus,
        notes: Optional[str] = None,
    ) -> Optional[Application]:
        """
        Update application status.

        Args:
            application_id: Application ID
            user_id: User ID
            new_status: New status
            notes: Optional notes about the change

        Returns:
            Updated Application object or None
        """
        application = self.get_application_by_id(application_id, user_id)
        if not application:
            return None

        old_status = application.status
        application.update_status(new_status, notes)

        self.db.commit()
        self.db.refresh(application)

        logger.info(
            "application_status_updated",
            operation="update_status",
            user_id=f"user-{user_id}",
            application_id=application_id,
            old_status=old_status.value,
            new_status=new_status.value,
        )

        return application

    def delete_application(self, application_id: int, user_id: int) -> bool:
        """
        Delete an application.

        Args:
            application_id: Application ID
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        application = self.get_application_by_id(application_id, user_id)
        if not application:
            return False

        self.db.delete(application)
        self.db.commit()

        logger.info(
            "application_deleted",
            operation="delete_application",
            user_id=f"user-{user_id}",
            application_id=application_id,
        )

        return True

    def get_application_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get application statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with statistics
        """
        applications = self.db.query(Application).filter(
            Application.user_id == user_id
        ).all()

        # Count by status
        status_counts = {}
        for status in ApplicationStatus:
            status_counts[status.value] = sum(
                1 for a in applications if a.status == status
            )

        # Recent activity
        recent = sorted(
            applications,
            key=lambda a: a.updated_at,
            reverse=True
        )[:5]

        # Upcoming interviews
        now = datetime.utcnow()
        upcoming_interviews = [
            a for a in applications
            if a.interview_at and a.interview_at > now
        ]
        upcoming_interviews.sort(key=lambda a: a.interview_at)

        return {
            "total": len(applications),
            "by_status": status_counts,
            "active": sum(
                1 for a in applications
                if a.status not in [
                    ApplicationStatus.REJECTED,
                    ApplicationStatus.WITHDRAWN,
                    ApplicationStatus.ACCEPTED
                ]
            ),
            "recent_applications": [
                {
                    "id": a.id,
                    "company": a.company_name,
                    "position": a.position,
                    "status": a.status.value,
                    "updated_at": a.updated_at.isoformat(),
                }
                for a in recent
            ],
            "upcoming_interviews": [
                {
                    "id": a.id,
                    "company": a.company_name,
                    "position": a.position,
                    "interview_at": a.interview_at.isoformat(),
                }
                for a in upcoming_interviews[:3]
            ],
        }
