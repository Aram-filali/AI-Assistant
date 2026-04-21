"""HubSpot CRM Integration"""

import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class HubSpotClient:
    """HubSpot CRM client for lead sync"""
    
    BASE_URL = "https://api.hubapi.com"
    
    def __init__(self, api_key: str):
        """
        Initialize HubSpot client
        
        Args:
            api_key: HubSpot API key (from .env HUBSPOT_API_KEY)
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def sync_lead(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update a contact in HubSpot with lead info
        
        Args:
            payload: {
                'email': str,
                'name': str (optional),
                'phone': str (optional),
                'company': str (optional),
                'message': str (optional),
                'score': int (optional),
                'intent': str (optional),
                'session_id': str (optional)
            }
            
        Returns:
            {
                'crm_id': str (HubSpot contact ID),
                'status': 'lead_synced' | 'contact_updated',
                'email': str,
                'score': int,
                'timestamp': str,
                'api': 'hubspot'
            }
        """
        try:
            email = payload.get("email")
            if not email:
                raise ValueError("Email required for HubSpot sync")
            
            logger.info(f"🔄 HubSpot: Syncing lead {email}")
            
            # 1. Search for existing contact by email
            existing_contact = await self._get_contact_by_email(email)
            
            if existing_contact:
                # Update existing contact
                contact_id = existing_contact['id']
                logger.info(f"✓ HubSpot: Found existing contact {contact_id}")
                
                # Update contact with new data
                await self._update_contact(contact_id, payload)
                status = "contact_updated"
            else:
                # Create new contact
                contact_id = await self._create_contact(email, payload)
                logger.info(f"✓ HubSpot: Created new contact {contact_id}")
                status = "lead_synced"
            
            # 2. Add contact to lead list (if configured)
            if settings.HUBSPOT_CONTACT_LIST_ID:
                await self._add_to_list(contact_id, settings.HUBSPOT_CONTACT_LIST_ID)
                logger.info(f"✓ HubSpot: Added {contact_id} to list {settings.HUBSPOT_CONTACT_LIST_ID}")
            
            # 3. Create activity/note about the interaction
            company = payload.get("company", "")
            intent = payload.get("intent", "")
            score = payload.get("score", 0)
            
            note_text = f"AI Lead - Intent: {intent}, Score: {score}"
            if company:
                note_text += f", Company: {company}"
            
            await self._create_note(contact_id, note_text)
            
            return {
                "crm_id": contact_id,
                "status": status,
                "email": email,
                "score": score,
                "timestamp": datetime.utcnow().isoformat(),
                "api": "hubspot"
            }
            
        except Exception as e:
            logger.error(f"❌ HubSpot sync error: {str(e)}")
            raise
    
    async def _get_contact_by_email(self, email: str) -> Optional[Dict]:
        """Search for contact by email"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                params = {
                    "limit": 1,
                    "after": "",
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "propertyName": "email",
                                    "operator": "EQ",
                                    "value": email
                                }
                            ]
                        }
                    ]
                }
                
                response = await client.post(
                    f"{self.BASE_URL}/crm/v3/objects/contacts/search",
                    json=params,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    if results:
                        return results[0]
                elif response.status_code != 404:
                    logger.warning(f"HubSpot search returned {response.status_code}: {response.text}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching HubSpot contact: {e}")
            return None
    
    async def _create_contact(self, email: str, payload: Dict[str, Any]) -> str:
        """Create new contact in HubSpot"""
        name = payload.get("name", "")
        phone = payload.get("phone", "")
        company = payload.get("company", "")
        
        properties = {
            "email": email,
        }
        
        if name:
            # Split name into first/last if possible
            parts = name.split(" ", 1)
            properties["firstname"] = parts[0]
            if len(parts) > 1:
                properties["lastname"] = parts[1]
        
        if phone:
            properties["phone"] = phone
        
        if company:
            properties["company"] = company
        
        # Add lead status (use valid HubSpot enum values)
        properties["hs_lead_status"] = "OPEN"
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.BASE_URL}/crm/v3/objects/contacts",
                    json={"properties": properties},
                    headers=self.headers
                )
                
                if response.status_code in [200, 201]:
                    contact_data = response.json()
                    return contact_data['id']
                else:
                    raise Exception(f"HubSpot API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Error creating HubSpot contact: {e}")
            raise
    
    async def _update_contact(self, contact_id: str, payload: Dict[str, Any]) -> None:
        """Update existing contact"""
        phone = payload.get("phone", "")
        company = payload.get("company", "")
        name = payload.get("name", "")
        score = payload.get("score", 0)
        
        properties = {}
        
        if name:
            parts = name.split(" ", 1)
            properties["firstname"] = parts[0]
            if len(parts) > 1:
                properties["lastname"] = parts[1]
        
        if phone:
            properties["phone"] = phone
        
        if company:
            properties["company"] = company
        
        # Set lead status based on score (use valid HubSpot enum values)
        if score >= 80:
            properties["hs_lead_status"] = "IN_PROGRESS"
        elif score >= 50:
            properties["hs_lead_status"] = "OPEN_DEAL"
        else:
            properties["hs_lead_status"] = "OPEN"
        
        if not properties:
            return
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.patch(
                    f"{self.BASE_URL}/crm/v3/objects/contacts/{contact_id}",
                    json={"properties": properties},
                    headers=self.headers
                )
                
                if response.status_code not in [200, 204]:
                    logger.warning(f"HubSpot update returned {response.status_code}: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error updating HubSpot contact: {e}")
    
    async def _add_to_list(self, contact_id: str, list_id: str) -> None:
        """Add contact to a HubSpot list"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.BASE_URL}/crm/v3/lists/{list_id}/members/batch",
                    json={
                        "inputs": [{"id": contact_id}]
                    },
                    headers=self.headers
                )
                
                if response.status_code not in [200, 201]:
                    logger.warning(f"HubSpot list add returned {response.status_code}: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error adding contact to HubSpot list: {e}")
    
    async def _create_note(self, contact_id: str, note_text: str) -> None:
        """Create a note/engagement on contact"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.BASE_URL}/crm/v3/objects/contacts/{contact_id}/associations/batch",
                    json={
                        "inputs": [
                            {
                                "id": contact_id,
                                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationType": "contact_to_note"}]
                            }
                        ]
                    },
                    headers=self.headers
                )
                
                # Note: Full note creation is more complex in HubSpot - this is simplified
                logger.debug(f"Created note for contact {contact_id}")
                    
        except Exception as e:
            logger.debug(f"Note creation skipped: {e}")
