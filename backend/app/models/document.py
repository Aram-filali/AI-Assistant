"""Document and DocumentChunk models"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class DocumentType(str, enum.Enum):
    """Document type"""
    PDF = "pdf"
    WEB = "web"
    TEXT = "text"
    MARKDOWN = "markdown"
    API = "api"


class DocumentStatus(str, enum.Enum):
    """Document indexing status"""
    PENDING = "pending"
    INDEXED = "indexed"
    ERROR = "error"


class Document(BaseModel):
    """Knowledge base document"""
    
    __tablename__ = "documents"
    __table_args__ = {"schema": "app"}
    
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String(1000), nullable=True)
    
    doc_type = Column(
        SQLEnum(DocumentType, schema="app"),
        nullable=False,
        index=True
    )
    
    file_size = Column(Integer, nullable=True, comment="File size in bytes")
    
    status = Column(
        SQLEnum(DocumentStatus, schema="app"),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True
    )
    
    meta_data = Column(
        JSON,
        default=dict,
        nullable=False,
        comment="Author, tags, category, etc."
    )
    
    indexed_at = Column(String(50), nullable=True)
    
    # Relationships
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Document {self.title[:30]} - {self.status}>"


class DocumentChunk(BaseModel):
    """Document chunk for RAG"""
    
    __tablename__ = "document_chunks"
    __table_args__ = {"schema": "app"}
    
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("app.documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    content = Column(Text, nullable=False)
    
    chunk_index = Column(
        Integer,
        nullable=False,
        comment="Position in document"
    )
    
    embedding_id = Column(
        Integer,
        nullable=True,
        comment="Reference to FAISS index"
    )
    
    meta_data = Column(
        JSON,
        default=dict,
        nullable=False,
        comment="Page number, section, etc."
    )
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk {self.document_id} - {self.chunk_index}>"
