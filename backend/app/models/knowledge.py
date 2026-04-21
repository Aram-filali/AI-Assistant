"""Knowledge Base and Document models"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class KnowledgeBase(BaseModel):
    """Collection of documents"""
    
    __tablename__ = "knowledge_bases"
    __table_args__ = {"schema": "app"}
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app.users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="knowledge_bases")
    documents = relationship("KnowledgeDocument", back_populates="knowledge_base", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="knowledge_base")
    
    @property
    def document_count(self) -> int:
        # Avoid triggering lazy load during serialization
        if "documents" in self.__dict__:
            return len(self.documents)
        return 0


class KnowledgeDocument(BaseModel):
    """Individual document within a knowledge base"""
    
    __tablename__ = "documents_rag"
    __table_args__ = {"schema": "app"}
    
    filename = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0)
    
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("app.knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app.users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    user = relationship("User", back_populates="documents_rag")


