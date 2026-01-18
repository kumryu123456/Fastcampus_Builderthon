"""
Job Discovery service for search and AI-powered recommendations.

Constitution Compliance:
- Principle II: API Resilience - Retry logic for Gemini calls
- Principle III: User Data Privacy - PII scrubbing in logs
- Principle V: Code Quality - Structured logging throughout

T054: Job service for search and recommendations
T055-T056: Gemini job matching prompts
"""

import time
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.config import settings
from src.models.job import Job
from src.models.resume import Resume
from src.services.gemini_client import GeminiClient
from src.utils.logging_config import get_logger
from src.utils.privacy import scrub_all_pii

logger = get_logger(__name__)


class JobService:
    """
    Service for job discovery and AI-powered matching.

    T054: Job search and recommendation logic
    T055-T056: Gemini integration for job matching
    """

    def __init__(self, db: Session):
        """Initialize job service."""
        self.db = db
        self.gemini_client = GeminiClient()

    async def search_jobs(
        self,
        user_id: int,
        query: Optional[str] = None,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        limit: int = 20,
    ) -> List[Job]:
        """
        Search jobs based on criteria.

        For MVP, this searches saved jobs in the database.
        In production, this would integrate with job boards APIs.

        Args:
            user_id: User ID
            query: Search query (title/company)
            location: Location filter
            job_type: Job type filter
            experience_level: Experience level filter
            limit: Maximum results

        Returns:
            List of matching jobs
        """
        logger.info(
            "job_search_started",
            operation="search_jobs",
            user_id=f"user-{user_id}",
            query=scrub_all_pii(query) if query else None,
            location=location,
            job_type=job_type,
        )

        # Build query
        db_query = self.db.query(Job).filter(Job.user_id == user_id)

        if query:
            search_term = f"%{query}%"
            db_query = db_query.filter(
                or_(
                    Job.title.ilike(search_term),
                    Job.company.ilike(search_term),
                    Job.description.ilike(search_term),
                )
            )

        if location:
            db_query = db_query.filter(Job.location.ilike(f"%{location}%"))

        if job_type:
            db_query = db_query.filter(Job.job_type == job_type)

        if experience_level:
            db_query = db_query.filter(Job.experience_level == experience_level)

        # Order by match score (if available) then by created date
        jobs = (
            db_query
            .order_by(Job.match_score.desc().nullslast(), Job.created_at.desc())
            .limit(limit)
            .all()
        )

        logger.info(
            "job_search_completed",
            operation="search_jobs",
            user_id=f"user-{user_id}",
            results_count=len(jobs),
        )

        return jobs

    async def get_job_recommendations(
        self,
        user_id: int,
        resume_id: int,
        job_preferences: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get AI-powered job recommendations based on resume.

        T055-T056: Uses Gemini to generate job recommendations

        Args:
            user_id: User ID
            resume_id: Resume ID to base recommendations on
            job_preferences: Optional preferences (location, job_type, etc.)
            limit: Maximum recommendations

        Returns:
            List of job recommendations with match analysis
        """
        start_time = time.time()

        logger.info(
            "job_recommendations_started",
            operation="get_job_recommendations",
            user_id=f"user-{user_id}",
            resume_id=resume_id,
        )

        # Get resume analysis
        resume = self._get_user_resume(user_id, resume_id)
        if not resume or not resume.analysis_result:
            raise ValueError(f"Resume {resume_id} not found or not analyzed")

        try:
            # Generate recommendations using Gemini
            recommendations = self._generate_recommendations_with_gemini(
                resume=resume,
                preferences=job_preferences,
                limit=limit,
                user_id=user_id,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "job_recommendations_completed",
                operation="get_job_recommendations",
                user_id=f"user-{user_id}",
                recommendations_count=len(recommendations),
                duration_ms=duration_ms,
            )

            # Performance check (<30 seconds)
            if duration_ms > 30000:
                logger.warning(
                    "job_recommendations_slow",
                    operation="get_job_recommendations",
                    duration_ms=duration_ms,
                    threshold_ms=30000,
                )

            return recommendations

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "job_recommendations_failed",
                operation="get_job_recommendations",
                user_id=f"user-{user_id}",
                duration_ms=duration_ms,
                error=str(e),
                exc_info=True,
            )
            raise

    def _generate_recommendations_with_gemini(
        self,
        resume: Resume,
        preferences: Optional[Dict[str, Any]],
        limit: int,
        user_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate job recommendations using Gemini AI.

        T055-T056: Prompt engineering for job recommendations
        """
        prompt = self._build_recommendation_prompt(resume, preferences, limit)

        logger.info(
            "gemini_job_recommendation_request",
            operation="generate_recommendations",
            user_id=f"user-{user_id}",
            prompt_length=len(prompt),
        )

        # Call Gemini API
        response = self.gemini_client.model.generate_content(prompt)

        # Parse response
        recommendations = self._parse_recommendations_response(response.text)

        return recommendations

    def _build_recommendation_prompt(
        self,
        resume: Resume,
        preferences: Optional[Dict[str, Any]],
        limit: int,
    ) -> str:
        """Build prompt for job recommendations."""
        analysis = resume.analysis_result

        prompt = f"""You are an expert career advisor and job matching specialist. Based on the candidate's resume analysis, recommend suitable job positions.

## Candidate Profile
- **Skills**: {', '.join(analysis.get('skills', [])[:20])}
- **Experience**: {analysis.get('experience_years', 0)} years
- **Strengths**: {'; '.join(analysis.get('strengths', [])[:3])}
- **Suitable Roles (from analysis)**: {', '.join(analysis.get('suitable_roles', [])[:5])}
"""

        if preferences:
            prompt += f"""
## Job Preferences
- **Preferred Location**: {preferences.get('location', 'Any')}
- **Job Type**: {preferences.get('job_type', 'Any')}
- **Experience Level**: {preferences.get('experience_level', 'Any')}
- **Industry**: {preferences.get('industry', 'Any')}
"""

        prompt += f"""
## Task
Generate {limit} specific job recommendations that would be a great match for this candidate.

For each recommendation, provide:
1. A specific job title
2. Type of company (startup, large corporation, etc.)
3. Industry
4. Match score (0-100)
5. Why this role is a good match
6. Skills that match
7. Skills the candidate might need to develop

## Output Format
Return ONLY a valid JSON array with this structure (no markdown, no additional text):
[
  {{
    "title": "Job Title",
    "company_type": "Startup / Mid-size / Enterprise",
    "industry": "Industry name",
    "location": "Recommended location or Remote",
    "job_type": "full-time / part-time / contract / internship",
    "experience_level": "entry / mid / senior",
    "match_score": 85,
    "match_reason": "Brief explanation of why this is a good match",
    "matching_skills": ["skill1", "skill2"],
    "skills_to_develop": ["skill3"],
    "sample_companies": ["Company1", "Company2", "Company3"]
  }}
]

Important:
- Be specific with job titles (not generic)
- Match scores should be realistic (70-95 range for good matches)
- Consider the candidate's experience level
- Provide actionable recommendations
"""
        return prompt

    def _parse_recommendations_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse Gemini response into recommendations list."""
        try:
            # Clean response
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            # Parse JSON
            recommendations = json.loads(text)

            if not isinstance(recommendations, list):
                recommendations = [recommendations]

            # Validate and normalize each recommendation
            validated = []
            for rec in recommendations:
                validated.append({
                    "title": rec.get("title", "Unknown Position"),
                    "company_type": rec.get("company_type", "Various"),
                    "industry": rec.get("industry", "Technology"),
                    "location": rec.get("location", "Various"),
                    "job_type": rec.get("job_type", "full-time"),
                    "experience_level": rec.get("experience_level", "mid"),
                    "match_score": min(100, max(0, rec.get("match_score", 70))),
                    "match_reason": rec.get("match_reason", "Good skill match"),
                    "matching_skills": rec.get("matching_skills", []),
                    "skills_to_develop": rec.get("skills_to_develop", []),
                    "sample_companies": rec.get("sample_companies", []),
                })

            return validated

        except json.JSONDecodeError as e:
            logger.error(
                "recommendations_parse_failed",
                operation="parse_recommendations",
                error=str(e),
                response_preview=response_text[:200],
            )
            # Return fallback
            return [{
                "title": "Software Engineer",
                "company_type": "Various",
                "industry": "Technology",
                "location": "Various",
                "job_type": "full-time",
                "experience_level": "mid",
                "match_score": 75,
                "match_reason": "Based on your technical skills",
                "matching_skills": [],
                "skills_to_develop": [],
                "sample_companies": [],
                "parse_error": str(e),
            }]

    async def analyze_job_match(
        self,
        user_id: int,
        resume_id: int,
        job_title: str,
        job_description: str,
        company: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze how well a specific job matches the resume.

        Args:
            user_id: User ID
            resume_id: Resume ID
            job_title: Job title
            job_description: Job description text
            company: Optional company name

        Returns:
            Match analysis with score and details
        """
        start_time = time.time()

        logger.info(
            "job_match_analysis_started",
            operation="analyze_job_match",
            user_id=f"user-{user_id}",
            resume_id=resume_id,
            job_title=scrub_all_pii(job_title),
        )

        # Get resume
        resume = self._get_user_resume(user_id, resume_id)
        if not resume or not resume.analysis_result:
            raise ValueError(f"Resume {resume_id} not found or not analyzed")

        try:
            # Analyze match using Gemini
            analysis = self._analyze_match_with_gemini(
                resume=resume,
                job_title=job_title,
                job_description=job_description,
                company=company,
                user_id=user_id,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "job_match_analysis_completed",
                operation="analyze_job_match",
                user_id=f"user-{user_id}",
                match_score=analysis.get("match_score"),
                duration_ms=duration_ms,
            )

            return analysis

        except Exception as e:
            logger.error(
                "job_match_analysis_failed",
                operation="analyze_job_match",
                user_id=f"user-{user_id}",
                error=str(e),
                exc_info=True,
            )
            raise

    def _analyze_match_with_gemini(
        self,
        resume: Resume,
        job_title: str,
        job_description: str,
        company: Optional[str],
        user_id: int,
    ) -> Dict[str, Any]:
        """Analyze job match using Gemini."""
        analysis = resume.analysis_result

        prompt = f"""You are an expert job matching specialist. Analyze how well this candidate matches the job posting.

## Candidate Profile
- **Skills**: {', '.join(analysis.get('skills', [])[:20])}
- **Experience**: {analysis.get('experience_years', 0)} years
- **Strengths**: {'; '.join(analysis.get('strengths', [])[:3])}

## Job Posting
- **Title**: {job_title}
- **Company**: {company or 'Not specified'}
- **Description**:
{job_description[:2000]}

## Task
Analyze the match and provide:
1. Overall match score (0-100)
2. Skills that match the job requirements
3. Skills the candidate is missing
4. Strengths relevant to this role
5. Areas where the candidate could improve
6. Overall recommendation

## Output Format
Return ONLY valid JSON (no markdown):
{{
  "match_score": 85,
  "match_level": "Strong Match" | "Good Match" | "Moderate Match" | "Weak Match",
  "matching_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3", "skill4"],
  "relevant_strengths": ["strength1"],
  "improvement_areas": ["area1"],
  "recommendation": "Brief recommendation about applying",
  "key_requirements_met": ["req1", "req2"],
  "key_requirements_missing": ["req3"]
}}
"""

        response = self.gemini_client.model.generate_content(prompt)

        # Parse response
        try:
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            result = json.loads(text)
            result["analyzed_at"] = time.time()
            result["model_used"] = self.gemini_client.model_name
            return result

        except json.JSONDecodeError as e:
            logger.error(
                "match_analysis_parse_failed",
                operation="analyze_match",
                error=str(e),
            )
            return {
                "match_score": 70,
                "match_level": "Moderate Match",
                "matching_skills": [],
                "missing_skills": [],
                "relevant_strengths": [],
                "improvement_areas": [],
                "recommendation": "Please review the job requirements carefully.",
                "parse_error": str(e),
            }

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

    async def save_job(
        self,
        user_id: int,
        title: str,
        company: str,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
        source: str = "manual",
    ) -> Job:
        """Save a job to user's list."""
        job = Job(
            user_id=user_id,
            title=title,
            company=company,
            location=location,
            job_type=job_type,
            description=description,
            url=url,
            source=source,
            is_saved=True,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        logger.info(
            "job_saved",
            operation="save_job",
            user_id=f"user-{user_id}",
            job_id=job.id,
        )

        return job

    def get_saved_jobs(self, user_id: int, limit: int = 50) -> List[Job]:
        """Get user's saved jobs."""
        return (
            self.db.query(Job)
            .filter(Job.user_id == user_id, Job.is_saved == True)
            .order_by(Job.match_score.desc().nullslast(), Job.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_job_by_id(self, job_id: int, user_id: int) -> Optional[Job]:
        """Get job by ID for specific user."""
        return (
            self.db.query(Job)
            .filter(Job.id == job_id, Job.user_id == user_id)
            .first()
        )
