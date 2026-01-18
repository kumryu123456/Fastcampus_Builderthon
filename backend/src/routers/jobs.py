"""
Job Discovery API endpoints for PathPilot.

Constitution Compliance:
- Principle II: API Resilience - Error handling with proper status codes
- Principle III: User Data Privacy - PII scrubbing in logs
- Principle V: Code Quality - Structured logging throughout

T057: POST /jobs/recommend endpoint
T058: POST /jobs/match endpoint
"""

import time
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.job_service import JobService
from src.utils.logging_config import get_logger
from src.utils.privacy import scrub_all_pii

logger = get_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


# Request/Response Models
class JobRecommendRequest(BaseModel):
    """Request model for job recommendations."""
    resume_id: int = Field(..., description="Resume ID to base recommendations on")
    location: Optional[str] = Field(None, description="Preferred location")
    job_type: Optional[str] = Field(None, description="Job type: full-time, part-time, etc.")
    experience_level: Optional[str] = Field(None, description="Experience level: entry, mid, senior")
    industry: Optional[str] = Field(None, description="Preferred industry")
    limit: int = Field(10, ge=1, le=20, description="Number of recommendations")


class JobMatchRequest(BaseModel):
    """Request model for job match analysis."""
    resume_id: int = Field(..., description="Resume ID to analyze")
    job_title: str = Field(..., min_length=1, max_length=255, description="Job title")
    job_description: str = Field(..., min_length=10, max_length=10000, description="Job description")
    company: Optional[str] = Field(None, max_length=255, description="Company name")


class JobSaveRequest(BaseModel):
    """Request model for saving a job."""
    title: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    job_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=10000)
    url: Optional[str] = Field(None, max_length=1000)


class JobSearchRequest(BaseModel):
    """Request model for job search."""
    query: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    job_type: Optional[str] = Field(None, max_length=50)
    experience_level: Optional[str] = Field(None, max_length=50)
    limit: int = Field(20, ge=1, le=50)


def get_current_user_id() -> int:
    """Get current user ID (MVP: hardcoded)."""
    return 1


@router.post("/recommend", status_code=status.HTTP_200_OK)
async def get_job_recommendations(
    request: JobRecommendRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Get AI-powered job recommendations based on resume.

    T057: Job recommendation endpoint

    Returns:
        List of recommended jobs with match analysis
    """
    start_time = time.time()

    logger.info(
        "job_recommend_request",
        operation="get_job_recommendations",
        user_id=f"user-{user_id}",
        resume_id=request.resume_id,
        limit=request.limit,
    )

    try:
        service = JobService(db)

        preferences = {
            "location": request.location,
            "job_type": request.job_type,
            "experience_level": request.experience_level,
            "industry": request.industry,
        }
        # Remove None values
        preferences = {k: v for k, v in preferences.items() if v}

        recommendations = await service.get_job_recommendations(
            user_id=user_id,
            resume_id=request.resume_id,
            job_preferences=preferences if preferences else None,
            limit=request.limit,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "job_recommend_success",
            operation="get_job_recommendations",
            user_id=f"user-{user_id}",
            recommendations_count=len(recommendations),
            duration_ms=duration_ms,
        )

        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "resume_id": request.resume_id,
            "duration_ms": duration_ms,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
        )

    except Exception as e:
        logger.error(
            "job_recommend_error",
            operation="get_job_recommendations",
            user_id=f"user-{user_id}",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": str(e)},
        )


@router.post("/match", status_code=status.HTTP_200_OK)
async def analyze_job_match(
    request: JobMatchRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Analyze how well a job matches the resume.

    T058: Job match analysis endpoint

    Returns:
        Match analysis with score and details
    """
    start_time = time.time()

    logger.info(
        "job_match_request",
        operation="analyze_job_match",
        user_id=f"user-{user_id}",
        resume_id=request.resume_id,
        job_title=scrub_all_pii(request.job_title),
    )

    try:
        service = JobService(db)

        analysis = await service.analyze_job_match(
            user_id=user_id,
            resume_id=request.resume_id,
            job_title=request.job_title,
            job_description=request.job_description,
            company=request.company,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "job_match_success",
            operation="analyze_job_match",
            user_id=f"user-{user_id}",
            match_score=analysis.get("match_score"),
            duration_ms=duration_ms,
        )

        return {
            "analysis": analysis,
            "job_title": request.job_title,
            "company": request.company,
            "duration_ms": duration_ms,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
        )

    except Exception as e:
        logger.error(
            "job_match_error",
            operation="analyze_job_match",
            user_id=f"user-{user_id}",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": str(e)},
        )


@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_job(
    request: JobSaveRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """Save a job to user's list."""
    logger.info(
        "job_save_request",
        operation="save_job",
        user_id=f"user-{user_id}",
        job_title=scrub_all_pii(request.title),
    )

    try:
        service = JobService(db)

        job = await service.save_job(
            user_id=user_id,
            title=request.title,
            company=request.company,
            location=request.location,
            job_type=request.job_type,
            description=request.description,
            url=request.url,
        )

        return {
            "job_id": job.id,
            "message": "Job saved successfully",
            "job": job.get_summary(),
        }

    except Exception as e:
        logger.error(
            "job_save_error",
            operation="save_job",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": str(e)},
        )


@router.get("/saved")
async def get_saved_jobs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    limit: int = 50,
) -> Dict[str, Any]:
    """Get user's saved jobs."""
    service = JobService(db)
    jobs = service.get_saved_jobs(user_id, limit)

    return {
        "jobs": [job.get_summary() for job in jobs],
        "count": len(jobs),
    }


@router.post("/search")
async def search_jobs(
    request: JobSearchRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """Search jobs."""
    service = JobService(db)

    jobs = await service.search_jobs(
        user_id=user_id,
        query=request.query,
        location=request.location,
        job_type=request.job_type,
        experience_level=request.experience_level,
        limit=request.limit,
    )

    return {
        "jobs": [job.get_summary() for job in jobs],
        "count": len(jobs),
    }


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """Get job details."""
    service = JobService(db)
    job = service.get_job_by_id(job_id, user_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Job {job_id} not found"},
        )

    return {
        "job": {
            **job.get_summary(),
            "description": job.description,
            "requirements": job.requirements,
            "url": job.url,
            "match_analysis": job.match_analysis,
            "notes": job.notes,
        }
    }
