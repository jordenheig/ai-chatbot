"""CRUD operations for user management."""

from sqlalchemy.orm import Session
from app.db.models import User

class CRUDUser:
    def get_by_username(self, db: Session, username: str) -> User:
        """Get user by username.
        
        Args:
            db: Database session
            username: Username to lookup
            
        Returns:
            User if found, None otherwise
        """
        return db.query(User).filter(User.username == username).first()

# Create singleton instance
user_crud = CRUDUser() 