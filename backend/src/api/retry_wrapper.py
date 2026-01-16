"""
API retry logic with exponential backoff.

Constitution Compliance:
- Principle II: External API Resilience - All Claude/Gemini/ElevenLabs calls have retry logic
- Principle V: Code Quality - Structured logging for retry attempts
"""

import time
from typing import Any, Callable, Optional, Type, Union
from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
import logging

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 10.0,
    multiplier: float = 2.0,
    exceptions: tuple = (Exception,),
    logger_name: Optional[str] = None,
):
    """
    Decorator for retrying functions with exponential backoff.

    Constitution II: API Resilience
    - Minimum 3 retry attempts with exponential backoff
    - Clear timeout definitions for all API calls

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_wait: Initial wait time in seconds (default: 1.0)
        max_wait: Maximum wait time between retries (default: 10.0)
        multiplier: Exponential backoff multiplier (default: 2.0)
        exceptions: Tuple of exceptions to retry on (default: all exceptions)
        logger_name: Custom logger name (optional)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_backoff(max_attempts=3, initial_wait=1.0)
        async def call_gemini_api(prompt: str) -> str:
            response = await client.generate(prompt)
            return response.text

    Backoff sequence (default):
        - Attempt 1: immediate
        - Attempt 2: wait 1s (2^0 * 1.0)
        - Attempt 3: wait 2s (2^1 * 1.0)
        - Attempt 4: wait 4s (2^2 * 1.0)
    """

    def decorator(func: Callable) -> Callable:
        # Get or create logger
        func_logger = get_logger(logger_name or func.__module__)

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=multiplier,
                min=initial_wait,
                max=max_wait,
            ),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logging.getLogger(func_logger.name), logging.WARNING),
            after=after_log(logging.getLogger(func_logger.name), logging.INFO),
        )
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                func_logger.debug(
                    "api_call_started",
                    operation=func.__name__,
                    max_attempts=max_attempts,
                )
                result = await func(*args, **kwargs)
                func_logger.info(
                    "api_call_succeeded",
                    operation=func.__name__,
                )
                return result
            except Exception as e:
                func_logger.error(
                    "api_call_failed_all_retries",
                    operation=func.__name__,
                    max_attempts=max_attempts,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                raise

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=multiplier,
                min=initial_wait,
                max=max_wait,
            ),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logging.getLogger(func_logger.name), logging.WARNING),
            after=after_log(logging.getLogger(func_logger.name), logging.INFO),
        )
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                func_logger.debug(
                    "api_call_started",
                    operation=func.__name__,
                    max_attempts=max_attempts,
                )
                result = func(*args, **kwargs)
                func_logger.info(
                    "api_call_succeeded",
                    operation=func.__name__,
                )
                return result
            except Exception as e:
                func_logger.error(
                    "api_call_failed_all_retries",
                    operation=func.__name__,
                    max_attempts=max_attempts,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                raise

        # Return appropriate wrapper based on function type
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Specific retry decorators for common APIs
def retry_gemini_api(
    max_attempts: int = 3,
    timeout: float = 30.0,
):
    """
    Retry decorator specifically for Gemini API calls.

    Uses project configuration for retry settings (Constitution II).

    Args:
        max_attempts: Maximum retry attempts (default from config: 3)
        timeout: API call timeout in seconds (default from config: 30)

    Example:
        @retry_gemini_api()
        async def analyze_resume(text: str) -> dict:
            response = await gemini_client.generate(text)
            return response
    """
    from src.config import settings

    return retry_with_backoff(
        max_attempts=max_attempts or settings.gemini_max_retries,
        initial_wait=1.0,
        max_wait=8.0,
        exceptions=(Exception,),  # Retry all exceptions for now
        logger_name="pathpilot.api.gemini",
    )


def retry_elevenlabs_api(
    max_attempts: int = 3,
    timeout: float = 10.0,
):
    """
    Retry decorator specifically for ElevenLabs API calls.

    Uses project configuration for retry settings (Constitution II).

    Args:
        max_attempts: Maximum retry attempts (default from config: 3)
        timeout: API call timeout in seconds (default from config: 10)

    Example:
        @retry_elevenlabs_api()
        async def synthesize_voice(text: str) -> bytes:
            audio = await elevenlabs_client.generate(text)
            return audio
    """
    from src.config import settings

    return retry_with_backoff(
        max_attempts=max_attempts or settings.elevenlabs_max_retries,
        initial_wait=0.5,
        max_wait=5.0,
        exceptions=(Exception,),  # Retry all exceptions for now
        logger_name="pathpilot.api.elevenlabs",
    )


# Example usage
if __name__ == "__main__":
    import asyncio

    @retry_with_backoff(max_attempts=3, initial_wait=1.0)
    def flaky_function(fail_count: int = 2):
        """Example function that fails a few times then succeeds."""
        if not hasattr(flaky_function, "attempts"):
            flaky_function.attempts = 0

        flaky_function.attempts += 1
        print(f"Attempt {flaky_function.attempts}")

        if flaky_function.attempts <= fail_count:
            raise ValueError(f"Simulated failure {flaky_function.attempts}")

        return f"Success after {flaky_function.attempts} attempts!"

    @retry_gemini_api()
    async def mock_gemini_call():
        """Example async function with Gemini retry logic."""
        print("Calling Gemini API...")
        await asyncio.sleep(0.1)
        return "Gemini response"

    # Test sync retry
    try:
        result = flaky_function(fail_count=2)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")

    # Test async retry
    asyncio.run(mock_gemini_call())
