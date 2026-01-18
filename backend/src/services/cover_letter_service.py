"""
Cover Letter service for generation and management.

Constitution Compliance:
- Principle II: API Resilience - Retry logic for Gemini calls
- Principle III: User Data Privacy - PII scrubbing in logs
- Principle V: Code Quality - Structured logging throughout

T039: Cover Letter service
T040-T041: Gemini cover letter generation prompts
"""

import time
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy.orm import Session

from src.config import settings
from src.models.cover_letter import CoverLetter
from src.models.resume import Resume
from src.services.gemini_client import GeminiClient
from src.utils.logging_config import get_logger
from src.utils.privacy import scrub_all_pii

logger = get_logger(__name__)


class CoverLetterService:
    """
    Service for handling cover letter operations.

    T039: Cover letter generation and management
    T040-T041: Gemini prompt engineering for cover letters
    """

    # Default generation parameters
    DEFAULT_TONE = "professional"
    DEFAULT_LENGTH = "medium"

    def __init__(self, db: Session):
        """
        Initialize cover letter service.

        Args:
            db: Database session
        """
        self.db = db
        self.gemini_client = GeminiClient()

    async def generate_cover_letter(
        self,
        user_id: int,
        job_title: str,
        company_name: str,
        job_description: Optional[str] = None,
        resume_id: Optional[int] = None,
        tone: str = "professional",
        length: str = "medium",
        focus_areas: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None,
    ) -> CoverLetter:
        """
        Generate a cover letter using Gemini AI.

        T039: Complete workflow for cover letter generation
        T040-T041: Uses optimized prompts for cover letter creation

        Args:
            user_id: User ID
            job_title: Target job title
            company_name: Target company name
            job_description: Optional job posting text
            resume_id: Optional resume ID to use for personalization
            tone: Writing tone (professional, casual, enthusiastic)
            length: Length preference (short, medium, long)
            focus_areas: List of areas to emphasize
            custom_instructions: Additional user instructions

        Returns:
            CoverLetter object with generated content

        Raises:
            ValueError: If invalid parameters
            Exception: If generation fails
        """
        start_time = time.time()

        logger.info(
            "cover_letter_generation_started",
            operation="generate_cover_letter",
            user_id=f"user-{user_id}",
            job_title=scrub_all_pii(job_title),
            company_name=scrub_all_pii(company_name),
            has_job_description=bool(job_description),
            resume_id=resume_id,
            tone=tone,
            length=length,
        )

        try:
            # Validate tone and length
            if tone not in ["professional", "casual", "enthusiastic"]:
                tone = self.DEFAULT_TONE
            if length not in ["short", "medium", "long"]:
                length = self.DEFAULT_LENGTH

            # Get resume data if provided
            resume_summary = None
            if resume_id:
                resume = self._get_user_resume(user_id, resume_id)
                if resume and resume.analysis_result:
                    resume_summary = self._extract_resume_summary(resume)

            # Create cover letter record
            cover_letter = CoverLetter(
                user_id=user_id,
                resume_id=resume_id,
                job_title=job_title,
                company_name=company_name,
                job_description=job_description,
                status="generating",
                generation_params={
                    "tone": tone,
                    "length": length,
                    "focus_areas": focus_areas or [],
                    "custom_instructions": custom_instructions,
                    "resume_summary": resume_summary,
                },
            )
            self.db.add(cover_letter)
            self.db.commit()
            self.db.refresh(cover_letter)

            logger.info(
                "cover_letter_record_created",
                operation="generate_cover_letter",
                user_id=f"user-{user_id}",
                cover_letter_id=cover_letter.id,
            )

            # Generate content with Gemini
            try:
                generated_content = self._generate_with_gemini(
                    job_title=job_title,
                    company_name=company_name,
                    job_description=job_description,
                    resume_summary=resume_summary,
                    tone=tone,
                    length=length,
                    focus_areas=focus_areas,
                    custom_instructions=custom_instructions,
                    user_id=user_id,
                )

                cover_letter.content = generated_content
                cover_letter.status = "generated"
                cover_letter.generated_at = datetime.utcnow()
                cover_letter.generation_params["model_used"] = self.gemini_client.model_name
                cover_letter.generation_params["generated_at"] = time.time()
                self.db.commit()

                logger.info(
                    "cover_letter_generation_success",
                    operation="generate_cover_letter",
                    user_id=f"user-{user_id}",
                    cover_letter_id=cover_letter.id,
                    word_count=cover_letter.get_word_count(),
                )

            except Exception as e:
                cover_letter.status = "failed"
                cover_letter.error_message = f"Generation failed: {str(e)}"
                self.db.commit()
                raise

            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "cover_letter_generation_completed",
                operation="generate_cover_letter",
                user_id=f"user-{user_id}",
                cover_letter_id=cover_letter.id,
                duration_ms=duration_ms,
                status=cover_letter.status,
            )

            # Performance check (SC-001: <60 seconds)
            if duration_ms > 60000:
                logger.warning(
                    "cover_letter_generation_slow",
                    operation="generate_cover_letter",
                    duration_ms=duration_ms,
                    threshold_ms=60000,
                )

            return cover_letter

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "cover_letter_generation_failed",
                operation="generate_cover_letter",
                user_id=f"user-{user_id}",
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            raise

    def _generate_with_gemini(
        self,
        job_title: str,
        company_name: str,
        job_description: Optional[str],
        resume_summary: Optional[Dict[str, Any]],
        tone: str,
        length: str,
        focus_areas: Optional[List[str]],
        custom_instructions: Optional[str],
        user_id: int,
    ) -> str:
        """
        Generate cover letter content using Gemini.

        T040-T041: Prompt engineering for cover letter generation

        Returns:
            Generated cover letter text
        """
        prompt = self._build_cover_letter_prompt(
            job_title=job_title,
            company_name=company_name,
            job_description=job_description,
            resume_summary=resume_summary,
            tone=tone,
            length=length,
            focus_areas=focus_areas,
            custom_instructions=custom_instructions,
        )

        logger.info(
            "gemini_cover_letter_request",
            operation="generate_with_gemini",
            user_id=f"user-{user_id}",
            prompt_length=len(prompt),
        )

        # Call Gemini API
        response = self.gemini_client.model.generate_content(prompt)

        # Clean response
        content = response.text.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        return content

    def _build_cover_letter_prompt(
        self,
        job_title: str,
        company_name: str,
        job_description: Optional[str],
        resume_summary: Optional[Dict[str, Any]],
        tone: str,
        length: str,
        focus_areas: Optional[List[str]],
        custom_instructions: Optional[str],
    ) -> str:
        """
        Build prompt for cover letter generation.

        T040-T041: Optimized prompt engineering
        """
        # Length guidelines
        length_guide = {
            "short": "250-350 words (3 paragraphs)",
            "medium": "350-500 words (4 paragraphs)",
            "long": "500-700 words (5-6 paragraphs)",
        }

        # Tone guidelines
        tone_guide = {
            "professional": "formal, polished, and business-appropriate",
            "casual": "friendly yet professional, conversational but respectful",
            "enthusiastic": "energetic and passionate, showing genuine excitement",
        }

        prompt = f"""You are an expert career coach and professional writer. Write a compelling cover letter for the following job application.

## Job Details
- **Position**: {job_title}
- **Company**: {company_name}
"""

        if job_description:
            prompt += f"""
## Job Description
{job_description}
"""

        if resume_summary:
            prompt += f"""
## Candidate Background (from resume)
- **Skills**: {', '.join(resume_summary.get('skills', [])[:15])}
- **Experience**: {resume_summary.get('experience_years', 0)} years
- **Strengths**: {'; '.join(resume_summary.get('strengths', [])[:3])}
- **Suitable Roles**: {', '.join(resume_summary.get('suitable_roles', [])[:3])}
"""

        prompt += f"""
## Writing Requirements
- **Tone**: {tone_guide.get(tone, tone_guide['professional'])}
- **Length**: {length_guide.get(length, length_guide['medium'])}
"""

        if focus_areas:
            prompt += f"- **Focus Areas**: {', '.join(focus_areas)}\n"

        if custom_instructions:
            prompt += f"- **Additional Instructions**: {custom_instructions}\n"

        prompt += """
## Structure Guidelines
1. **Opening**: Hook the reader with a compelling introduction that shows enthusiasm for the role
2. **Body**: Highlight relevant skills and experiences that match the job requirements
3. **Connection**: Show understanding of the company and how you can contribute
4. **Closing**: Strong call to action expressing interest in an interview

## Important Rules
- Write in first person
- Be specific and use concrete examples when possible
- Avoid generic phrases like "I am writing to apply for..."
- Show personality while maintaining professionalism
- Tailor content specifically to this company and role
- Do NOT include placeholder text like [Your Name] - write complete sentences
- Output ONLY the cover letter text, no additional commentary

Write the cover letter now:
"""
        return prompt

    def _get_user_resume(self, user_id: int, resume_id: int) -> Optional[Resume]:
        """Get user's resume by ID."""
        return (
            self.db.query(Resume)
            .filter(
                Resume.id == resume_id,
                Resume.user_id == user_id,
                Resume.status == "analyzed",
            )
            .first()
        )

    def _extract_resume_summary(self, resume: Resume) -> Dict[str, Any]:
        """Extract relevant summary from resume analysis."""
        if not resume.analysis_result:
            return {}

        return {
            "skills": resume.analysis_result.get("skills", []),
            "strengths": resume.analysis_result.get("strengths", []),
            "suitable_roles": resume.analysis_result.get("suitable_roles", []),
            "experience_years": resume.analysis_result.get("experience_years", 0),
        }

    async def update_cover_letter(
        self,
        cover_letter_id: int,
        user_id: int,
        content: Optional[str] = None,
        regenerate: bool = False,
    ) -> CoverLetter:
        """
        Update or regenerate a cover letter.

        T043: Cover letter update/regenerate endpoint

        Args:
            cover_letter_id: Cover letter ID
            user_id: User ID
            content: New content (for manual edit)
            regenerate: If True, regenerate with AI

        Returns:
            Updated CoverLetter object
        """
        cover_letter = self.get_cover_letter_by_id(cover_letter_id, user_id)
        if not cover_letter:
            raise ValueError(f"Cover letter {cover_letter_id} not found")

        if regenerate:
            # Regenerate with same parameters
            params = cover_letter.generation_params or {}
            generated_content = self._generate_with_gemini(
                job_title=cover_letter.job_title,
                company_name=cover_letter.company_name,
                job_description=cover_letter.job_description,
                resume_summary=params.get("resume_summary"),
                tone=params.get("tone", self.DEFAULT_TONE),
                length=params.get("length", self.DEFAULT_LENGTH),
                focus_areas=params.get("focus_areas"),
                custom_instructions=params.get("custom_instructions"),
                user_id=user_id,
            )
            cover_letter.content = generated_content
            cover_letter.version += 1
            cover_letter.generated_at = datetime.utcnow()

            logger.info(
                "cover_letter_regenerated",
                operation="update_cover_letter",
                user_id=f"user-{user_id}",
                cover_letter_id=cover_letter_id,
                new_version=cover_letter.version,
            )
        elif content:
            # Manual edit
            cover_letter.content = content
            cover_letter.version += 1

            logger.info(
                "cover_letter_manually_edited",
                operation="update_cover_letter",
                user_id=f"user-{user_id}",
                cover_letter_id=cover_letter_id,
                new_version=cover_letter.version,
            )

        self.db.commit()
        self.db.refresh(cover_letter)
        return cover_letter

    def get_cover_letter_by_id(self, cover_letter_id: int, user_id: int) -> Optional[CoverLetter]:
        """Get cover letter by ID for specific user."""
        return (
            self.db.query(CoverLetter)
            .filter(
                CoverLetter.id == cover_letter_id,
                CoverLetter.user_id == user_id,
            )
            .first()
        )

    def get_user_cover_letters(self, user_id: int, limit: int = 20) -> List[CoverLetter]:
        """Get all cover letters for a user."""
        return (
            self.db.query(CoverLetter)
            .filter(CoverLetter.user_id == user_id)
            .order_by(CoverLetter.created_at.desc())
            .limit(limit)
            .all()
        )
