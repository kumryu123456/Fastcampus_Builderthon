"""
API routers for PathPilot.

Constitution Compliance:
- Principle II: API Resilience - All routers have error handling
- Principle V: Code Quality - Structured logging in all endpoints
"""

from src.routers import resume

__all__ = ["resume"]
