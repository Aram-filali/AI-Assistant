"""Message model"""

from sqlalchemy import Column, String, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class MessageRole(str, enum.Enum):
    """Message role"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Chat message"""
    
    __tablename__ = "messages"
    __table_args__ = {"schema": "app"}
    
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("app.conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    role = Column(
        SQLEnum(MessageRole, schema="app"),
        nullable=False,
        index=True
    )
    
    content = Column(Text, nullable=False)
    
    meta_data = Column(
        JSON,
        default=dict,
        nullable=False,
        comment="Sources, confidence, tokens, etc."
    )
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.role} - {self.content[:30]}>"
