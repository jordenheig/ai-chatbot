from sqlalchemy.orm import Session
from app.db.session import engine, SessionLocal
from app.db.models import Base
from app.core.logging import logger
from app.core.security import get_password_hash
from app.db.models import User
import time

def init_db() -> None:
    max_retries = 5
    retry_interval = 5  # seconds

    for attempt in range(max_retries):
        try:
            # Create all tables
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")

            # Create initial admin user if it doesn't exist
            db = SessionLocal()
            try:
                # Check if admin user exists
                admin_email = "admin@example.com"
                admin = db.query(User).filter(User.email == admin_email).first()
                
                if not admin:
                    admin = User(
                        email=admin_email,
                        hashed_password=get_password_hash("admin123")  # Change this password
                    )
                    db.add(admin)
                    db.commit()
                    logger.info("Admin user created successfully")
            finally:
                db.close()
            
            break  # Exit the retry loop if successful
            
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database initialization attempt {attempt + 1} failed: {str(e)}")
                logger.info(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                logger.error(f"Database initialization failed after {max_retries} attempts")
                raise

if __name__ == "__main__":
    init_db() 