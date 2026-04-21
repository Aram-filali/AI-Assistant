"""Service for managing leads and capturing visitor information"""

import logging
import re
from typing import Dict, Optional, List
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.lead import Lead, LeadStatus
from app.models.conversation import Conversation
from app.core.rag.generator import RAGGenerator

logger = logging.getLogger(__name__)


class LeadCaptureService:
    """Handle lead capture, status updates, and engagement tracking"""
    
    def __init__(self, generator: RAGGenerator):
        self.generator = generator
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+?33|0)[1-9](?:[0-9]{8}|[0-9]{9})|(?:\+\d{1,3})?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}')
    
    async def extract_lead_info(self, message: str) -> Dict[str, Optional[str]]:
        """
        Extract email and phone from user message using pattern matching.
        Name is NOT extracted automatically - must be captured explicitly by the user.
        
        Returns:
            Dict with 'email', 'phone', 'name' keys (name always None)
        """
        extracted = {
            'email': None,
            'name': None,  # ✨ Always None - name must be provided explicitly by user
            'phone': None
        }
        
        # Extract email
        email_match = self.email_pattern.search(message)
        if email_match:
            extracted['email'] = email_match.group(0)
        
        # Extract phone (simple pattern for French numbers)
        phone_match = self.phone_pattern.search(message)
        if phone_match:
            extracted['phone'] = phone_match.group(0)
        
        return extracted
    
    async def detect_intent(self, message: str, conversation_history: List[Dict] = None) -> str:
        """
        Detect user intent from message
        
        Returns:
            Intent string like 'PRICING_REQUEST', 'DEMO_REQUEST', etc.
        """
        message_lower = message.lower()
        
        # Define intent keywords
        intent_keywords = {
            'PRICING_REQUEST': ['tarif', 'prix', 'coût', 'combien', 'facture', 'devis', 'coûte'],
            'DEMO_REQUEST': ['démo', 'demo', 'essai', 'test', 'voir', 'montrer', 'présentation'],
            'TECHNICAL_FEATURES': ['api', 'intégration', 'webhook', 'endpoint', 'technique', 'authentification', 'code'],
            'COMPARISON': ['vs', 'comparer', 'différence', 'competitor', 'concurrence', 'avantage'],
            'USE_CASE_EXPLANATION': ['mon cas', 'ma situation', 'mon besoin', 'mon entreprise', 'notre besoin', 'nous avons besoin'],
            'POSITIVE_SIGNAL': ['merci', 'bien', 'parfait', 'intéressé', 'ok', 'cool', 'excellent', 'super'],
            'SUPPORT': ['problème', 'erreur', 'bug', 'ne marche pas', 'help', 'aide', 'déboguer'],
        }
        
        detected_intents = []
        for intent, keywords in intent_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_intents.append(intent)
        
        # Return primary intent or default
        return detected_intents[0] if detected_intents else 'GENERAL_INQUIRY'
    
    async def should_capture_email(self, conversation: Conversation, intent: str, 
                                   message_count: int, session_duration: int) -> bool:
        """
        Determine if bot should propose email/contact capture
        
        Returns:
            True if bot should ask for contact info
        """
        # Already has email
        if conversation.lead_id and conversation.lead:
            return False
        
        # Check triggers
        email_triggers = {
            'PRICING_REQUEST': True,
            'DEMO_REQUEST': True,
            'COMPARISON': True,
            'USE_CASE_EXPLANATION': True,
        }
        
        # Trigger 1: Intent-based
        if email_triggers.get(intent, False):
            return True
        
        # Trigger 2: Time-based (5+ minutes)
        if session_duration > 300 and message_count >= 2:
            return True
        
        # Trigger 3: Multiple messages
        if message_count >= 4 and intent != 'GENERAL_INQUIRY':
            return True
        
        return False
    
    async def should_capture_name(self, lead: 'Lead', extracted_info: Dict[str, Optional[str]]) -> bool:
        """
        Determine if bot should propose name capture
        
        Returns:
            True if we should ask for name
        """
        # Already has name
        if lead and lead.name:
            return False
        
        # Ask for name if we just got email or phone
        has_contact = extracted_info.get('email') or extracted_info.get('phone')
        return has_contact
    
    def generate_name_capture_prompt(self, extracted_info: Dict[str, Optional[str]]) -> str:
        """
        Generate a conversational prompt asking for name, with optional company.
        """
        if extracted_info.get('email') and extracted_info.get('phone'):
            return "Super, merci. Pour personnaliser la suite, quel est votre nom ? Vous pouvez aussi ajouter le nom de votre entreprise si vous le souhaitez."
        elif extracted_info.get('email'):
            return "Parfait, merci. Pour continuer, quel est votre nom ? Vous pouvez aussi indiquer votre entreprise (optionnel)."
        elif extracted_info.get('phone'):
            return "Merci, c'est bien noté. Quel est votre nom ? Et si vous voulez, le nom de votre entreprise."
        return None
    
    async def create_or_update_lead(
        self,
        db: AsyncSession,
        session_id: str,
        intent: str,
        extracted_info: Dict[str, Optional[str]],
        message_count: int,
        session_duration: int,
        keywords: List[str],
        email_capture_method: Optional[str] = None
    ) -> Optional[Lead]:
        """
        Create new lead or update existing one
        
        Returns:
            Created/Updated Lead object
        """
        try:
            # Try to find existing lead by email or session
            existing_lead = None
            
            if extracted_info.get('email'):
                result = await db.execute(
                    select(Lead).filter(Lead.email == extracted_info['email'])
                )
                existing_lead = result.scalars().first()
            
            # Update or create
            if existing_lead:
                # Update existing lead
                if not existing_lead.meta_data:
                    existing_lead.meta_data = {}
                
                # Update extracted info
                if extracted_info.get('email'):
                    existing_lead.email = extracted_info['email']
                if extracted_info.get('name'):
                    existing_lead.name = extracted_info['name']
                if extracted_info.get('phone'):
                    existing_lead.phone = extracted_info['phone']
                
                # Update metadata
                existing_lead.meta_data['message_count'] = message_count
                existing_lead.meta_data['session_duration'] = session_duration
                existing_lead.meta_data['keywords'] = list(set(existing_lead.meta_data.get('keywords', []) + keywords))
                existing_lead.meta_data['session_id'] = session_id
                session_ids = existing_lead.meta_data.get('session_ids', [])
                if session_id not in session_ids:
                    session_ids.append(session_id)
                existing_lead.meta_data['session_ids'] = session_ids
                existing_lead.meta_data['last_message_at'] = datetime.utcnow().isoformat()
                if email_capture_method:
                    existing_lead.meta_data['email_capture_method'] = email_capture_method
                
                # Update status if needed
                new_status = self._calculate_status(existing_lead.status, message_count, extracted_info)
                if new_status.value != existing_lead.status.value:
                    existing_lead.meta_data['previous_statuses'] = existing_lead.meta_data.get('previous_statuses', []) + [existing_lead.status.value]
                    existing_lead.status = new_status

                # Ensure current session conversation is linked to existing lead
                result = await db.execute(
                    select(Conversation).filter(Conversation.session_id == session_id)
                )
                conversation = result.scalars().first()
                if conversation and not conversation.lead_id:
                    conversation.lead_id = existing_lead.id
                
                await db.flush()
                return existing_lead
            else:
                initial_status = self._calculate_status(LeadStatus.NEW, message_count, extracted_info)
                # Create new lead
                new_lead = Lead(
                    email=extracted_info.get('email'),
                    name=extracted_info.get('name'),
                    phone=extracted_info.get('phone'),
                    status=initial_status,
                    meta_data={
                        'message_count': message_count,
                        'session_duration': session_duration,
                        'keywords': keywords,
                        'session_id': session_id,
                        'session_ids': [session_id],
                        'last_message_at': datetime.utcnow().isoformat(),
                        'trigger_type': intent,
                        'email_capture_method': email_capture_method or 'UNKNOWN',
                        'notes': '',
                        'previous_statuses': []
                    }
                )
                db.add(new_lead)
                await db.flush()
                
                # ✨ NEW: Link the conversation to this lead immediately
                # This ensures ALL messages from the session are counted
                result = await db.execute(
                    select(Conversation).filter(Conversation.session_id == session_id)
                )
                conversation = result.scalars().first()
                if conversation and not conversation.lead_id:
                    conversation.lead_id = new_lead.id
                    await db.flush()
                
                return new_lead
        
        except Exception as e:
            logger.error(f"Error creating/updating lead: {e}")
            return None
    
    def _calculate_status(self, current_status: LeadStatus, message_count: int, 
                         extracted_info: Dict[str, Optional[str]]) -> LeadStatus:
        """
        Calculate new lead status based on engagement metrics
        """
        # NEW → ENGAGED: 3+ messages OR 2+ min
        if current_status == LeadStatus.NEW and message_count >= 3:
            return LeadStatus.ENGAGED
        
        # ENGAGED/NEW → QUALIFIED: Email provided OR requested devis
        if extracted_info.get('email') and current_status in [LeadStatus.NEW, LeadStatus.ENGAGED]:
            return LeadStatus.QUALIFIED
        
        # Otherwise keep current
        return current_status
    
    def get_engagement_level(self, message_count: int, session_duration: int) -> str:
        """
        Calculate engagement level for AI context
        """
        if message_count >= 5 and session_duration >= 300:
            return "HIGH"
        elif message_count >= 3 or session_duration >= 180:
            return "MEDIUM"
        else:
            return "LOW"


# Global instance
lead_capture_service = LeadCaptureService(generator=None)  # Will be properly initialized
