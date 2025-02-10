"""Database initialization and setup.

This module handles:
- Database table creation
- Initial data seeding
- Database migrations
- Index creation
"""

from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models import User
from app.core.logging import logger

def init_db(db: Session) -> None:
    """Initialize database with required tables and initial data.
    
    Args:
        db: Database session
        
    This function:
    1. Creates all tables
    2. Creates initial admin user if not exists
    3. Sets up required indexes
    """
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Create admin user if not exists
        admin_email = settings.FIRST_ADMIN_EMAIL
        if not db.query(User).filter(User.email == admin_email).first():
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash(settings.FIRST_ADMIN_PASSWORD)
            )
            db.add(admin_user)
            db.commit()
            logger.info("Created initial admin user")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

if __name__ == "__main__":
    init_db() 