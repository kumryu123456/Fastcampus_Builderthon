"""
Gemini API client for PathPilot.

Constitution Compliance:
- Principle II: API Resilience - Retry logic with exponential backoff
- Principle V: Code Quality - Structured logging for all API calls
- Performance: <60 seconds for analysis (SC-001)

T023: Gemini API client for resume analysis with structured output
T025: Prompt engineering for resume analysis
"""

import json
import time
from typing import Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from src.config import settings
from src.api.retry_wrapper import retry_gemini_api
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class GeminiClient:
    """
    Client for Google Gemini API with resume analysis capabilities.

    Constitution II: All API calls use retry logic with exponential backoff.
    """

    def __init__(self):
        """Initialize Gemini client with API key from config."""
        # Configure Gemini API (Constitution III: API key from environment)
        genai.configure(api_key=settings.google_api_key)

        # Select model based on configuration
        self.model_name = settings.preferred_ai_model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": 0.7,  # Balanced creativity
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,  # Increased for longer analysis
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )

        logger.info(
            "gemini_client_initialized",
            operation="init",
            model=self.model_name,
        )

    async def generate_content(self, prompt: str) -> str:
        """
        Generic content generation method for prompts.

        Args:
            prompt: Text prompt for Gemini

        Returns:
            Generated text response
        """
        start_time = time.time()

        logger.info(
            "gemini_generate_started",
            operation="generate_content",
            prompt_length=len(prompt),
        )

        try:
            response = self.model.generate_content(prompt)
            result = response.text

            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "gemini_generate_completed",
                operation="generate_content",
                duration_ms=duration_ms,
                response_length=len(result),
            )

            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "gemini_generate_failed",
                operation="generate_content",
                duration_ms=duration_ms,
                error=str(e),
                exc_info=True,
            )
            raise

    @retry_gemini_api(max_attempts=3, timeout=30.0)
    def analyze_resume_text(self, resume_text: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze resume text using Gemini and return structured results.

        Constitution II: Uses @retry_gemini_api decorator for resilience
        Constitution V: Structured logging with operation context
        Performance: Target <60 seconds (SC-001)

        Args:
            resume_text: Extracted resume text
            user_id: Optional user ID for logging (anonymized)

        Returns:
            Dictionary with structured analysis:
            {
                "strengths": ["str1", "str2", ...],
                "weaknesses": ["str1", "str2", ...],
                "recommendations": ["str1", "str2", ...],
                "suitable_roles": ["role1", "role2", ...],
                "skills": ["skill1", "skill2", ...],
                "experience_years": int,
                "analyzed_at": "ISO timestamp",
                "model_used": "gemini-1.5-pro"
            }

        Raises:
            Exception: If analysis fails after all retries
        """
        start_time = time.time()

        logger.info(
            "resume_analysis_started",
            operation="analyze_resume",
            user_id=f"user-{user_id}" if user_id else "anonymous",
            model=self.model_name,
            text_length=len(resume_text),
        )

        try:
            # T025: Prompt engineering for structured resume analysis
            prompt = self._build_resume_analysis_prompt(resume_text)

            # Call Gemini API (with retry logic from decorator)
            response = self.model.generate_content(prompt)

            # Parse response
            analysis = self._parse_analysis_response(response.text)

            # Add metadata
            analysis["analyzed_at"] = time.time()
            analysis["model_used"] = self.model_name

            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "resume_analysis_completed",
                operation="analyze_resume",
                user_id=f"user-{user_id}" if user_id else "anonymous",
                duration_ms=duration_ms,
                success=True,
                strengths_count=len(analysis.get("strengths", [])),
                weaknesses_count=len(analysis.get("weaknesses", [])),
            )

            # Performance check (SC-001: <60 seconds)
            if duration_ms > 60000:
                logger.warning(
                    "resume_analysis_slow",
                    operation="analyze_resume",
                    duration_ms=duration_ms,
                    threshold_ms=60000,
                )

            return analysis

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "resume_analysis_failed",
                operation="analyze_resume",
                user_id=f"user-{user_id}" if user_id else "anonymous",
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            raise

    def _build_resume_analysis_prompt(self, resume_text: str) -> str:
        """
        Build prompt for resume analysis.

        T025: Prompt engineering for structured, actionable analysis.

        Args:
            resume_text: Resume content

        Returns:
            Formatted prompt for Gemini
        """
        prompt = f"""You are an expert career coach and resume analyst. Analyze the following resume and provide a comprehensive, structured analysis.

Resume Content:
{resume_text}

Please provide your analysis in the following JSON format (respond with ONLY valid JSON, no markdown formatting):

{{
  "strengths": [
    "List 3-5 key strengths demonstrated in this resume",
    "Focus on specific skills, achievements, and experiences"
  ],
  "weaknesses": [
    "List 2-4 areas for improvement",
    "Be constructive and specific"
  ],
  "recommendations": [
    "List 3-5 actionable recommendations to improve the resume",
    "Be specific and prioritize high-impact changes"
  ],
  "suitable_roles": [
    "List 3-5 job titles this candidate would be well-suited for",
    "Based on their experience and skills"
  ],
  "skills": [
    "Extract all technical and professional skills mentioned",
    "Include programming languages, tools, frameworks, soft skills"
  ],
  "experience_years": <estimate total years of professional experience as integer>
}}

Important:
- Be honest but constructive in your feedback
- Focus on actionable insights
- Consider industry standards and best practices
- Return ONLY the JSON object, no additional text or markdown formatting
"""
        return prompt

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini response into structured analysis.

        Args:
            response_text: Raw response from Gemini

        Returns:
            Parsed analysis dictionary

        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            # Parse JSON
            analysis = json.loads(response_text)

            # Validate required fields
            required_fields = ["strengths", "weaknesses", "recommendations", "suitable_roles", "skills"]
            for field in required_fields:
                if field not in analysis:
                    logger.warning(
                        "analysis_missing_field",
                        operation="parse_analysis",
                        field=field,
                    )
                    analysis[field] = []

            # Ensure experience_years is present
            if "experience_years" not in analysis:
                analysis["experience_years"] = 0

            return analysis

        except json.JSONDecodeError as e:
            logger.error(
                "analysis_parse_failed",
                operation="parse_analysis",
                error=str(e),
                response_preview=response_text[:200],
            )
            # Return fallback structure
            return {
                "strengths": ["Unable to parse analysis"],
                "weaknesses": [],
                "recommendations": ["Please try uploading your resume again"],
                "suitable_roles": [],
                "skills": [],
                "experience_years": 0,
                "parse_error": str(e),
            }


# Example usage
if __name__ == "__main__":
    from src.utils.logging_config import configure_logging

    # Configure logging
    configure_logging(log_level="INFO", json_output=False)

    # Test client
    client = GeminiClient()

    # Sample resume text
    sample_resume = """
    John Doe
    Software Engineer

    Experience:
    - Senior Software Engineer at Tech Corp (2020-2024)
      • Led development of microservices architecture
      • Managed team of 5 engineers
      • Improved system performance by 40%

    - Software Engineer at Startup Inc (2018-2020)
      • Built REST APIs with Python and FastAPI
      • Implemented CI/CD pipelines

    Skills: Python, JavaScript, React, Docker, Kubernetes, PostgreSQL, AWS
    Education: BS Computer Science, State University (2018)
    """

    # Test analysis
    try:
        result = client.analyze_resume_text(sample_resume)
        print("\n=== Analysis Result ===")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
