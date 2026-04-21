"""Pydantic schemas for Chat Conversations and Messages"""

from pydantic import BaseModel, Field
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== Enums ====================

class MessageRole(str, Enum):
    """Message role"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    """Conversation status"""
    ACTIVE = "active"
    ARCHIVED = "archived"


# ==================== Message Schemas ====================

class MessageBase(BaseModel):
    """Base message schema"""
    content: str
    role: MessageRole
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class MessageCreate(MessageBase):
    """Schema for creating a message"""
    conversation_id: uuid.UUID


class SourceInfo(BaseModel):
    """Schema for RAG source information"""
    filename: str
    chunk_index: int
    document_id: uuid.UUID
    score: float
    text: Optional[str] = None


class MessageResponse(MessageBase):
    """Schema for message response"""
    id: uuid.UUID
    conversation_id: uuid.UUID
    sources: Optional[List[Dict[str, Any]]] = None
    rag_used: bool = False
    retrieval_score: Optional[float] = None
    triggered_actions: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Conversation Schemas ====================

class ConversationBase(BaseModel):
    """Base conversation schema"""
    title: str = Field(default="Nouvelle conversation", max_length=500)
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation"""
    knowledge_base_id: Optional[uuid.UUID] = None


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation"""
    title: Optional[str] = Field(None, max_length=500)
    status: Optional[ConversationStatus] = None
    meta_data: Optional[Dict[str, Any]] = None


class ConversationResponse(ConversationBase):
    """Schema for conversation response"""
    id: uuid.UUID
    user_id: uuid.UUID
    knowledge_base_id: Optional[uuid.UUID] = None
    knowledge_base_name: Optional[str] = None
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    """Conversation with its list of messages"""
    messages: List[MessageResponse] = []


# ==================== Chat Interaction Schemas ====================

class ChatRequest(BaseModel):
    """Schema for a chat message request"""
    question: str = Field(..., min_length=1)
    conversation_id: Optional[uuid.UUID] = None  # Optional for public chats
    knowledge_base_id: Optional[uuid.UUID] = None
    top_k: int = Field(default=5, ge=1, le=20)
    session_id: Optional[str] = None  # ✨ NEW: Session ID for public/anonymous users


# Update forward references
ConversationWithMessages.model_rebuild()
