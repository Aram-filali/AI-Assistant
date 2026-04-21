"""API endpoints for Knowledge Base management"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import shutil
from pathlib import Path
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.knowledge import KnowledgeBase, KnowledgeDocument
from app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseWithDocuments,
    DocumentResponse,
    DocumentUploadResponse,
    URLAddRequest,
    QueryRequest,
    QueryResponse,
    RAGStats,
    KnowledgeBaseStats
)
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

# Upload directory
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ==================== Knowledge Base CRUD ====================

@router.post("/bases", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new knowledge base"""
    try:
        kb = KnowledgeBase(
            name=kb_data.name,
            description=kb_data.description,
            user_id=current_user.id
        )
        db.add(kb)
        await db.commit()
        await db.refresh(kb)
        
        logger.info(f"Created knowledge base: {kb.name} (ID: {kb.id})")
        return kb
        
    except Exception as e:
        logger.error(f"Error creating knowledge base: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bases", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all knowledge bases for current user"""
    result = await db.execute(
        select(KnowledgeBase)
        .options(selectinload(KnowledgeBase.documents))
        .filter(KnowledgeBase.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    knowledge_bases = result.scalars().all()
    return knowledge_bases


@router.get("/bases/{kb_id}", response_model=KnowledgeBaseWithDocuments)
async def get_knowledge_base(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get knowledge base with documents"""
    import uuid
    kb_uuid = uuid.UUID(kb_id)
    
    result = await db.execute(
        select(KnowledgeBase)
        .options(selectinload(KnowledgeBase.documents))
        .filter(
            KnowledgeBase.id == kb_uuid,
            KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalars().first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    return kb


@router.put("/bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: str,
    kb_update: KnowledgeBaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update knowledge base"""
    import uuid
    kb_uuid = uuid.UUID(kb_id)
    
    result = await db.execute(
        select(KnowledgeBase)
        .filter(
            KnowledgeBase.id == kb_uuid,
            KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalars().first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # Update fields
    if kb_update.name is not None:
        kb.name = kb_update.name
    if kb_update.description is not None:
        kb.description = kb_update.description
    
    await db.commit()
    await db.refresh(kb)
    
    logger.info(f"Updated knowledge base: {kb.id}")
    return kb


@router.delete("/bases/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete knowledge base and all documents"""
    import uuid
    kb_uuid = uuid.UUID(kb_id)
    
    result = await db.execute(
        select(KnowledgeBase)
        .filter(
            KnowledgeBase.id == kb_uuid,
            KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalars().first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # Delete all documents (cascade will handle this in DB)
    await db.delete(kb)
    await db.commit()
    
    # Rebuild FAISS index without deleted documents
    try:
        await rag_service.rebuild_index(db)
    except Exception as e:
        logger.error(f"Error rebuilding index: {e}")
    
    logger.info(f"Deleted knowledge base: {kb_id}")


# ==================== Document Management ====================

@router.post("/bases/{kb_id}/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and process document"""
    import uuid
    kb_uuid = uuid.UUID(kb_id)
    
    # Check KB exists and belongs to user
    result = await db.execute(
        select(KnowledgeBase)
        .filter(
            KnowledgeBase.id == kb_uuid,
            KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalars().first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.txt', '.md', '.docx', '.html'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not supported. Allowed: {allowed_extensions}"
        )
    
    try:
        # Save file
        file_path = UPLOAD_DIR / f"{current_user.id}_{kb_id}_{file.filename}"
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Saved file: {file_path}")
        
        # Process with RAG service
        document = await rag_service.add_document(
            file_path=str(file_path),
            db=db,
            user_id=current_user.id,
            knowledge_base_id=kb_uuid
        )
        
        return document
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        # Clean up file if processing failed
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bases/{kb_id}/documents/url", response_model=DocumentUploadResponse)
async def add_url(
    kb_id: str,
    url_data: URLAddRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add URL content to knowledge base"""
    import uuid
    kb_uuid = uuid.UUID(kb_id)
    
    # Check KB exists
    result = await db.execute(
        select(KnowledgeBase)
        .filter(
            KnowledgeBase.id == kb_uuid,
            KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalars().first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    try:
        document = await rag_service.add_url(
            url=str(url_data.url),
            db=db,
            user_id=current_user.id,
            knowledge_base_id=kb_uuid
        )
        
        return document
        
    except Exception as e:
        logger.error(f"Error adding URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bases/{kb_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents in knowledge base"""
    import uuid
    kb_uuid = uuid.UUID(kb_id)
    
    # Check KB access
    result = await db.execute(
        select(KnowledgeBase)
        .filter(
            KnowledgeBase.id == kb_uuid,
            KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalars().first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    result = await db.execute(
        select(KnowledgeDocument)
        .filter(KnowledgeDocument.knowledge_base_id == kb_uuid)
    )
    documents = result.scalars().all()
    
    return documents


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete document"""
    import uuid
    doc_uuid = uuid.UUID(doc_id)
    
    result = await db.execute(
        select(KnowledgeDocument)
        .filter(
            KnowledgeDocument.id == doc_uuid,
            KnowledgeDocument.user_id == current_user.id
        )
    )
    document = result.scalars().first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete file if exists
        if document.file_type != 'url':
            file_path = Path(document.file_path)
            if file_path.exists():
                file_path.unlink()
        
        # Delete from DB
        await db.delete(document)
        await db.commit()
        
        logger.info(f"Deleted document: {doc_id}")
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Query ====================

@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(
    query: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Query knowledge base using RAG"""
    try:
        kb_uuid = None
        # If KB specified, check access
        if query.knowledge_base_id:
            kb_uuid = query.knowledge_base_id

            result = await db.execute(
                select(KnowledgeBase)
                .filter(
                    KnowledgeBase.id == kb_uuid,
                    KnowledgeBase.user_id == current_user.id
                )
            )
            kb = result.scalars().first()
            
            if not kb:
                raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Execute query
        response = await rag_service.query(
            question=query.question,
            knowledge_base_id=kb_uuid,
            top_k=query.top_k,
            include_sources=query.include_sources
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error querying: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Stats ====================

@router.get("/stats", response_model=RAGStats)
async def get_rag_stats(
    current_user: User = Depends(get_current_user)
):
    """Get RAG system statistics"""
    try:
        stats = rag_service.get_stats()
        return RAGStats(
            total_vectors=stats['faiss']['total_vectors'],
            embedding_dim=stats['faiss']['embedding_dim'],
            total_documents=stats['faiss']['total_documents'],
            embedding_model=stats['embedding_model']
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebuild-index", status_code=200)
async def rebuild_index(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rebuild FAISS index from database (admin only)"""
    try:
        await rag_service.rebuild_index(db)
        return {"message": "Index rebuilt successfully"}
    except Exception as e:
        logger.error(f"Error rebuilding index: {e}")
        raise HTTPException(status_code=500, detail=str(e))
