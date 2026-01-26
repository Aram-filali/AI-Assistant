"""User model"""

from sqlalchemy import Column, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """User roles"""
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """User account"""
    
    __tablename__ = "users"
    __table_args__ = {"schema": "app"}
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    role = Column(
        SQLEnum(UserRole, schema="app"),
        default=UserRole.USER,
        nullable=False
    )
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(String(10), default="true", nullable=False)
    
    # Relationships
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User {self.email}>"