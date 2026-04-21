"""
Hybrid Chat Service - Orchestrate RAG and Standard Chat

This service implements the core chat logic with automatic mode selection:
- RAG Mode: If conversation has a linked Knowledge Base, use semantic search + LLM
- Standard Mode: If no KB, use LLM directly for general conversation
- Fallback: If RAG retrieves no relevant chunks, fall back to standard chat

Features:
- Preserves conversation history (last 5 messages for context)
- Tracks sources for RAG responses (transparency)
- Multi-tenant isolation (users see only their conversations)
- Async-first architecture for scalability
"""

import uuid
import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.services.rag_service import rag_service
from app.services.action_service import action_service
from app.core.rag.generator import rag_generator

logger = logging.getLogger(__name__)

class ChatService:
    """
    Hybrid chat orchestration service.
    
    Automatically determines chat mode (RAG vs Standard) and generates responses
    with or without document context based on conversation configuration.
    """

    async def generate_response(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        question: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Generate response for user question with automatic RAG detection.
        
        Flow:
        1. Validate conversation ownership (multi-tenant isolation)
        2. Load conversation history for context
        3. Save user message to DB
        4. Determine mode (RAG if KB linked, else standard)
        5. Generate response
        6. Save assistant message to DB
        7. Return response with metadata
        
        Args:
            db: Async database session
            user_id: Owner of conversation (for authorization)
            conversation_id: Which conversation to respond in
            question: User message content
            top_k: Number of document chunks to retrieve (default 5)
            
        Returns:
            Dict with keys: content, role, sources, rag_used, retrieval_score
        """
        # 1. LOAD CONVERSATION - with authorization check
        # Using selectinload to eager-load knowledge_base (prevents N+1 queries)
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.knowledge_base))
            .filter(
                Conversation.id == conversation_id, 
                Conversation.user_id == user_id  # Multi-tenant isolation
            )
        )
        conversation = result.scalars().first()
        
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found or unauthorized")

        # 2. RETRIEVE CONVERSATION HISTORY - for context window
        # Fetch last 5 messages to give LLM recent context
        history_result = await db.execute(
            select(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(5)
        )
        history_msgs = history_result.scalars().all()
        history_msgs.reverse()  # Convert to chronological order (oldest→newest)
        
        # Format history for LLM
        history_payload = [
            {
                "role": msg.role.value if hasattr(msg.role, 'value') else msg.role, 
                "content": msg.content
            }
            for msg in history_msgs
        ]

        # 3. SAVE USER MESSAGE - persist to DB before generating response
        user_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=question
        )
        db.add(user_message)
        await db.flush()  # Flush to get message ID, but don't commit yet

        # 4. INTELLIGENT MODE SELECTION - RAG if KB available, Standard otherwise
        response_data = None
        rag_used = False
        retrieval_score = 0.0
        sources = []
        fallback_message = None

        if conversation.knowledge_base_id:
            # ===== RAG MODE: Retrieve + Augment + Generate =====
            logger.info(f"🧠 Using RAG for conversation {conversation_id} with KB {conversation.knowledge_base_id}")
            
            try:
                # Retrieve semantically similar document chunks
                logger.debug(f"📚 Semantic search for: '{question}'")
                chunks = await rag_service.retriever.retrieve(
                    query=question,
                    top_k=top_k
                )
                logger.debug(f"✅ Retrieved {len(chunks)} total chunks")
                
                # MULTI-TENANT FILTERING: Only include chunks from this KB
                kb_id_str = str(conversation.knowledge_base_id)
                kb_chunks = []
                for c in chunks:
                    meta = c.get('metadata', {})
                    chunk_kb_id = str(meta.get('knowledge_base_id', ''))
                    if chunk_kb_id == kb_id_str:
                        kb_chunks.append(c)
                        sources.append({
                            'filename': meta.get('filename', 'unknown'),
                            'chunk_index': meta.get('chunk_index', 0),
                            'text_preview': c.get('content', '')[:100] + '...'  # First 100 chars
                        })
                
                logger.info(f"✅ Found {len(kb_chunks)} relevant chunks from KB {kb_id_str}")
                
                # Check if we have relevant context (minimum 1 chunk)
                if kb_chunks:
                    # Score check (heuristic)
                    avg_score = sum(c.get('score', 0) for c in kb_chunks) / len(kb_chunks)
                    retrieval_score = avg_score
                    logger.debug(f"Average retrieval score: {retrieval_score}")
                    
                    # Generate RAG response
                    logger.info("Calling RAG generator...")
                    response_data = await rag_generator.generate_response(
                        query=question,
                        context_chunks=kb_chunks,
                        history=history_payload
                    )
                    rag_used = True
                    sources = response_data.get('sources', [])
                else:
                    logger.info("No chunks found in KB, falling back to normal chat")
                    fallback_message = "💬 Je n'ai pas trouvé d'information pertinente dans vos documents. Voici ce que je peux dire en général :"
                    response_data = await self._generate_normal_response(
                        query=question,
                        history=history_payload,
                        prefix_message=fallback_message
                    )
                    rag_used = False

            except Exception as rag_err:
                logger.exception(f"Error during RAG execution: {rag_err}")
                # Fallback on RAG error
                fallback_message = "💬 Un problème est survenu lors de la recherche dans vos documents. Voici une réponse générale :"
                response_data = await self._generate_normal_response(
                    query=question,
                    history=history_payload,
                    prefix_message=fallback_message
                )
                rag_used = False
        else:
            # Mode chat normal
            logger.info(f"Using normal chat for conversation {conversation_id}")
            response_data = await self._generate_normal_response(
                query=question,
                history=history_payload
            )
            rag_used = False

        # 5. Save Assistant Message
        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=response_data['answer'],
            rag_used=rag_used,
            retrieval_score=retrieval_score if rag_used else None,
            sources=sources if rag_used else None,
            meta_data={
                "model": response_data.get('model'),
                "fallback": fallback_message is not None
            }
        )
        db.add(assistant_message)
        await db.flush()

        # 6. Action detection (the "Arms")
        try:
            triggered_actions = await action_service.detect_and_handle_actions(
                db=db,
                conversation_id=conversation_id,
                user_message=question,
                assistant_response=response_data['answer'],
                history=history_payload
            )
            # Add action metadata to message
            if triggered_actions:
                assistant_message.meta_data["triggered_actions"] = [str(a.id) for a in triggered_actions]
        except Exception as action_err:
            logger.error(f"Action detection failed: {action_err}")
            triggered_actions = []

        conversation.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(assistant_message)

        return {
            "id": assistant_message.id,
            "content": assistant_message.content,
            "role": assistant_message.role,
            "rag_used": assistant_message.rag_used,
            "retrieval_score": assistant_message.retrieval_score,
            "sources": assistant_message.sources,
            "fallback_message": fallback_message,
            "triggered_actions": [
                {"id": str(a.id), "type": a.action_type, "status": a.status}
                for a in triggered_actions
            ],
            "created_at": assistant_message.created_at
        }

    async def _generate_normal_response(
        self,
        query: str,
        history: List[Dict],
        prefix_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response without context (standard LLM chat)"""
        
        system_prompt = "Tu es un assistant intelligent et utile. Réponds de manière claire et concise."
        
        # Call generator with empty context
        response = await rag_generator._call_openrouter(
            system_prompt=system_prompt,
            user_prompt=query,
            history=history
        )
        
        answer = response['content']
        if prefix_message:
            answer = f"{prefix_message}\n\n{answer}"
            
        return {
            "answer": answer,
            "model": rag_generator.model,
            "usage": response.get('usage', {})
        }

    def format_conversation_history(self, messages: List[Message], limit: int = 10) -> str:
        """Helper to format history for prompts if needed outside generator"""
        recent = messages[-limit:]
        formatted = []
        for msg in recent:
            role = "Utilisateur" if msg.role == MessageRole.USER else "Assistant"
            formatted.append(f"[{role}]: {msg.content}")
        return "\n".join(formatted)

chat_service = ChatService()
