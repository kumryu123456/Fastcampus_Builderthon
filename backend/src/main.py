"""
PathPilot FastAPI Application.

Constitution Compliance:
- Principle II: API Resilience - Health checks and graceful error handling
- Principle III: User Data Privacy - CORS configuration, no credential exposure
- Principle V: Code Quality - Structured logging middleware
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

from src.config import settings
from src.database import init_db, check_db_connection
from src.utils.logging_config import configure_logging, get_logger

# Configure logging on startup
configure_logging(
    log_level=settings.log_level,
    json_output=settings.is_production,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Handles startup and shutdown operations:
    - Startup: Initialize database, check connections
    - Shutdown: Cleanup resources
    """
    # Startup
    logger.info(
        "application_startup",
        operation="startup",
        environment=settings.app_env,
        debug=settings.app_debug,
    )

    try:
        # Initialize database
        init_db()
        logger.info("database_initialized", operation="startup")

        # Check database connection
        if check_db_connection():
            logger.info("database_connection_healthy", operation="startup")
        else:
            logger.warning("database_connection_unhealthy", operation="startup")

    except Exception as e:
        logger.error(
            "startup_failed",
            operation="startup",
            error=str(e),
            exc_info=True,
        )
        raise

    yield

    # Shutdown
    logger.info("application_shutdown", operation="shutdown")


# Create FastAPI application
app = FastAPI(
    title="PathPilot API",
    description="AI-powered job application automation platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# CORS Middleware (Constitution III: Configured from environment)
# Development: allow all origins for easier testing
cors_origins = ["*"] if settings.is_development else settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,  # Must be False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)


# Logging Middleware (Constitution V: Structured logging)
@app.middleware("http")
async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Log all HTTP requests with structured logging.

    Includes:
    - request_id: Unique identifier for request tracing
    - method: HTTP method
    - path: Request path
    - duration_ms: Request processing time
    """
    # Generate request ID
    request_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    # Start timer
    start_time = time.time()

    # Log request
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        request_id=request_id,
    )

    # Process request
    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)

        # Log response
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_id=request_id,
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            duration_ms=duration_ms,
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise


# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with structured logging."""
    logger.warning(
        "validation_error",
        path=request.url.path,
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured logging."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.app_debug else "An error occurred",
        },
    )


# Health Check Endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status with database connectivity check

    Constitution II: API Resilience - Health checks for monitoring
    """
    db_healthy = check_db_connection()

    health_status = {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "environment": settings.app_env,
        "features": {
            "job_discovery": settings.feature_job_discovery,
            "mock_interview": settings.feature_mock_interview,
            "dashboard_stats": settings.feature_dashboard_stats,
        },
    }

    status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    logger.info("health_check_performed", **health_status)

    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "PathPilot API",
        "version": "0.1.0",
        "description": "AI-powered job application automation",
        "docs": "/docs",
        "health": "/health",
        "constitution_compliant": True,
        "ai_provider": "Google Gemini",
    }


# Router imports (Phase 3+)
from src.routers import resume, cover_letter, jobs, interview

# Register routers
app.include_router(resume.router, prefix="/api/v1")
app.include_router(cover_letter.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(interview.router, prefix="/api/v1")

# Future routers (will be added later):
# from src.routers import cover_letter, jobs, interview
# app.include_router(cover_letter.router, prefix="/api/v1/cover-letter", tags=["Cover Letter"])
# app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
# app.include_router(interview.router, prefix="/api/v1/interview", tags=["Interview"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_debug,
        log_level=settings.log_level.lower(),
    )
