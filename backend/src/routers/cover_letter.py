"""
Cover Letter API endpoints for PathPilot.

Constitution Compliance:
- Principle II: API Resilience - Error handling with proper status codes
- Principle III: User Data Privacy - PII scrubbing in logs
- Principle V: Code Quality - Structured logging throughout

T042: POST /cover-letter/generate endpoint
T043: PUT /cover-letter/{id} endpoint
T044: Logging + PII scrubbing
"""

import time
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.cover_letter_service import CoverLetterService
from src.utils.logging_config import get_logger
from src.utils.privacy import scrub_all_pii

logger = get_logger(__name__)

router = APIRouter(prefix="/cover-letter", tags=["cover-letter"])


# Request/Response Models
class CoverLetterGenerateRequest(BaseModel):
    """Request model for cover letter generation."""
    job_title: str = Field(..., min_length=1, max_length=255, description="Target job title")
    company_name: str = Field(..., min_length=1, max_length=255, description="Target company name")
    job_description: Optional[str] = Field(None, max_length=10000, description="Job posting text")
    resume_id: Optional[int] = Field(None, description="Resume ID to use for personalization")
    tone: str = Field("professional", description="Writing tone: professional, casual, enthusiastic")
    length: str = Field("medium", description="Length: short, medium, long")
    focus_areas: Optional[List[str]] = Field(None, description="Areas to emphasize")
    custom_instructions: Optional[str] = Field(None, max_length=1000, description="Additional instructions")


class CoverLetterUpdateRequest(BaseModel):
    """Request model for cover letter update."""
    content: Optional[str] = Field(None, description="New content for manual edit")
    regenerate: bool = Field(False, description="If True, regenerate with AI")


class CoverLetterResponse(BaseModel):
    """Response model for cover letter."""
    id: int
    job_title: str
    company_name: str
    content: Optional[str]
    status: str
    version: int
    word_count: int
    created_at: Optional[str]
    generated_at: Optional[str]


def get_current_user_id() -> int:
    """
    Get current user ID from auth context.

    TODO: Replace with actual authentication logic
    For MVP, we'll use a hardcoded user ID.
    """
    return 1


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_cover_letter(
    request: CoverLetterGenerateRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Generate a new cover letter using AI.

    T042: Cover letter generation endpoint
    Constitution III: PII scrubbing in all logs

    Args:
        request: Generation parameters
        db: Database session
        user_id: Current user ID

    Returns:
        Generated cover letter with metadata:
        {
            "cover_letter_id": int,
            "status": "generated" | "failed",
            "content": str,
            "word_count": int,
            "message": str
        }
    """
    start_time = time.time()

    logger.info(
        "cover_letter_generate_request",
        operation="generate_cover_letter",
        user_id=f"user-{user_id}",
        job_title=scrub_all_pii(request.job_title),
        company_name=scrub_all_pii(request.company_name),
        has_job_description=bool(request.job_description),
        resume_id=request.resume_id,
        tone=request.tone,
        length=request.length,
    )

    try:
        service = CoverLetterService(db)

        cover_letter = await service.generate_cover_letter(
            user_id=user_id,
            job_title=request.job_title,
            company_name=request.company_name,
            job_description=request.job_description,
            resume_id=request.resume_id,
            tone=request.tone,
            length=request.length,
            focus_areas=request.focus_areas,
            custom_instructions=request.custom_instructions,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        if cover_letter.status == "generated":
            logger.info(
                "cover_letter_generate_success",
                operation="generate_cover_letter",
                user_id=f"user-{user_id}",
                cover_letter_id=cover_letter.id,
                duration_ms=duration_ms,
                word_count=cover_letter.get_word_count(),
            )

            return {
                "cover_letter_id": cover_letter.id,
                "status": cover_letter.status,
                "content": cover_letter.content,
                "job_title": cover_letter.job_title,
                "company_name": cover_letter.company_name,
                "word_count": cover_letter.get_word_count(),
                "version": cover_letter.version,
                "message": "Cover letter generated successfully",
                "duration_ms": duration_ms,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": "Cover letter generation failed",
                    "error": cover_letter.error_message,
                    "cover_letter_id": cover_letter.id,
                },
            )

    except ValueError as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.warning(
            "cover_letter_generate_validation_error",
            operation="generate_cover_letter",
            user_id=f"user-{user_id}",
            duration_ms=duration_ms,
            error=str(e),
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "cover_letter_generate_error",
            operation="generate_cover_letter",
            user_id=f"user-{user_id}",
            duration_ms=duration_ms,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred during cover letter generation",
                "error": str(e),
            },
        )


@router.get("/{cover_letter_id}")
async def get_cover_letter(
    cover_letter_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Get a specific cover letter by ID.

    Args:
        cover_letter_id: Cover letter ID
        db: Database session
        user_id: Current user ID

    Returns:
        Cover letter details
    """
    logger.info(
        "get_cover_letter_request",
        operation="get_cover_letter",
        user_id=f"user-{user_id}",
        cover_letter_id=cover_letter_id,
    )

    service = CoverLetterService(db)
    cover_letter = service.get_cover_letter_by_id(cover_letter_id, user_id)

    if not cover_letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Cover letter {cover_letter_id} not found"},
        )

    return {
        "cover_letter_id": cover_letter.id,
        "job_title": cover_letter.job_title,
        "company_name": cover_letter.company_name,
        "job_description": cover_letter.job_description,
        "content": cover_letter.content,
        "status": cover_letter.status,
        "version": cover_letter.version,
        "word_count": cover_letter.get_word_count(),
        "generation_params": cover_letter.generation_params,
        "created_at": cover_letter.created_at.isoformat() if cover_letter.created_at else None,
        "generated_at": cover_letter.generated_at.isoformat() if cover_letter.generated_at else None,
    }


@router.put("/{cover_letter_id}")
async def update_cover_letter(
    cover_letter_id: int,
    request: CoverLetterUpdateRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Update or regenerate a cover letter.

    T043: Cover letter update endpoint

    Args:
        cover_letter_id: Cover letter ID
        request: Update parameters
        db: Database session
        user_id: Current user ID

    Returns:
        Updated cover letter
    """
    start_time = time.time()

    logger.info(
        "cover_letter_update_request",
        operation="update_cover_letter",
        user_id=f"user-{user_id}",
        cover_letter_id=cover_letter_id,
        regenerate=request.regenerate,
        has_content=bool(request.content),
    )

    try:
        service = CoverLetterService(db)

        cover_letter = await service.update_cover_letter(
            cover_letter_id=cover_letter_id,
            user_id=user_id,
            content=request.content,
            regenerate=request.regenerate,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "cover_letter_update_success",
            operation="update_cover_letter",
            user_id=f"user-{user_id}",
            cover_letter_id=cover_letter_id,
            duration_ms=duration_ms,
            new_version=cover_letter.version,
        )

        return {
            "cover_letter_id": cover_letter.id,
            "status": cover_letter.status,
            "content": cover_letter.content,
            "version": cover_letter.version,
            "word_count": cover_letter.get_word_count(),
            "message": "Cover letter updated successfully",
            "duration_ms": duration_ms,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(e)},
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "cover_letter_update_error",
            operation="update_cover_letter",
            user_id=f"user-{user_id}",
            cover_letter_id=cover_letter_id,
            duration_ms=duration_ms,
            error=str(e),
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": str(e)},
        )


@router.get("/")
async def list_cover_letters(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    limit: int = 20,
) -> Dict[str, Any]:
    """
    List all cover letters for the current user.

    Args:
        db: Database session
        user_id: Current user ID
        limit: Maximum number of results

    Returns:
        List of cover letter summaries
    """
    logger.info(
        "list_cover_letters_request",
        operation="list_cover_letters",
        user_id=f"user-{user_id}",
        limit=limit,
    )

    service = CoverLetterService(db)
    cover_letters = service.get_user_cover_letters(user_id, limit)

    return {
        "cover_letters": [cl.get_summary() for cl in cover_letters],
        "count": len(cover_letters),
    }
