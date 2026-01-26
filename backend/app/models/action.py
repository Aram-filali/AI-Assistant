"""Action model"""

from sqlalchemy import Column, String, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class ActionType(str, enum.Enum):
    """Action type"""
    EMAIL = "email"
    CRM = "crm"
    TICKET = "ticket"
    SCORING = "scoring"
    NOTIFICATION = "notification"


class ActionStatus(str, enum.Enum):
    """Action status"""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class Action(BaseModel):
    """Automated action"""
    
    __tablename__ = "actions"
    __table_args__ = {"schema": "app"}
    
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("app.conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    action_type = Column(
        SQLEnum(ActionType, schema="app"),
        nullable=False,
        index=True
    )
    
    status = Column(
        SQLEnum(ActionStatus, schema="app"),
        default=ActionStatus.PENDING,
        nullable=False,
        index=True
    )
    
    payload = Column(
        JSON,
        nullable=False,
        comment="Action input data"
    )
    
    result = Column(
        JSON,
        default=dict,
        nullable=False,
        comment="Action output data"
    )
    
    executed_at = Column(String(50), nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="actions")
    
    def __repr__(self):
        return f"<Action {self.action_type} - {self.status}>"
