"""
Database configuration and session management for PathPilot.

Constitution Compliance:
- Principle III: User Data Privacy - Secure connection pooling, no credential logging
- Principle V: Code Quality - Structured logging for database operations
"""

from typing import Generator
from sqlalchemy import create_engine, event, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from src.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Database connection with pooling configuration
# Constitution III: database_url from environment, never hardcoded
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=10,  # Maximum number of permanent connections
    max_overflow=20,  # Maximum number of temporary connections
    pool_timeout=30,  # Timeout for getting connection from pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before using them
    echo=settings.app_debug,  # Log SQL queries in debug mode
    future=True,  # Use SQLAlchemy 2.0 style
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

# Naming convention for constraints (helps with migrations)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)

# Base class for all models
Base = declarative_base(metadata=metadata)


# Database event listeners for logging
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log database connections (Constitution V: Structured logging)."""
    logger.debug(
        "database_connection_established",
        operation="db_connect",
        pool_size=engine.pool.size(),
    )


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkout from pool."""
    logger.debug(
        "database_connection_checkout",
        operation="db_checkout",
        pool_size=engine.pool.size(),
        overflow=engine.pool.overflow(),
    )


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database sessions.

    Yields:
        Database session

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        logger.debug("database_session_created", operation="session_create")
        yield db
    except Exception as e:
        logger.error(
            "database_session_error",
            operation="session_error",
            error=str(e),
            exc_info=True,
        )
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("database_session_closed", operation="session_close")


def init_db() -> None:
    """
    Initialize database tables and create default test user.

    Creates all tables defined in models that inherit from Base.
    Should be called on application startup.
    """
    # Import models to register them with Base.metadata
    from src.models import user, resume, cover_letter, job, interview  # noqa: F401
    from src.models.user import User

    logger.info("database_initialization_started", operation="init_db")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("database_initialization_completed", operation="init_db", success=True)

        # Create default test user for MVP (Constitution IV: Hackathon MVP First)
        db = SessionLocal()
        try:
            existing_user = db.query(User).filter(User.id == 1).first()
            if not existing_user:
                default_user = User(
                    email="test@pathpilot.com",
                )
                db.add(default_user)
                db.commit()
                db.refresh(default_user)
                logger.info("default_user_created", operation="init_db", user_id=default_user.id)
            else:
                logger.info("default_user_exists", operation="init_db", user_id=existing_user.id)
        except Exception as e:
            logger.warning("default_user_creation_failed", operation="init_db", error=str(e))
            db.rollback()
        finally:
            db.close()

    except Exception as e:
        logger.error(
            "database_initialization_failed",
            operation="init_db",
            error=str(e),
            exc_info=True,
        )
        raise


def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        True if connection successful, False otherwise

    Used by health check endpoint.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.debug("database_health_check_passed", operation="health_check")
        return True
    except Exception as e:
        logger.error(
            "database_health_check_failed",
            operation="health_check",
            error=str(e),
        )
        return False


# Example model for reference (will be replaced by actual models)
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func

class ExampleModel(Base):
    __tablename__ = "example"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # JSON column for flexible data storage (e.g., resume analysis results)
    metadata = Column(JSON, nullable=True)
"""
