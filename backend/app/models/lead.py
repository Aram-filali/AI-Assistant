"""Lead model for capturing public visitors"""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.models.base import Base


class LeadStatus(str, enum.Enum):
    """Lead status states"""
    NEW = "NEW"  # Just arrived
    ENGAGED = "ENGAGED"  # Asked questions (3+ messages or 2+ min)
    QUALIFIED = "QUALIFIED"  # Requested devis/demo or provided email
    CONTACTED = "CONTACTED"  # Admin has reached out
    CONVERTED = "CONVERTED"  # Has purchased/closed
    ABANDONED = "ABANDONED"  # Inactive 7+ days


class Lead(Base):
    """Public visitor captured as a potential lead"""
    
    __tablename__ = "leads"
    __table_args__ = (
        UniqueConstraint('email', name='uq_lead_email'),
        {"schema": "app"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Contact info (may be captured gradually)
    email = Column(String(255), unique=True, nullable=True, index=True)
    name = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)
    company_name = Column(String(255), nullable=True)
    
    # Lead status (crucial field)
    status = Column(SQLEnum(LeadStatus, schema='app'), default=LeadStatus.NEW, nullable=False, index=True)
    
    # Links to knowledge base
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey('app.knowledge_bases.id'), nullable=True)
    
    # Engagement metrics (JSON for flexibility)
    meta_data = Column(JSON, default={
        "message_count": 0,
        "session_duration": 0,  # seconds
        "keywords": [],
        "last_message_at": None,
        "trigger_type": None,  # Which trigger captured them?
        "email_capture_method": None,  # "MANUAL" or "AI_PROPOSAL"
        "notes": "",
        "previous_statuses": []  # History of status transitions
    }, nullable=False)
    
    # When was contact made?
    contacted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships - ONE Lead can have MANY Conversations
    conversations = relationship("Conversation", back_populates="lead", foreign_keys="Conversation.lead_id")
    
    def __repr__(self):
        return f"<Lead {self.email} ({self.status})>"
    
    def to_dict(self):
        """Convert to dict for API responses"""
        return {
            'id': str(self.id),
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'company_name': self.company_name,
            'status': self.status.value,
            'meta_data': self.meta_data,
            'message_count': self.meta_data.get('message_count', 0),
            'session_duration': self.meta_data.get('session_duration', 0),
            'last_message_at': self.meta_data.get('last_message_at'),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'contacted_at': self.contacted_at.isoformat() if self.contacted_at else None,
        }
