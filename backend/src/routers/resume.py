"""
Resume API endpoints for PathPilot.

Constitution Compliance:
- Principle II: API Resilience - Error handling with proper status codes
- Principle III: User Data Privacy - PII scrubbing in logs
- Principle V: Code Quality - Structured logging throughout

T027: POST /resume/upload endpoint
T028: GET /resume/{id}/analysis endpoint
"""

import time
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.resume_service import ResumeService
from src.utils.logging_config import get_logger
from src.utils.privacy import scrub_all_pii

logger = get_logger(__name__)

router = APIRouter(prefix="/resume", tags=["resume"])


def get_current_user_id() -> int:
    """
    Get current user ID from auth context.

    TODO: Replace with actual authentication logic (T013: Auth endpoints)
    For MVP, we'll use a hardcoded user ID.

    Returns:
        User ID
    """
    # Hardcoded for MVP - replace with actual auth
    return 1


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX, max 5MB)"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Upload and analyze resume.

    T027: Resume upload endpoint with multipart/form-data
    Constitution III: PII scrubbing in all logs

    Args:
        file: Uploaded resume file
        db: Database session
        user_id: Current user ID from auth

    Returns:
        Resume upload and analysis results:
        {
            "resume_id": int,
            "status": "analyzed" | "failed",
            "analysis": {
                "strengths": [...],
                "weaknesses": [...],
                "recommendations": [...],
                "suitable_roles": [...],
                "skills": [...],
                "experience_years": int
            },
            "message": "Resume analyzed successfully"
        }

    Raises:
        HTTPException 400: Invalid file type or size
        HTTPException 500: Analysis failed
    """
    start_time = time.time()

    logger.info(
        "resume_upload_request",
        operation="upload_resume",
        user_id=f"user-{user_id}",
        filename=scrub_all_pii(file.filename) if file.filename else "unknown",
        content_type=file.content_type,
    )

    try:
        # Initialize service
        resume_service = ResumeService(db)

        # Upload and analyze resume (handles validation, extraction, caching, analysis)
        resume = await resume_service.upload_and_analyze_resume(
            file=file,
            user_id=user_id,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # Check if analysis succeeded
        if resume.status == "analyzed":
            logger.info(
                "resume_upload_success",
                operation="upload_resume",
                user_id=f"user-{user_id}",
                resume_id=resume.id,
                duration_ms=duration_ms,
                status=resume.status,
            )

            return {
                "resume_id": resume.id,
                "status": resume.status,
                "analysis": resume.analysis_result,
                "message": "Resume analyzed successfully",
                "duration_ms": duration_ms,
            }
        else:
            # Analysis failed
            logger.error(
                "resume_upload_failed",
                operation="upload_resume",
                user_id=f"user-{user_id}",
                resume_id=resume.id,
                duration_ms=duration_ms,
                status=resume.status,
                error=resume.error_message,
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": "Resume analysis failed",
                    "error": resume.error_message,
                    "resume_id": resume.id,
                },
            )

    except ValueError as e:
        # Validation errors (file type, size, etc.)
        duration_ms = int((time.time() - start_time) * 1000)
        logger.warning(
            "resume_upload_validation_error",
            operation="upload_resume",
            user_id=f"user-{user_id}",
            duration_ms=duration_ms,
            error=str(e),
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
        )

    except Exception as e:
        # Unexpected errors
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "resume_upload_error",
            operation="upload_resume",
            user_id=f"user-{user_id}",
            duration_ms=duration_ms,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred during resume upload",
                "error": str(e),
            },
        )


@router.get("/{resume_id}/analysis")
async def get_resume_analysis(
    resume_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Retrieve resume analysis results.

    T028: Get resume analysis endpoint
    Constitution III: User can only access their own resumes

    Args:
        resume_id: Resume ID
        db: Database session
        user_id: Current user ID from auth

    Returns:
        Resume analysis:
        {
            "resume_id": int,
            "original_filename": str,
            "status": "analyzed" | "processing" | "failed",
            "analysis": {
                "strengths": [...],
                "weaknesses": [...],
                "recommendations": [...],
                "suitable_roles": [...],
                "skills": [...],
                "experience_years": int,
                "analyzed_at": "timestamp",
                "model_used": "gemini-1.5-pro"
            },
            "created_at": "timestamp",
            "analyzed_at": "timestamp" | null
        }

    Raises:
        HTTPException 404: Resume not found or access denied
    """
    start_time = time.time()

    logger.info(
        "get_resume_analysis_request",
        operation="get_resume_analysis",
        user_id=f"user-{user_id}",
        resume_id=resume_id,
    )

    try:
        # Initialize service
        resume_service = ResumeService(db)

        # Get resume (only if user owns it)
        resume = resume_service.get_resume_by_id(resume_id, user_id)

        if not resume:
            logger.warning(
                "resume_not_found",
                operation="get_resume_analysis",
                user_id=f"user-{user_id}",
                resume_id=resume_id,
            )

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"Resume {resume_id} not found or access denied"},
            )

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "get_resume_analysis_success",
            operation="get_resume_analysis",
            user_id=f"user-{user_id}",
            resume_id=resume_id,
            duration_ms=duration_ms,
            status=resume.status,
        )

        # Build response
        response = {
            "resume_id": resume.id,
            "original_filename": scrub_all_pii(resume.original_filename),
            "status": resume.status,
            "analysis": resume.analysis_result if resume.is_analyzed() else None,
            "created_at": resume.created_at.isoformat() if resume.created_at else None,
            "analyzed_at": resume.analyzed_at.isoformat() if resume.analyzed_at else None,
            "error_message": resume.error_message if resume.status == "failed" else None,
        }

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "get_resume_analysis_error",
            operation="get_resume_analysis",
            user_id=f"user-{user_id}",
            resume_id=resume_id,
            duration_ms=duration_ms,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred while retrieving resume analysis",
                "error": str(e),
            },
        )
