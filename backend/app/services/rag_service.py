"""
RAG (Retrieval Augmented Generation) Service

Orchestrates the complete RAG pipeline:
1. LOAD: Extract text from documents (PDF, DOCX, markdown, URLs)
2. SPLIT: Chunk large documents into semantic pieces
3. EMBED: Generate vector embeddings using Sentence Transformers
4. STORE: Index embeddings in FAISS for fast similarity search
5. RETRIEVE: Find relevant chunks based on user query
6. GENERATE: Create responses using GPT-4 + retrieved context

This approach ensures answers are grounded in company knowledge
while maintaining accuracy and reducing hallucinations.
"""

from typing import List, Dict, Optional
import logging
from pathlib import Path
import uuid

from app.core.rag.document_loader import document_loader
from app.core.rag.text_splitter import text_splitter
from app.core.rag.embedder import get_embedder
from app.core.rag.faiss_manager import faiss_manager
from app.core.rag.retriever import semantic_retriever
from app.core.rag.generator import rag_generator
from app.models.knowledge import KnowledgeBase, KnowledgeDocument
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

logger = logging.getLogger(__name__)


class RAGService:
    """
    Complete RAG pipeline orchestration.
    
    Responsibilities:
    - Document ingestion (files + URLs)
    - Chunk embedding generation
    - FAISS index management
    - Semantic search coordination
    - LLM-based response generation with context
    """
    
    def __init__(self):
        """Initialize RAG components and load persisted FAISS index"""
        self.embedder = get_embedder()              # Sentence Transformers model
        self.retriever = semantic_retriever         # FAISS + semantic search
        self.generator = rag_generator              # GPT-4 response generation
        
        # Load FAISS index from disk if available (production persistence)
        try:
            faiss_manager.load()
            logger.info("✅ FAISS index loaded from disk")
        except Exception as e:
            logger.warning(f"⚠️ FAISS index not found - will create new: {e}")
    
    async def add_document(
        self,
        file_path: str,
        db: AsyncSession,
        user_id: str,
        knowledge_base_id: str
    ) -> KnowledgeDocument:
        """
        Complete pipeline: Load document → Split → Embed → Index → Save
        
        Args:
            file_path: Local path to document (PDF, DOCX, etc.)
            db: AsyncSession for database operations
            user_id: Owner of the document (for multi-tenant isolation)
            knowledge_base_id: Knowledge base this document belongs to
            
        Returns:
            KnowledgeDocument object with metadata
            
        Raises:
            Exception: File load, embedding, or indexing errors
        """
        try:
            # 1. Load document
            logger.info(f"Loading document: {file_path}")
            doc_data = document_loader.load_file(file_path)
            
            # 2. Split into chunks
            logger.info("Splitting into chunks...")
            chunks = text_splitter.split_text(doc_data['content'])
            logger.info(f"Created {len(chunks)} chunks")
            
            # 3. Create document in DB
            document = KnowledgeDocument(
                filename=doc_data['metadata']['filename'],
                file_path=str(Path(file_path).absolute()),
                file_type=doc_data['metadata']['extension'],
                file_size=doc_data['metadata']['size'],
                chunk_count=len(chunks),
                user_id=user_id,
                knowledge_base_id=knowledge_base_id
            )
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            # 4. Generate embeddings
            logger.info("Generating embeddings...")
            embeddings = self.embedder.embed_texts(chunks)
            
            # 5. Prepare metadata for each chunk
            metadata_list = []
            for i, chunk in enumerate(chunks):
                metadata_list.append({
                    'text': chunk,
                    'chunk_index': i,
                    'document_id': document.id,
                    'filename': document.filename,
                    'knowledge_base_id': knowledge_base_id,
                    'user_id': user_id
                })
            
            # 6. Add to FAISS index
            logger.info("Adding to FAISS index...")
            
            # Create index if doesn't exist
            if faiss_manager.index is None:
                faiss_manager.create_index(self.embedder.get_embedding_dimension())
            
            faiss_manager.add_embeddings(embeddings, metadata_list)
            faiss_manager.save()
            
            logger.info(f"✅ Document added: {document.filename}")
            
            return document
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            await db.rollback()
            raise
    
    async def add_url(
        self,
        url: str,
        db: AsyncSession,
        user_id: str,
        knowledge_base_id: str
    ) -> KnowledgeDocument:
        """
        Add URL content to knowledge base
        
        Args:
            url: URL to fetch
            db: Database session
            user_id: User ID
            knowledge_base_id: Knowledge base ID
            
        Returns:
            Created Document object
        """
        try:
            # 1. Load from URL
            logger.info(f"Fetching URL: {url}")
            doc_data = document_loader.load_from_url(url)
            
            # 2. Split into chunks
            chunks = text_splitter.split_text(doc_data['content'])
            logger.info(f"Created {len(chunks)} chunks from URL")
            
            # 3. Create document in DB
            document = KnowledgeDocument(
                filename=doc_data['metadata']['title'],
                file_path=url,
                file_type='url',
                file_size=len(doc_data['content']),
                chunk_count=len(chunks),
                user_id=user_id,
                knowledge_base_id=knowledge_base_id
            )
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            # 4. Generate embeddings and add to index
            embeddings = self.embedder.embed_texts(chunks)
            
            metadata_list = []
            for i, chunk in enumerate(chunks):
                metadata_list.append({
                    'text': chunk,
                    'chunk_index': i,
                    'document_id': document.id,
                    'filename': document.filename,
                    'knowledge_base_id': knowledge_base_id,
                    'user_id': user_id,
                    'source_url': url
                })
            
            if faiss_manager.index is None:
                faiss_manager.create_index(self.embedder.get_embedding_dimension())
            
            faiss_manager.add_embeddings(embeddings, metadata_list)
            faiss_manager.save()
            
            logger.info(f"✅ URL added: {url}")
            
            return document
            
        except Exception as e:
            logger.error(f"Error adding URL: {e}")
            await db.rollback()
            raise
    
    async def query(
        self,
        question: str,
        knowledge_base_id: Optional[str] = None,
        top_k: int = 5,
        include_sources: bool = True
    ) -> Dict:
        """
        Query the knowledge base with strict KB isolation
        
        Args:
            question: User question
            knowledge_base_id: RECOMMENDED - Filter by specific KB for safety
            top_k: Number of chunks to retrieve
            include_sources: Include source documents
            
        Returns:
            Dict with answer, sources, metadata
            
        Note: If knowledge_base_id is provided, results will be STRICTLY filtered to that KB.
              This ensures multi-tenant data isolation in public chat scenarios.
        """
        try:
            # 1. Retrieve relevant chunks
            logger.info(f"Querying: {question[:100]}..." + (f" [KB: {knowledge_base_id}]" if knowledge_base_id else ""))
            chunks = await self.retriever.retrieve(
                query=question,
                top_k=top_k
            )
            
            # 2. STRICT Filter by knowledge base if specified
            # This ensures public chat responses use ONLY the specified KB
            if knowledge_base_id and chunks:
                kb_id_str = str(knowledge_base_id)
                original_count = len(chunks)
                chunks = [
                    c for c in chunks 
                    if str(c['metadata'].get('knowledge_base_id')) == kb_id_str
                ]
                if len(chunks) < original_count:
                    logger.info(f"KB Isolation: Filtered {original_count} → {len(chunks)} chunks for KB {kb_id_str}")
            elif not knowledge_base_id:
                logger.warning("⚠️ Query executed WITHOUT knowledge_base_id filter - consider specifying kb_id for multi-tenant safety")
            
            # 3. Generate response (with or without context)
            response = await self.generator.generate_response(
                query=question,
                context_chunks=chunks if chunks else None
            )
            
            # 4. Add retrieval metadata
            response['retrieval'] = {
                'chunks_retrieved': len(chunks) if chunks else 0,
                'top_scores': [c['score'] for c in chunks[:3]] if chunks else [],
                'knowledge_base_id': knowledge_base_id
            }
            
            if not include_sources:
                response.pop('sources', None)
            
            return response
            
        except Exception as e:
            logger.error(f"Error querying: {e}")
            raise

    async def chat(
        self,
        db: AsyncSession,
        user_id: str,
        question: str,
        conversation_id: uuid.UUID,
        knowledge_base_id: Optional[uuid.UUID] = None,
        top_k: int = 5
    ) -> Dict:
        """
        Complete chat interaction: load history, Query RAG, save messages
        
        Args:
            db: Database session
            user_id: User UUID
            question: User question
            conversation_id: Conversation UUID
            knowledge_base_id: Optional KB filter
            top_k: Number of chunks to retrieve
            
        Returns:
            Assistant response with sources and updated history
        """
        # 1. Verify conversation
        conv_result = await db.execute(
            select(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conversation = conv_result.scalars().first()
        if not conversation:
            raise ValueError("Conversation not found or access denied")

        # 2. Load History (last 10 messages for context)
        history_result = await db.execute(
            select(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(10)
        )
        history_msgs = history_result.scalars().all()
        # Reverse to get chronological order
        history_msgs.reverse()
        
        history_payload = [
            {"role": msg.role, "content": msg.content} 
            for msg in history_msgs
        ]

        # 3. Save User Message
        user_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=question
        )
        db.add(user_msg)
        await db.flush() # Get user_msg.id without committing yet

        # 4. Perform RAG Query with history
        # (Using the retriever to get chunks)
        chunks = await self.retriever.retrieve(
            query=question,
            top_k=top_k
        )
        
        if knowledge_base_id:
            chunks = [
                c for c in chunks 
                if str(c['metadata'].get('knowledge_base_id')) == str(knowledge_base_id)
            ]

        # 5. Generate Response
        response_data = await self.generator.generate_response(
            query=question,
            context_chunks=chunks,
            history=history_payload
        )

        # 6. Save Assistant Message
        assistant_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=response_data['answer'],
            meta_data={
                "sources": response_data.get('sources', []),
                "context_used": response_data.get('context_used', 0),
                "model": response_data.get('model')
            }
        )
        db.add(assistant_msg)
        
        # Update conversation timestamp
        from datetime import datetime
        conversation.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return response_data
    
    async def rebuild_index(self, db: AsyncSession):
        """
        Rebuild FAISS index from database
        
        Args:
            db: Database session
        """
        try:
            logger.info("Rebuilding FAISS index...")
            
            # Clear current index
            faiss_manager.clear()
            
            # Get all documents
            result = await db.execute(select(KnowledgeDocument))
            documents = result.scalars().all()
            
            if not documents:
                logger.warning("No documents to index")
                return
            
            # Process each document
            total_chunks = 0
            for doc in documents:
                try:
                    # Load and chunk document
                    if doc.file_type == 'url':
                        doc_data = document_loader.load_from_url(doc.file_path)
                    else:
                        doc_data = document_loader.load_file(doc.file_path)
                    
                    chunks = text_splitter.split_text(doc_data['content'])
                    
                    # Generate embeddings
                    embeddings = self.embedder.embed_texts(chunks)
                    
                    # Prepare metadata
                    metadata_list = []
                    for i, chunk in enumerate(chunks):
                        metadata_list.append({
                            'text': chunk,
                            'chunk_index': i,
                            'document_id': doc.id,
                            'filename': doc.filename,
                            'knowledge_base_id': doc.knowledge_base_id,
                            'user_id': doc.user_id
                        })
                    
                    # Add to index
                    if faiss_manager.index is None:
                        faiss_manager.create_index(
                            self.embedder.get_embedding_dimension()
                        )
                    
                    faiss_manager.add_embeddings(embeddings, metadata_list)
                    total_chunks += len(chunks)
                    
                except Exception as e:
                    logger.error(f"Error indexing document {doc.id}: {e}")
                    continue
            
            # Save index
            faiss_manager.save()
            
            logger.info(f"✅ Index rebuilt: {total_chunks} chunks from {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Error rebuilding index: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """Get RAG system statistics"""
        return {
            'faiss': faiss_manager.get_stats(),
            'embedding_model': self.embedder.model_name,
            'embedding_dimension': self.embedder.get_embedding_dimension()
        }


# Lazy-loaded global instance (avoids blocking at startup)
_rag_service_instance = None

def get_rag_service() -> RAGService:
    """Get or create RAG service singleton (lazy loading)"""
    global _rag_service_instance
    if _rag_service_instance is None:
        logger.info("Initializing RAG Service (lazy loading)...")
        _rag_service_instance = RAGService()
    return _rag_service_instance

# Backward-compatible proxy - acts like the service
class _RAGServiceProxy:
    def __getattr__(self, name):
        return getattr(get_rag_service(), name)

rag_service = _RAGServiceProxy()
