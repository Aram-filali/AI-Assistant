"""Conversation model"""

from sqlalchemy import Column, String, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class ConversationStatus(str, enum.Enum):
    """Conversation status"""
    ACTIVE = "active"
    ARCHIVED = "archived"


class Conversation(BaseModel):
    """Chat conversation"""
    
    __tablename__ = "conversations"
    __table_args__ = {"schema": "app"}
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("app.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    title = Column(String(500), nullable=False, default="Nouvelle conversation")
    
    status = Column(
        SQLEnum(ConversationStatus, schema="app"),
        default=ConversationStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    meta_data = Column(
        JSON,
        default=dict,
        nullable=False,
        comment="Additional data: language, tags, score, etc."
    )
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    actions = relationship(
        "Action",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Conversation {self.id} - {self.title[:30]}>"