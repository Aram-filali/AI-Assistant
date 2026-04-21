"""Database models for AI Sales Assistant"""

from app.models.base import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document as TrackingDocument, DocumentChunk
from app.models.knowledge import KnowledgeBase, KnowledgeDocument
from app.models.action import Action
from app.models.lead import Lead, LeadStatus  # ✨ NEW

__all__ = [
    "Base",
    "User",
    "Conversation",
    "Message",
    "Lead",
    "LeadStatus",
    "TrackingDocument",
    "DocumentChunk",
    "KnowledgeDocument",
    "KnowledgeBase",
    "Action",
]