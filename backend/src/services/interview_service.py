"""
Interview service for mock interview generation and evaluation.

Constitution Compliance:
- Principle II: API Resilience - Retry logic for Gemini calls
- Principle III: User Data Privacy - PII scrubbing in logs
- Principle V: Code Quality - Structured logging throughout

T069: Interview service for question generation and answer evaluation
"""

import time
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy.orm import Session

from src.config import settings
from src.models.interview import Interview
from src.models.resume import Resume
from src.models.job import Job
from src.services.gemini_client import GeminiClient
from src.utils.logging_config import get_logger
from src.utils.privacy import scrub_all_pii

logger = get_logger(__name__)


class InterviewService:
    """
    Service for handling mock interview operations.

    T069: Interview question generation and answer evaluation
    """

    # Default configuration
    DEFAULT_QUESTION_COUNT = 5
    DEFAULT_INTERVIEW_TYPE = "mixed"
    DEFAULT_DIFFICULTY = "mid"
    DEFAULT_LANGUAGE = "ko"

    def __init__(self, db: Session):
        """
        Initialize interview service.

        Args:
            db: Database session
        """
        self.db = db
        self.gemini_client = GeminiClient()

    async def generate_interview(
        self,
        user_id: int,
        job_title: str,
        company_name: Optional[str] = None,
        job_description: Optional[str] = None,
        resume_id: Optional[int] = None,
        job_id: Optional[int] = None,
        interview_type: str = "mixed",
        difficulty: str = "mid",
        question_count: int = 5,
        focus_areas: Optional[List[str]] = None,
        language: str = "ko",
    ) -> Interview:
        """
        Generate mock interview questions using Gemini AI.

        Args:
            user_id: User ID
            job_title: Target job title
            company_name: Optional company name
            job_description: Optional job description
            resume_id: Optional resume ID for personalization
            job_id: Optional saved job ID
            interview_type: Type of interview (behavioral, technical, mixed)
            difficulty: Difficulty level (entry, mid, senior)
            question_count: Number of questions to generate (1-10)
            focus_areas: List of areas to focus on
            language: Response language (ko, en)

        Returns:
            Interview object with generated questions

        Raises:
            ValueError: If invalid parameters
            Exception: If generation fails
        """
        start_time = time.time()

        logger.info(
            "interview_generation_started",
            operation="generate_interview",
            user_id=f"user-{user_id}",
            job_title=scrub_all_pii(job_title),
            interview_type=interview_type,
            difficulty=difficulty,
            question_count=question_count,
        )

        try:
            # Validate parameters
            if interview_type not in ["behavioral", "technical", "mixed"]:
                interview_type = self.DEFAULT_INTERVIEW_TYPE
            if difficulty not in ["entry", "mid", "senior"]:
                difficulty = self.DEFAULT_DIFFICULTY
            question_count = max(1, min(10, question_count))

            # Get resume data if provided
            resume_summary = None
            if resume_id:
                resume = self._get_user_resume(user_id, resume_id)
                if resume and resume.analysis_result:
                    resume_summary = self._extract_resume_summary(resume)

            # Get job data if provided
            if job_id and not job_description:
                job = self.db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
                if job:
                    job_description = job.description
                    if not company_name:
                        company_name = job.company

            # Create interview record
            interview = Interview(
                user_id=user_id,
                resume_id=resume_id,
                job_id=job_id,
                job_title=job_title,
                company_name=company_name,
                job_description=job_description,
                status="generating",
                config={
                    "interview_type": interview_type,
                    "difficulty": difficulty,
                    "question_count": question_count,
                    "focus_areas": focus_areas or [],
                    "language": language,
                },
            )
            self.db.add(interview)
            self.db.commit()
            self.db.refresh(interview)

            logger.info(
                "interview_record_created",
                operation="generate_interview",
                interview_id=interview.id,
            )

            # Generate questions with Gemini
            try:
                questions = await self._generate_questions_with_gemini(
                    job_title=job_title,
                    company_name=company_name,
                    job_description=job_description,
                    resume_summary=resume_summary,
                    interview_type=interview_type,
                    difficulty=difficulty,
                    question_count=question_count,
                    focus_areas=focus_areas,
                    language=language,
                )

                # Update interview with questions
                interview.questions = questions
                interview.status = "ready"
                self.db.commit()

                duration_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    "interview_generation_completed",
                    operation="generate_interview",
                    interview_id=interview.id,
                    question_count=len(questions),
                    duration_ms=duration_ms,
                )

            except Exception as e:
                interview.status = "failed"
                interview.error_message = str(e)
                self.db.commit()
                raise

            return interview

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "interview_generation_failed",
                operation="generate_interview",
                error=str(e),
                duration_ms=duration_ms,
                exc_info=True,
            )
            raise

    async def evaluate_answer(
        self,
        interview_id: int,
        user_id: int,
        question_id: int,
        answer_text: str,
        answer_audio_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a user's answer to an interview question.

        Args:
            interview_id: Interview session ID
            user_id: User ID
            question_id: Question ID within the interview
            answer_text: User's answer text
            answer_audio_url: Optional audio recording URL

        Returns:
            Evaluation result with score and feedback

        Raises:
            ValueError: If interview or question not found
            Exception: If evaluation fails
        """
        start_time = time.time()

        logger.info(
            "answer_evaluation_started",
            operation="evaluate_answer",
            interview_id=interview_id,
            question_id=question_id,
        )

        try:
            # Get interview
            interview = self.db.query(Interview).filter(
                Interview.id == interview_id,
                Interview.user_id == user_id,
            ).first()

            if not interview:
                raise ValueError(f"Interview {interview_id} not found")

            if not interview.questions:
                raise ValueError("Interview has no questions")

            # Find the question
            question = None
            for q in interview.questions:
                if q.get("id") == question_id:
                    question = q
                    break

            if not question:
                raise ValueError(f"Question {question_id} not found in interview")

            # Update status if first answer
            if interview.status == "ready":
                interview.status = "in_progress"
                interview.started_at = datetime.utcnow()

            # Evaluate with Gemini
            evaluation = await self._evaluate_with_gemini(
                question=question,
                answer_text=answer_text,
                job_title=interview.job_title,
                language=interview.config.get("language", "ko"),
            )

            # Store the answer
            answer_record = {
                "question_id": question_id,
                "answer_text": answer_text,
                "answer_audio_url": answer_audio_url,
                "answered_at": datetime.utcnow().isoformat(),
                "evaluation": evaluation,
            }

            # Update or append answer
            answers = interview.answers or []
            existing_idx = next(
                (i for i, a in enumerate(answers) if a.get("question_id") == question_id),
                None
            )
            if existing_idx is not None:
                answers[existing_idx] = answer_record
            else:
                answers.append(answer_record)

            interview.answers = answers
            interview.completed_questions = len(answers)

            # Check if all questions answered
            if len(answers) >= len(interview.questions):
                interview.status = "completed"
                interview.completed_at = datetime.utcnow()
                interview.total_score = interview.calculate_total_score()

            self.db.commit()

            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "answer_evaluation_completed",
                operation="evaluate_answer",
                interview_id=interview_id,
                question_id=question_id,
                score=evaluation.get("score"),
                duration_ms=duration_ms,
            )

            return {
                "question_id": question_id,
                "evaluation": evaluation,
                "progress": interview.get_progress(),
                "is_completed": interview.status == "completed",
                "total_score": interview.total_score if interview.status == "completed" else None,
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "answer_evaluation_failed",
                operation="evaluate_answer",
                error=str(e),
                duration_ms=duration_ms,
                exc_info=True,
            )
            raise

    async def _generate_questions_with_gemini(
        self,
        job_title: str,
        company_name: Optional[str],
        job_description: Optional[str],
        resume_summary: Optional[Dict[str, Any]],
        interview_type: str,
        difficulty: str,
        question_count: int,
        focus_areas: Optional[List[str]],
        language: str,
    ) -> List[Dict[str, Any]]:
        """Generate interview questions using Gemini AI."""

        # Build the prompt
        lang_instruction = "한국어로 답변해주세요." if language == "ko" else "Please respond in English."

        difficulty_desc = {
            "entry": "신입/주니어 레벨 (1-2년 경력)",
            "mid": "중급 레벨 (3-5년 경력)",
            "senior": "시니어 레벨 (6년 이상 경력)",
        }.get(difficulty, "중급 레벨")

        type_desc = {
            "behavioral": "행동 면접 질문 (과거 경험, 상황 대처)",
            "technical": "기술 면접 질문 (기술 지식, 문제 해결)",
            "mixed": "행동 면접과 기술 면접 혼합",
        }.get(interview_type, "혼합")

        prompt = f"""당신은 전문 면접관입니다. 다음 조건에 맞는 면접 질문을 {question_count}개 생성해주세요.

{lang_instruction}

## 채용 정보
- 직무: {job_title}
- 회사: {company_name or '미지정'}
- 난이도: {difficulty_desc}
- 면접 유형: {type_desc}

"""

        if job_description:
            prompt += f"""## 직무 설명
{job_description[:2000]}

"""

        if resume_summary:
            prompt += f"""## 지원자 이력서 요약
- 기술 스택: {', '.join(resume_summary.get('skills', [])[:10])}
- 경력: {resume_summary.get('experience_summary', 'N/A')}

"""

        if focus_areas:
            prompt += f"""## 집중 영역
{', '.join(focus_areas)}

"""

        prompt += """## 출력 형식
다음 JSON 형식으로 정확히 출력해주세요:

```json
[
  {
    "id": 1,
    "question": "질문 내용",
    "type": "behavioral" 또는 "technical" 또는 "situational",
    "difficulty": 1-5 (숫자),
    "expected_topics": ["예상 답변 주제1", "주제2"],
    "time_limit_seconds": 120,
    "tips": "답변 팁"
  }
]
```

질문은 구체적이고 실무 중심으로 작성해주세요. STAR 기법으로 답변할 수 있는 질문을 포함해주세요.
"""

        # Call Gemini
        response = await self.gemini_client.generate_content(prompt)

        # Parse JSON response
        try:
            # Extract JSON from response
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            questions = json.loads(response_text)

            # Validate and normalize questions
            validated_questions = []
            for i, q in enumerate(questions[:question_count], 1):
                validated_questions.append({
                    "id": i,
                    "question": q.get("question", ""),
                    "type": q.get("type", "behavioral"),
                    "difficulty": min(5, max(1, int(q.get("difficulty", 3)))),
                    "expected_topics": q.get("expected_topics", []),
                    "time_limit_seconds": q.get("time_limit_seconds", 120),
                    "tips": q.get("tips", ""),
                })

            return validated_questions

        except json.JSONDecodeError as e:
            logger.error(
                "question_json_parse_failed",
                operation="generate_questions",
                error=str(e),
            )
            # Return fallback questions
            return self._get_fallback_questions(job_title, question_count, language)

    async def _evaluate_with_gemini(
        self,
        question: Dict[str, Any],
        answer_text: str,
        job_title: str,
        language: str,
    ) -> Dict[str, Any]:
        """Evaluate an answer using Gemini AI."""

        lang_instruction = "한국어로 답변해주세요." if language == "ko" else "Please respond in English."

        prompt = f"""당신은 전문 면접관입니다. 다음 면접 답변을 평가해주세요.

{lang_instruction}

## 면접 질문
{question.get('question', '')}

## 예상 답변 주제
{', '.join(question.get('expected_topics', []))}

## 직무
{job_title}

## 지원자 답변
{answer_text}

## 평가 기준
1. 답변의 구체성 (예시, 수치, 경험 포함 여부)
2. STAR 기법 활용 (Situation, Task, Action, Result)
3. 직무 관련성
4. 논리적 구조
5. 커뮤니케이션 명확성

## 출력 형식
다음 JSON 형식으로 정확히 출력해주세요:

```json
{{
  "score": 0-100 (숫자),
  "strengths": ["강점1", "강점2"],
  "improvements": ["개선점1", "개선점2"],
  "feedback": "상세 피드백 (2-3문장)",
  "model_answer": "모범 답변 예시 (3-4문장)"
}}
```
"""

        # Call Gemini
        response = await self.gemini_client.generate_content(prompt)

        # Parse JSON response
        try:
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            evaluation = json.loads(response_text)

            # Normalize evaluation
            return {
                "score": min(100, max(0, int(evaluation.get("score", 50)))),
                "strengths": evaluation.get("strengths", [])[:5],
                "improvements": evaluation.get("improvements", [])[:5],
                "feedback": evaluation.get("feedback", "평가를 완료했습니다."),
                "model_answer": evaluation.get("model_answer", ""),
            }

        except json.JSONDecodeError as e:
            logger.error(
                "evaluation_json_parse_failed",
                operation="evaluate_answer",
                error=str(e),
            )
            return {
                "score": 60,
                "strengths": ["답변을 제출했습니다"],
                "improvements": ["더 구체적인 예시를 들어주세요"],
                "feedback": "답변을 평가했습니다. 더 구체적인 경험과 수치를 포함하면 좋겠습니다.",
                "model_answer": "",
            }

    def _get_user_resume(self, user_id: int, resume_id: int) -> Optional[Resume]:
        """Get user's resume."""
        return self.db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == user_id,
        ).first()

    def _extract_resume_summary(self, resume: Resume) -> Dict[str, Any]:
        """Extract summary from resume analysis."""
        if not resume.analysis_result:
            return {}

        analysis = resume.analysis_result
        return {
            "skills": analysis.get("skills", []),
            "experience_summary": analysis.get("experience_summary", ""),
            "education": analysis.get("education", []),
            "strengths": analysis.get("strengths", []),
        }

    def _get_fallback_questions(
        self,
        job_title: str,
        count: int,
        language: str,
    ) -> List[Dict[str, Any]]:
        """Get fallback questions if Gemini fails."""

        if language == "ko":
            fallback = [
                {
                    "question": f"{job_title} 직무에 지원하게 된 동기가 무엇인가요?",
                    "type": "behavioral",
                    "expected_topics": ["동기", "열정", "경력 목표"],
                },
                {
                    "question": "가장 도전적이었던 프로젝트 경험을 말씀해주세요.",
                    "type": "behavioral",
                    "expected_topics": ["문제 해결", "팀워크", "성과"],
                },
                {
                    "question": "팀에서 갈등이 발생했을 때 어떻게 해결하셨나요?",
                    "type": "situational",
                    "expected_topics": ["커뮤니케이션", "협업", "리더십"],
                },
                {
                    "question": "본인의 강점과 약점은 무엇이라고 생각하시나요?",
                    "type": "behavioral",
                    "expected_topics": ["자기인식", "성장", "개선"],
                },
                {
                    "question": "5년 후 본인의 모습을 어떻게 그리고 계신가요?",
                    "type": "behavioral",
                    "expected_topics": ["경력 계획", "목표", "성장"],
                },
            ]
        else:
            fallback = [
                {
                    "question": f"Why are you interested in the {job_title} position?",
                    "type": "behavioral",
                    "expected_topics": ["motivation", "passion", "career goals"],
                },
                {
                    "question": "Tell me about your most challenging project experience.",
                    "type": "behavioral",
                    "expected_topics": ["problem solving", "teamwork", "results"],
                },
                {
                    "question": "How do you handle conflicts within a team?",
                    "type": "situational",
                    "expected_topics": ["communication", "collaboration", "leadership"],
                },
                {
                    "question": "What are your strengths and weaknesses?",
                    "type": "behavioral",
                    "expected_topics": ["self-awareness", "growth", "improvement"],
                },
                {
                    "question": "Where do you see yourself in 5 years?",
                    "type": "behavioral",
                    "expected_topics": ["career plan", "goals", "growth"],
                },
            ]

        questions = []
        for i, q in enumerate(fallback[:count], 1):
            questions.append({
                "id": i,
                "question": q["question"],
                "type": q["type"],
                "difficulty": 3,
                "expected_topics": q["expected_topics"],
                "time_limit_seconds": 120,
                "tips": "",
            })

        return questions

    def get_interview(self, interview_id: int, user_id: int) -> Optional[Interview]:
        """Get interview by ID."""
        return self.db.query(Interview).filter(
            Interview.id == interview_id,
            Interview.user_id == user_id,
        ).first()

    def get_user_interviews(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Interview]:
        """Get user's interview history."""
        return self.db.query(Interview).filter(
            Interview.user_id == user_id,
        ).order_by(Interview.created_at.desc()).offset(offset).limit(limit).all()
