"""
Application API endpoints for PathPilot.

Tracks job applications with CRUD operations.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.application import ApplicationStatus
from src.services.application_service import ApplicationService
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/applications", tags=["applications"])


# Pydantic models for request/response
class ApplicationCreate(BaseModel):
    """Request model for creating an application."""
    company_name: str = Field(..., min_length=1, max_length=255)
    position: str = Field(..., min_length=1, max_length=255)
    job_url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    salary_range: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field("saved", description="Initial status")
    resume_id: Optional[int] = None
    cover_letter_id: Optional[int] = None
    job_id: Optional[int] = None
    notes: Optional[str] = None
    deadline: Optional[datetime] = None
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)


class ApplicationUpdate(BaseModel):
    """Request model for updating an application."""
    company_name: Optional[str] = Field(None, max_length=255)
    position: Optional[str] = Field(None, max_length=255)
    job_url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    salary_range: Optional[str] = Field(None, max_length=100)
    resume_id: Optional[int] = None
    cover_letter_id: Optional[int] = None
    job_id: Optional[int] = None
    notes: Optional[str] = None
    deadline: Optional[datetime] = None
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    interview_at: Optional[datetime] = None


class StatusUpdate(BaseModel):
    """Request model for updating application status."""
    status: str = Field(..., description="New status")
    notes: Optional[str] = Field(None, description="Notes about the change")


def get_current_user_id() -> int:
    """Get current user ID from auth context."""
    # Hardcoded for MVP - replace with actual auth
    return 1


def parse_status(status_str: str) -> ApplicationStatus:
    """Parse status string to enum."""
    try:
        return ApplicationStatus(status_str.lower())
    except ValueError:
        valid = [s.value for s in ApplicationStatus]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{status_str}'. Valid values: {valid}"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Create a new job application.

    Args:
        data: Application data
        db: Database session
        user_id: Current user ID

    Returns:
        Created application data
    """
    logger.info(
        "application_create_request",
        operation="create_application",
        user_id=f"user-{user_id}",
        company=data.company_name,
        position=data.position,
    )

    try:
        service = ApplicationService(db)

        # Parse status
        app_status = parse_status(data.status) if data.status else ApplicationStatus.SAVED

        application = service.create_application(
            user_id=user_id,
            company_name=data.company_name,
            position=data.position,
            job_url=data.job_url,
            location=data.location,
            salary_range=data.salary_range,
            status=app_status,
            resume_id=data.resume_id,
            cover_letter_id=data.cover_letter_id,
            job_id=data.job_id,
            notes=data.notes,
            deadline=data.deadline,
            contact_name=data.contact_name,
            contact_email=data.contact_email,
        )

        return {
            "id": application.id,
            "company_name": application.company_name,
            "position": application.position,
            "status": application.status.value,
            "created_at": application.created_at.isoformat(),
            "message": "Application created successfully",
        }

    except Exception as e:
        logger.error(
            "application_create_error",
            operation="create_application",
            user_id=f"user-{user_id}",
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to create application", "error": str(e)}
        )


@router.get("/")
async def list_applications(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    List all applications for the current user.

    Args:
        status_filter: Filter by status (optional)
        limit: Maximum number of results
        offset: Offset for pagination
        db: Database session
        user_id: Current user ID

    Returns:
        List of applications
    """
    service = ApplicationService(db)

    # Parse status filter if provided
    app_status = None
    if status_filter:
        app_status = parse_status(status_filter)

    applications = service.get_user_applications(
        user_id=user_id,
        status=app_status,
        limit=limit,
        offset=offset,
    )

    return {
        "applications": [
            {
                "id": app.id,
                "company_name": app.company_name,
                "position": app.position,
                "location": app.location,
                "status": app.status.value,
                "job_url": app.job_url,
                "salary_range": app.salary_range,
                "resume_id": app.resume_id,
                "cover_letter_id": app.cover_letter_id,
                "applied_at": app.applied_at.isoformat() if app.applied_at else None,
                "interview_at": app.interview_at.isoformat() if app.interview_at else None,
                "deadline": app.deadline.isoformat() if app.deadline else None,
                "notes": app.notes,
                "contact_name": app.contact_name,
                "contact_email": app.contact_email,
                "created_at": app.created_at.isoformat(),
                "updated_at": app.updated_at.isoformat(),
            }
            for app in applications
        ],
        "total": len(applications),
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
async def get_application_stats(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Get application statistics for the current user.

    Returns:
        Statistics including counts by status, recent applications, etc.
    """
    service = ApplicationService(db)
    stats = service.get_application_stats(user_id)
    return stats


@router.get("/statuses")
async def get_available_statuses() -> Dict[str, Any]:
    """
    Get all available application statuses.

    Returns:
        List of valid status values
    """
    return {
        "statuses": [
            {"value": s.value, "label": s.value.replace("_", " ").title()}
            for s in ApplicationStatus
        ]
    }


@router.get("/{application_id}")
async def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Get a specific application by ID.

    Args:
        application_id: Application ID
        db: Database session
        user_id: Current user ID

    Returns:
        Application data
    """
    service = ApplicationService(db)
    application = service.get_application_by_id(application_id, user_id)

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Application {application_id} not found"}
        )

    return {
        "id": application.id,
        "company_name": application.company_name,
        "position": application.position,
        "location": application.location,
        "status": application.status.value,
        "job_url": application.job_url,
        "salary_range": application.salary_range,
        "resume_id": application.resume_id,
        "cover_letter_id": application.cover_letter_id,
        "job_id": application.job_id,
        "applied_at": application.applied_at.isoformat() if application.applied_at else None,
        "interview_at": application.interview_at.isoformat() if application.interview_at else None,
        "offer_at": application.offer_at.isoformat() if application.offer_at else None,
        "deadline": application.deadline.isoformat() if application.deadline else None,
        "notes": application.notes,
        "contact_name": application.contact_name,
        "contact_email": application.contact_email,
        "activity_log": application.activity_log or [],
        "created_at": application.created_at.isoformat(),
        "updated_at": application.updated_at.isoformat(),
    }


@router.put("/{application_id}")
async def update_application(
    application_id: int,
    data: ApplicationUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Update an application.

    Args:
        application_id: Application ID
        data: Fields to update
        db: Database session
        user_id: Current user ID

    Returns:
        Updated application data
    """
    service = ApplicationService(db)

    # Convert to dict, excluding None values
    update_data = {k: v for k, v in data.dict().items() if v is not None}

    application = service.update_application(
        application_id=application_id,
        user_id=user_id,
        **update_data
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Application {application_id} not found"}
        )

    return {
        "id": application.id,
        "company_name": application.company_name,
        "position": application.position,
        "status": application.status.value,
        "updated_at": application.updated_at.isoformat(),
        "message": "Application updated successfully",
    }


@router.patch("/{application_id}/status")
async def update_application_status(
    application_id: int,
    data: StatusUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Update application status.

    Args:
        application_id: Application ID
        data: New status and optional notes
        db: Database session
        user_id: Current user ID

    Returns:
        Updated application data
    """
    service = ApplicationService(db)

    new_status = parse_status(data.status)

    application = service.update_status(
        application_id=application_id,
        user_id=user_id,
        new_status=new_status,
        notes=data.notes,
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Application {application_id} not found"}
        )

    return {
        "id": application.id,
        "company_name": application.company_name,
        "position": application.position,
        "status": application.status.value,
        "updated_at": application.updated_at.isoformat(),
        "message": f"Status updated to {application.status.value}",
    }


@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Delete an application.

    Args:
        application_id: Application ID
        db: Database session
        user_id: Current user ID

    Returns:
        Success message
    """
    service = ApplicationService(db)
    deleted = service.delete_application(application_id, user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Application {application_id} not found"}
        )

    return {
        "message": f"Application {application_id} deleted successfully"
    }
