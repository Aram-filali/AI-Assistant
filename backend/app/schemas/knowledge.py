"""Pydantic schemas for Knowledge Base and Documents"""

from pydantic import BaseModel, Field, HttpUrl
import uuid

from typing import Optional, List
from datetime import datetime


# ==================== Knowledge Base Schemas ====================

class KnowledgeBaseCreate(BaseModel):
    """Schema for creating a knowledge base"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Documentation Technique",
                "description": "Base de connaissances pour la doc technique du projet"
            }
        }


class KnowledgeBaseUpdate(BaseModel):
    """Schema for updating a knowledge base"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Documentation Mise à Jour",
                "description": "Description modifiée"
            }
        }


class KnowledgeBaseResponse(BaseModel):
    """Schema for knowledge base response"""
    id: uuid.UUID
    name: str
    description: Optional[str]
    document_count: int
    created_at: datetime
    updated_at: datetime
    user_id: uuid.UUID

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Documentation Technique",
                "description": "Base de connaissances technique",
                "document_count": 5,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00",
                "user_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class KnowledgeBaseWithDocuments(KnowledgeBaseResponse):
    """Knowledge base with documents list"""
    documents: List['DocumentResponse'] = []


# ==================== Document Schemas ====================

class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    id: uuid.UUID
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    knowledge_base_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: uuid.UUID
    filename: str
    file_path: str
    file_type: str
    file_size: int
    chunk_count: int
    knowledge_base_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "guide.pdf",
                "file_path": "/uploads/guide.pdf",
                "file_type": ".pdf",
                "file_size": 1024000,
                "chunk_count": 42,
                "knowledge_base_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2024-01-15T10:30:00"
            }
        }


class URLAddRequest(BaseModel):
    """Schema for adding URL to knowledge base"""
    url: HttpUrl
    knowledge_base_id: uuid.UUID

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://docs.python.org/3/tutorial/",
                "knowledge_base_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


# ==================== Query Schemas ====================

class QueryRequest(BaseModel):
    """Schema for RAG query request"""
    question: str = Field(..., min_length=1, max_length=1000)
    knowledge_base_id: Optional[uuid.UUID] = None
    top_k: int = Field(default=5, ge=1, le=20)
    include_sources: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Comment installer FastAPI ?",
                "knowledge_base_id": "123e4567-e89b-12d3-a456-426614174000",
                "top_k": 5,
                "include_sources": True
            }
        }


class SourceInfo(BaseModel):
    """Information about a source"""
    filename: str
    chunk_index: int
    document_id: uuid.UUID
    score: Optional[float] = None


class QueryResponse(BaseModel):
    """Schema for RAG query response"""
    answer: str
    sources: List[SourceInfo] = []
    context_used: int
    model: str
    retrieval: Optional[dict] = None
    usage: Optional[dict] = None
    triggered_actions: Optional[List[dict]] = None
    lead_info: Optional[dict] = None  # ✨ NEW: Lead capture info for public chats
    conversation_id: Optional[uuid.UUID] = None  # ✨ NEW: For authenticated chat sessions

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Pour installer FastAPI, utilisez pip install fastapi...",
                "sources": [
                    {
                        "filename": "fastapi_guide.pdf",
                        "chunk_index": 0,
                        "document_id": 1,
                        "score": 0.92
                    }
                ],
                "context_used": 3,
                "model": "openai/gpt-4o-mini",
                "retrieval": {
                    "chunks_retrieved": 5,
                    "top_scores": [0.92, 0.87, 0.81]
                },
                "usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 50,
                    "total_tokens": 200
                }
            }
        }


# ==================== Stats Schemas ====================

class RAGStats(BaseModel):
    """RAG system statistics"""
    total_vectors: int
    embedding_dim: Optional[int]
    total_documents: int
    embedding_model: str

    class Config:
        json_schema_extra = {
            "example": {
                "total_vectors": 1250,
                "embedding_dim": 384,
                "total_documents": 15,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
            }
        }


class KnowledgeBaseStats(BaseModel):
    """Statistics for a knowledge base"""
    knowledge_base_id: uuid.UUID
    name: str
    document_count: int
    total_chunks: int
    avg_chunks_per_doc: float

    class Config:
        json_schema_extra = {
            "example": {
                "knowledge_base_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Documentation Technique",
                "document_count": 5,
                "total_chunks": 215,
                "avg_chunks_per_doc": 43.0
            }
        }


# Update forward references
KnowledgeBaseWithDocuments.model_rebuild()
