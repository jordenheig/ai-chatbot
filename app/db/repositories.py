from sqlalchemy.orm import Session
from app.db.models import User, Document, ChatSession, ChatMessage
from typing import List, Optional

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, email: str, hashed_password: str) -> User:
        user = User(email=email, hashed_password=hashed_password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_document(self, document: DocumentCreate, owner_id: int) -> Document:
        db_document = Document(
            **document.dict(),
            owner_id=owner_id
        )
        self.db.add(db_document)
        self.db.commit()
        self.db.refresh(db_document)
        return db_document

    def get_document(self, document_id: int, owner_id: int) -> Optional[Document]:
        return (
            self.db.query(Document)
            .filter(
                Document.id == document_id,
                Document.owner_id == owner_id
            )
            .first()
        )

    def get_user_documents(self, owner_id: int) -> List[Document]:
        return (
            self.db.query(Document)
            .filter(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
            .all()
        )

class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_session(self, session_id: int, user_id: int) -> Optional[ChatSession]:
        return self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()

    def get_user_sessions(self, user_id: int) -> List[ChatSession]:
        return self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).all()

    def get_session_messages(self, session_id: int) -> List[ChatMessage]:
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all() 