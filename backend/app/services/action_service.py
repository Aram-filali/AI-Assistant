import logging
import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import asyncio
import resend

from app.core.config import settings
from app.models.action import Action, ActionType, ActionStatus

logger = logging.getLogger(__name__)

class ActionService:
    """Service to handle automated actions like sending emails and CRM syncing."""

    def __init__(self):
        # Configure Resend
        if settings.RESEND_API_KEY and settings.RESEND_API_KEY != "re_123456789":
            resend.api_key = settings.RESEND_API_KEY
        else:
            logger.warning("RESEND_API_KEY not configured. Emails will be mocked.")

    async def create_action(
        self,
        db: AsyncSession,
        conversation_id: uuid.UUID,
        action_type: ActionType,
        payload: Dict[str, Any]
    ) -> Action:
        """Create a new action record in PENDING state."""
        action = Action(
            conversation_id=conversation_id,
            action_type=action_type,
            status=ActionStatus.PENDING,
            payload=payload
        )
        db.add(action)
        await db.flush()
        await db.commit()
        await db.refresh(action)
        return action

    async def execute_action(self, db: AsyncSession, action_id: uuid.UUID) -> Dict[str, Any]:
        """Execute a pending action based on its type."""
        # 1. Fetch action
        result = await db.execute(select(Action).filter(Action.id == action_id))
        action = result.scalars().first()
        
        if not action:
            raise ValueError(f"Action {action_id} not found")
            
        if action.status != ActionStatus.PENDING:
            return action.result
            
        action.status = ActionStatus.PROCESSING
        await db.commit()
        
        try:
            result_data = {}
            if action.action_type == ActionType.EMAIL:
                result_data = await self._send_email(action.payload)
            elif action.action_type == ActionType.CRM:
                result_data = await self._sync_crm(action.payload)
            elif action.action_type == ActionType.SCORING:
                result_data = await self._calculate_score(action.payload)
            elif action.action_type == ActionType.TICKET:
                result_data = await self._create_ticket(action.payload)
            else:
                raise ValueError(f"Unsupported action type: {action.action_type}")
            
            action.status = ActionStatus.DONE
            action.result = result_data
            action.executed_at = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error(f"Error executing action {action_id}: {str(e)}")
            action.status = ActionStatus.FAILED
            action.result = {"error": str(e)}
            result_data = action.result
            
        await db.commit()
        return result_data

    async def _send_email(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send email using Resend API."""
        to = payload.get("to")
        subject = payload.get("subject", "Notification de l'Assistant IA")
        html = payload.get("html", "<p>Message de votre assistant IA.</p>")
        
        if not to:
            raise ValueError("Email payload missing required 'to' field")

        if settings.RESEND_API_KEY and settings.RESEND_API_KEY != "re_123456789":
            try:
                params = {
                    "from": settings.FROM_EMAIL,
                    "to": to,
                    "subject": subject,
                    "html": html,
                }
                r = resend.Emails.send(params)
                return {"id": r.get("id"), "sent": True, "api": "resend"}
            except Exception as e:
                logger.error(f"Resend error: {str(e)}")
                raise
        else:
            # Mock sending
            logger.info(f"MOCK EMAIL SENT to {to}: {subject}")
            return {"mock": True, "sent": True, "to": to, "subject": subject}

    async def _sync_crm(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronize lead to CRM system (HubSpot, Salesforce, etc).
        
        Structure supports real CRM integration:
        - Set HUBSPOT_API_KEY or SALESFORCE_* in env to enable real sync
        - Otherwise falls back to mock for development/testing
        """
        email = payload.get("email")
        if not email:
            raise ValueError("CRM sync requires user email")
        
        logger.info(f"CRM SYNC: Processing lead <{email}>")
        
        # Route to real CRM if configured, else use mock
        hubspot_key = getattr(settings, "HUBSPOT_API_KEY", "")
        salesforce_instance = getattr(settings, "SALESFORCE_INSTANCE", "")
        crm_enabled = bool(hubspot_key) or bool(salesforce_instance)
        
        if crm_enabled:
            return await self._sync_crm_real(payload)
        else:
            return await self._sync_crm_mock(payload)
    
    async def _sync_crm_real(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Real CRM integration - route to HubSpot or Salesforce
        
        Supports:
        - HubSpot: Create/update contact via API key
        - Salesforce: Create/update lead via OAuth
        """
        try:
            # Try HubSpot first if configured
            if settings.HUBSPOT_API_KEY and settings.HUBSPOT_API_KEY != "":
                logger.info("🔗 Using HubSpot CRM for sync")
                from app.integrations.hubspot import HubSpotClient
                try:
                    client = HubSpotClient(settings.HUBSPOT_API_KEY)
                    return await client.sync_lead(payload)
                except Exception as e:
                    logger.error(f"HubSpot sync failed, falling back to mock: {e}")
                    return await self._sync_crm_mock(payload)
            
            # Try Salesforce if configured
            elif settings.SALESFORCE_INSTANCE and settings.SALESFORCE_INSTANCE != "":
                logger.info("🔗 Using Salesforce CRM for sync")
                from app.integrations.salesforce import SalesforceClient
                try:
                    client = SalesforceClient(
                        instance=settings.SALESFORCE_INSTANCE,
                        client_id=settings.SALESFORCE_CLIENT_ID,
                        client_secret=settings.SALESFORCE_CLIENT_SECRET,
                        username=settings.SALESFORCE_USERNAME,
                        password=settings.SALESFORCE_PASSWORD,
                        security_token=settings.SALESFORCE_SECURITY_TOKEN
                    )
                    return await client.sync_lead(payload)
                except Exception as e:
                    logger.error(f"Salesforce sync failed, falling back to mock: {e}")
                    return await self._sync_crm_mock(payload)
            
            else:
                logger.warning("⚠️ No CRM configured (HUBSPOT_API_KEY or SALESFORCE_INSTANCE missing) - using mock")
                return await self._sync_crm_mock(payload)
                
        except Exception as e:
            logger.error(f"CRM routing error: {e}")
            return await self._sync_crm_mock(payload)
    
    async def _sync_crm_mock(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Mock CRM synchronization for Lead creation/update (for testing/development)."""
        await asyncio.sleep(0.5)  # Simulate API latency
        
        email = payload.get("email")
        crm_id = f"crm_{uuid.uuid4().hex[:8]}"
        score = payload.get("score", 0)
        
        result = {
            "crm_id": crm_id,
            "status": "lead_synced",
            "email": email,
            "score": score,
            "timestamp": datetime.utcnow().isoformat(),
            "mock": True
        }
        
        logger.info(f"✓ MOCK CRM SYNC: Generated {crm_id} for {email} (score: {score})")
        return result

    async def _calculate_score(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lead scoring based on conversation keywords/intent."""
        score = 0
        reasons = []
        
        text = str(payload.get("text", "")).lower()
        
        # Heuristics
        intent_map = {
            "acheter": 30, "prix": 20, "tarif": 20, "devis": 25, "demo": 15,
            "commander": 30, "test": 10, "besoin": 10
        }
        
        for key, val in intent_map.items():
            if key in text:
                score += val
                reasons.append(f"Mot-clé détecté: {key} (+{val})")
        
        # Limite à 100
        score = min(score, 100)
        
        return {
            "score": score,
            "reasons": reasons,
            "level": "HOT" if score >= 60 else ("WARM" if score >= 30 else "COLD")
        }

    async def _create_ticket(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Mock ticket creation (Zendesk/Jira)."""
        logger.info(f"TICKET CREATION: {payload.get('subject')}")
        return {
            "ticket_id": f"TKT-{uuid.uuid4().hex[:6].upper()}",
            "status": "OPEN",
            "priority": payload.get("priority", "NORMAL")
        }

    async def detect_and_handle_actions(
        self,
        db: AsyncSession,
        conversation_id: uuid.UUID,
        user_message: str,
        assistant_response: str,
        history: List[Dict[str, str]] = None
    ) -> List[Action]:
        """Analyze message to auto-trigger actions (Emails, CRM, Scoring)."""
        actions = []
        user_msg_low = user_message.lower()
        resp_low = assistant_response.lower()

        # 1. Scoring (Lead Qualification) - Always done to refine lead profile
        scoring_payload = {"text": f"User: {user_message} | Assistant: {assistant_response}"}
        score_action = await self.create_action(db, conversation_id, ActionType.SCORING, scoring_payload)
        await self.execute_action(db, score_action.id)
        actions.append(score_action)
        
        # 2. Email Detection
        # Triggers for assistant promising to send something
        email_triggers = ["envoi", "send", "mail", "courriel", "reçois", "receive"]
        if any(t in resp_low for t in email_triggers):
            email_payload = {
                "to": None, # Will be filled if found in history/meta
                "subject": "Suivi de notre échange - AI Assistant",
                "html": f"<p>Bonjour,</p><p>Suite à notre discussion :</p><blockquote>{assistant_response}</blockquote>",
                "status": "waiting_for_email_address"
            }
            # Attempt to find email in user message
            import re
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', user_message)
            if emails:
                email_payload["to"] = emails[0]
                
            email_action = await self.create_action(db, conversation_id, ActionType.EMAIL, email_payload)
            actions.append(email_action)

        # 3. CRM Sync Detection
        # If user provides lots of info or shows very high intent
        high_intent = ["acheter", "devis", "tarif", "commander"]
        if any(w in user_msg_low for w in high_intent):
            crm_payload = {
                "email": None,
                "msg": user_message,
                "intent": "purchase_intent"
            }
            # Extract email if possible
            import re
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', user_message)
            if emails:
                crm_payload["email"] = emails[0]
                
            crm_action = await self.create_action(db, conversation_id, ActionType.CRM, crm_payload)
            # If we have the email, we can sync immediately
            if crm_payload["email"]:
                await self.execute_action(db, crm_action.id)
            actions.append(crm_action)

        return actions

action_service = ActionService()
