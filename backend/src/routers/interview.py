"""
Interview API endpoints for PathPilot Mock Interview feature.

Constitution Compliance:
- Principle II: API Resilience - Error handling with proper status codes
- Principle III: User Data Privacy - PII scrubbing in logs
- Principle V: Code Quality - Structured logging throughout

T070: POST /interview/generate-questions endpoint
T071: POST /interview/evaluate-answer endpoint
"""

import time
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.interview_service import InterviewService
from src.utils.logging_config import get_logger
from src.utils.privacy import scrub_all_pii

logger = get_logger(__name__)

router = APIRouter(prefix="/interview", tags=["interview"])


# Request/Response Models
class GenerateQuestionsRequest(BaseModel):
    """Request model for generating interview questions."""
    job_title: str = Field(..., min_length=1, max_length=255, description="Target job title")
    company_name: Optional[str] = Field(None, max_length=255, description="Company name")
    job_description: Optional[str] = Field(None, max_length=10000, description="Job description")
    resume_id: Optional[int] = Field(None, description="Resume ID for personalization")
    job_id: Optional[int] = Field(None, description="Saved job ID")
    interview_type: str = Field("mixed", description="Interview type: behavioral, technical, mixed")
    difficulty: str = Field("mid", description="Difficulty: entry, mid, senior")
    question_count: int = Field(5, ge=1, le=10, description="Number of questions")
    focus_areas: Optional[List[str]] = Field(None, description="Areas to focus on")
    language: str = Field("ko", description="Response language: ko, en")


class EvaluateAnswerRequest(BaseModel):
    """Request model for evaluating an answer."""
    question_id: int = Field(..., description="Question ID within the interview")
    answer_text: str = Field(..., min_length=1, max_length=5000, description="User's answer")
    answer_audio_url: Optional[str] = Field(None, description="Audio recording URL")


class QuestionResponse(BaseModel):
    """Response model for a single question."""
    id: int
    question: str
    type: str
    difficulty: int
    expected_topics: List[str]
    time_limit_seconds: int
    tips: str = ""


class InterviewResponse(BaseModel):
    """Response model for interview session."""
    interview_id: int
    status: str
    job_title: str
    company_name: Optional[str]
    question_count: int
    questions: List[QuestionResponse]
    config: Dict[str, Any]


class EvaluationResponse(BaseModel):
    """Response model for answer evaluation."""
    question_id: int
    evaluation: Dict[str, Any]
    progress: Dict[str, Any]
    is_completed: bool
    total_score: Optional[float]


def get_current_user_id() -> int:
    """
    Get current user ID from auth context.
    TODO: Replace with actual authentication logic
    """
    return 1


@router.post("/generate-questions", status_code=status.HTTP_201_CREATED)
async def generate_interview_questions(
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Generate mock interview questions.

    T070: POST /interview/generate-questions endpoint

    Creates a new interview session with AI-generated questions based on:
    - Job title and description
    - Resume (if provided)
    - Interview type (behavioral, technical, mixed)
    - Difficulty level

    Returns:
        Interview session with generated questions
    """
    start_time = time.time()

    logger.info(
        "api_generate_questions_started",
        operation="generate_questions",
        user_id=f"user-{user_id}",
        job_title=scrub_all_pii(request.job_title),
        interview_type=request.interview_type,
        question_count=request.question_count,
    )

    try:
        service = InterviewService(db)
        interview = await service.generate_interview(
            user_id=user_id,
            job_title=request.job_title,
            company_name=request.company_name,
            job_description=request.job_description,
            resume_id=request.resume_id,
            job_id=request.job_id,
            interview_type=request.interview_type,
            difficulty=request.difficulty,
            question_count=request.question_count,
            focus_areas=request.focus_areas,
            language=request.language,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "api_generate_questions_completed",
            operation="generate_questions",
            interview_id=interview.id,
            question_count=interview.get_question_count(),
            duration_ms=duration_ms,
        )

        return {
            "interview_id": interview.id,
            "status": interview.status,
            "job_title": interview.job_title,
            "company_name": interview.company_name,
            "question_count": interview.get_question_count(),
            "questions": interview.questions,
            "config": interview.config,
            "generation_time_ms": duration_ms,
        }

    except ValueError as e:
        logger.warning(
            "api_generate_questions_validation_error",
            operation="generate_questions",
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
        )
    except Exception as e:
        logger.error(
            "api_generate_questions_failed",
            operation="generate_questions",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to generate interview questions"},
        )


@router.post("/{interview_id}/evaluate-answer", status_code=status.HTTP_200_OK)
async def evaluate_answer(
    interview_id: int,
    request: EvaluateAnswerRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Evaluate a user's answer to an interview question.

    T071: POST /interview/{id}/evaluate-answer endpoint

    Evaluates the answer and provides:
    - Score (0-100)
    - Strengths and improvements
    - Detailed feedback
    - Model answer example

    Returns:
        Evaluation result with feedback
    """
    start_time = time.time()

    logger.info(
        "api_evaluate_answer_started",
        operation="evaluate_answer",
        interview_id=interview_id,
        question_id=request.question_id,
    )

    try:
        service = InterviewService(db)

        # Check interview exists
        interview = service.get_interview(interview_id, user_id)
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"Interview {interview_id} not found"},
            )

        result = await service.evaluate_answer(
            interview_id=interview_id,
            user_id=user_id,
            question_id=request.question_id,
            answer_text=request.answer_text,
            answer_audio_url=request.answer_audio_url,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "api_evaluate_answer_completed",
            operation="evaluate_answer",
            interview_id=interview_id,
            question_id=request.question_id,
            score=result["evaluation"]["score"],
            duration_ms=duration_ms,
        )

        result["evaluation_time_ms"] = duration_ms
        return result

    except ValueError as e:
        logger.warning(
            "api_evaluate_answer_validation_error",
            operation="evaluate_answer",
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "api_evaluate_answer_failed",
            operation="evaluate_answer",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to evaluate answer"},
        )


@router.get("/{interview_id}", status_code=status.HTTP_200_OK)
async def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Get interview session details.

    Returns full interview data including questions and answers.
    """
    logger.info(
        "api_get_interview",
        operation="get_interview",
        interview_id=interview_id,
    )

    service = InterviewService(db)
    interview = service.get_interview(interview_id, user_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Interview {interview_id} not found"},
        )

    return {
        "interview_id": interview.id,
        "status": interview.status,
        "job_title": interview.job_title,
        "company_name": interview.company_name,
        "job_description": interview.job_description,
        "config": interview.config,
        "questions": interview.questions,
        "answers": interview.answers,
        "progress": interview.get_progress(),
        "total_score": interview.total_score,
        "created_at": interview.created_at.isoformat() if interview.created_at else None,
        "started_at": interview.started_at.isoformat() if interview.started_at else None,
        "completed_at": interview.completed_at.isoformat() if interview.completed_at else None,
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def get_interview_history(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Get user's interview history.

    Returns list of interview sessions with summary info.
    """
    logger.info(
        "api_get_interview_history",
        operation="get_interview_history",
        user_id=f"user-{user_id}",
        limit=limit,
        offset=offset,
    )

    service = InterviewService(db)
    interviews = service.get_user_interviews(user_id, limit, offset)

    return {
        "interviews": [i.get_summary() for i in interviews],
        "count": len(interviews),
        "limit": limit,
        "offset": offset,
    }


@router.delete("/{interview_id}", status_code=status.HTTP_200_OK)
async def delete_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """Delete an interview session."""
    logger.info(
        "api_delete_interview",
        operation="delete_interview",
        interview_id=interview_id,
    )

    service = InterviewService(db)
    interview = service.get_interview(interview_id, user_id)

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Interview {interview_id} not found"},
        )

    db.delete(interview)
    db.commit()

    return {"message": "Interview deleted successfully", "interview_id": interview_id}
