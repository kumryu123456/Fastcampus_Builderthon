"""
Quick script to create a test user for MVP development.

Run this if you need to manually create the test user:
    python create_test_user.py
"""

from src.database import SessionLocal
from src.models.user import User
from src.utils.logging_config import configure_logging, get_logger

configure_logging(log_level="INFO", json_output=False)
logger = get_logger(__name__)


def create_test_user():
    """Create test user for MVP."""
    db = SessionLocal()
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == "test@pathpilot.com").first()

        if existing_user:
            logger.info(f"Test user already exists with ID: {existing_user.id}")
            return existing_user

        # Create new test user
        test_user = User(
            email="test@pathpilot.com",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        logger.info(f"Test user created successfully with ID: {test_user.id}")
        return test_user

    except Exception as e:
        logger.error(f"Failed to create test user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_test_user()
