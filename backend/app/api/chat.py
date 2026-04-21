"""API endpoints for Chat Conversations and Messages"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any
import logging
import uuid
from datetime import datetime

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationWithMessages,
    MessageResponse,
    ChatRequest
)
from app.services.rag_service import rag_service
from app.services.chat_service import chat_service
from app.schemas.knowledge import QueryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


# ==================== Conversation CRUD ====================

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conv_data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new chat conversation"""
    try:
        conversation = Conversation(
            user_id=current_user.id,
            title=conv_data.title,
            meta_data=conv_data.meta_data,
            knowledge_base_id=conv_data.knowledge_base_id
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        logger.info(f"Created conversation: {conversation.id} for user {current_user.id}")
        return conversation
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all conversations for the current user"""
    try:
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.knowledge_base))
            .filter(Conversation.user_id == current_user.id)
            .order_by(Conversation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        conversations = result.scalars().all()
        
        # Populate knowledge_base_name for each conversation
        for conv in conversations:
            if conv.knowledge_base:
                conv.knowledge_base_name = conv.knowledge_base.name
                
        return conversations
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversation details with message history"""
    result = await db.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.messages),
            selectinload(Conversation.knowledge_base)
        )
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalars().first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.knowledge_base:
        conversation.knowledge_base_name = conversation.knowledge_base.name
        
    return conversation


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: uuid.UUID,
    conv_update: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update conversation title or metadata"""
    result = await db.execute(
        select(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalars().first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conv_update.title is not None:
        conversation.title = conv_update.title
    if conv_update.status is not None:
        conversation.status = conv_update.status
    if conv_update.meta_data is not None:
        # Merge or replace metadata? Usually replace in CRUD
        conversation.meta_data = conv_update.meta_data
        
    await db.commit()
    await db.refresh(conversation)
    
    return conversation


@router.put("/conversations/{conversation_id}/knowledge-base", response_model=ConversationResponse)
async def link_knowledge_base(
    conversation_id: uuid.UUID,
    kb_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Link or unlink a knowledge base to a conversation"""
    result = await db.execute(
        select(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalars().first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    kb_id = kb_data.get("knowledge_base_id")
    if kb_id:
        conversation.knowledge_base_id = uuid.UUID(kb_id) if isinstance(kb_id, str) else kb_id
    else:
        conversation.knowledge_base_id = None
        
    await db.commit()
    await db.refresh(conversation)
    
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation and all its messages"""
    result = await db.execute(
        select(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalars().first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.delete(conversation)
    await db.commit()
    
    return None


# ==================== Message Retrieval ====================

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all messages for a specific conversation"""
    # Verify ownership of conversation first
    check_query = await db.execute(
        select(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    if not check_query.scalars().first():
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.execute(
        select(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    return messages


# ==================== Chat Interaction ====================

@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to a conversation and get a response from the AI (Authenticated users only).
    Handles history saving and retrieval automatically.
    ✨ Auto-creates conversation if conversation_id is not provided.
    """
    try:
        conversation_id = chat_request.conversation_id
        
        # Auto-create conversation if needed
        if not conversation_id:
            logger.info(f"Creating new conversation for user {current_user.id}")
            new_conversation = Conversation(
                user_id=current_user.id,
                title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                knowledge_base_id=chat_request.knowledge_base_id
            )
            db.add(new_conversation)
            await db.flush()
            conversation_id = new_conversation.id
            logger.info(f"Created conversation {conversation_id}")
        
        response = await chat_service.generate_response(
            db=db,
            user_id=current_user.id,
            conversation_id=conversation_id,
            question=chat_request.question,
            top_k=chat_request.top_k
        )
        
        return QueryResponse(
            answer=response["content"],
            sources=response["sources"] or [],
            context_used=len(response["sources"]) if response["sources"] else 0,
            model=response.get("model", "unknown"),
            triggered_actions=response.get("triggered_actions"),
            conversation_id=conversation_id
        )
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in chat execution: {e}")
        raise HTTPException(status_code=500, detail="Error processing your request")


@router.post("/ask-public", response_model=QueryResponse)
async def ask_question_public(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to the public ChatBot (No authentication required).
    ✨ NEW: Now tracks visitors and captures leads.
    
    Features:
    - Tracks anonymous sessions using session_id
    - Extracts contact info (email, phone, name) from messages
    - Detects user intent and proposes email capture at right time
    - Manages lead status transitions
    - ✨ SAFETY: Requires knowledge_base_id to ensure strict data isolation per tenant
    """
    try:
        # ✨ KB ISOLATION CHECK: Ensure all public queries are scoped to a specific KB
        if not chat_request.knowledge_base_id:
            raise HTTPException(
                status_code=400,
                detail="public chat requires knowledge_base_id parameter for data isolation"
            )
        
        from app.services.lead_service import LeadCaptureService
        from app.models.lead import Lead, LeadStatus
        from app.models.message import Message
        from app.models.conversation import Conversation
        from sqlalchemy import select
        
        # ✨ STEP 1: Get or create conversation for this session
        conversation = None
        session_id = chat_request.session_id or str(uuid.uuid4())
        
        if session_id:
            result = await db.execute(
                select(Conversation)
                .options(selectinload(Conversation.lead))
                .filter(Conversation.session_id == session_id)
            )
            conversation = result.scalars().first()
        
        if not conversation:
            # Create new conversation for this public visitor
            conversation = Conversation(
                user_id=None,  # ✨ Public conversation, no admin
                session_id=session_id,
                title=f"Public Chat - {session_id[:8]}",
                meta_data={
                    'public_chat': True,
                    'started_at': datetime.utcnow().isoformat(),
                    'engagement_metrics': {
                        'message_count': 0,
                        'keywords': []
                    }
                }
            )
            db.add(conversation)
            await db.flush()
        
        # ✨ STEP 2: Extract lead information from message
        lead_service = LeadCaptureService(None)
        extracted_info = await lead_service.extract_lead_info(chat_request.question)
        
        # ✨ STEP 3: Detect user intent
        intent = await lead_service.detect_intent(chat_request.question)
        
        # ✨ STEP 4: Update conversation metrics
        conversation.meta_data['engagement_metrics']['message_count'] = conversation.meta_data.get('engagement_metrics', {}).get('message_count', 0) + 1
        current_keywords = conversation.meta_data.get('engagement_metrics', {}).get('keywords', [])
        if intent not in current_keywords:
            current_keywords.append(intent)
        conversation.meta_data['engagement_metrics']['keywords'] = current_keywords
        
        # ✨ STEP 5: Store user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=chat_request.question,
            meta_data={'intent': intent}
        )
        db.add(user_message)
        await db.flush()
        
        # ✨ STEP 6: Call RAG service to get answer
        rag_response = await rag_service.query(
            question=chat_request.question,
            knowledge_base_id=str(chat_request.knowledge_base_id) if chat_request.knowledge_base_id else None,
            top_k=chat_request.top_k,
            include_sources=True
        )
        
        answer = rag_response.get("answer", "")
        
        # ✨ STEP 7: Determine if we should propose email capture
        message_count = conversation.meta_data['engagement_metrics']['message_count']
        # Calculate session duration in seconds from conversation creation
        session_duration = int((datetime.utcnow() - conversation.created_at).total_seconds())
        should_capture = await lead_service.should_capture_email(
            conversation=conversation,
            intent=intent,
            message_count=message_count,
            session_duration=session_duration
        )
        
        # ✨ STEP 8: Only propose email capture if needed (no email provided yet)
        if should_capture and not extracted_info.get('email') and not conversation.lead_id:
            # No email yet, propose to capture
            proposal = "\n\nSi vous voulez, je peux vous envoyer un devis ou planifier une démo gratuite. Vous pouvez me partager votre email ou votre numéro de téléphone."
            answer += proposal
        
        # ✨ STEP 9: Create or update lead
        lead = await lead_service.create_or_update_lead(
            db=db,
            session_id=session_id,
            intent=intent,
            extracted_info=extracted_info,
            message_count=message_count,
            session_duration=session_duration,
            keywords=[intent],
            email_capture_method='AI_PROPOSAL' if should_capture else None
        )
        
        # ✨ STEP 10: Link lead to conversation if created
        if lead and not conversation.lead_id:
            conversation.lead_id = lead.id
        
        # ✨ STEP 10b: Check if we should ask for name
        should_capture_name = False
        name_prompt = None
        if lead:
            should_capture_name = await lead_service.should_capture_name(lead, extracted_info)
            if should_capture_name:
                name_prompt = lead_service.generate_name_capture_prompt(extracted_info)
                answer += f"\n\n{name_prompt}"
        
        # Store AI response
        ai_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            meta_data={'sources_count': len(rag_response.get("sources", []))}
        )
        db.add(ai_message)
        
        await db.commit()
        
        # ✨ STEP 11: Trigger CRM sync if lead has email
        triggered_actions = None
        if lead and lead.email:
            from app.services.action_service import action_service
            try:
                logger.info(f"🔄 Triggering CRM sync for lead {lead.email}")
                actions = await action_service.detect_and_handle_actions(
                    db=db,
                    conversation_id=conversation.id,
                    user_message=chat_request.question,
                    assistant_response=answer
                )
                # Convert Action objects to dicts for JSON response
                if actions:
                    triggered_actions = [
                        {
                            "id": str(a.id),
                            "action_type": a.action_type.value,
                            "status": a.status.value,
                            "created_at": a.created_at.isoformat() if hasattr(a.created_at, 'isoformat') else str(a.created_at)
                        }
                        for a in actions
                    ]
                logger.info(f"✅ CRM sync triggered: {len(triggered_actions) if triggered_actions else 0} actions")
            except Exception as e:
                logger.error(f"Error triggering CRM actions: {e}", exc_info=True)
                # Don't fail the chat if CRM sync fails
        
        # ✨ STEP 12: Prepare response with lead info
        lead_info = None
        if lead:
            lead_info = {
                'lead_id': str(lead.id),
                'status': lead.status.value,
                'email_detected': lead.email is not None,
                'phone_detected': lead.phone is not None,
                'contact_proposed': should_capture and not extracted_info.get('email'),
                'name_requested': should_capture_name,  # ✨ NEW: Flag to show name form
            }
        
        return QueryResponse(
            answer=answer,
            sources=rag_response.get("sources", []),
            context_used=rag_response.get("context_used", 0),
            model=settings.OPENROUTER_MODEL,
            retrieval=rag_response.get("retrieval"),
            triggered_actions=triggered_actions,  # ✨ NOW: Public chat DOES trigger actions
            lead_info=lead_info  # ✨ NEW: Include lead info in response
        )
    
    except ValueError as e:
        logger.error(f"ValueError in public chat: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in public chat execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing your request")
