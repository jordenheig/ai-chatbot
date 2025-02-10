from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import time

def get_engine():
    max_retries = 5
    retry_interval = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(
                settings.SQLALCHEMY_DATABASE_URI,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            # Test the connection
            engine.connect()
            return engine
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Database connection attempt {attempt + 1} failed: {str(e)}")
                print(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                raise

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 