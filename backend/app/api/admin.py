"""Admin API endpoints for managing leads and analytics"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta
from io import StringIO
import csv
import logging
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.lead import Lead, LeadStatus
from app.models.message import Message, MessageRole
from app.schemas.chat import ConversationResponse
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==================== Request Models ====================

class LeadUpdateRequest(BaseModel):
    """Schema for updating lead"""
    name: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    status: Optional[LeadStatus] = None


def _safe_meta_message_count(lead: Lead) -> int:
    if not lead.meta_data:
        return 0
    return int(lead.meta_data.get("message_count", 0) or 0)


def _lead_session_ids(lead: Lead) -> list[str]:
    if not lead.meta_data:
        return []

    ids: list[str] = []
    single = lead.meta_data.get("session_id")
    if isinstance(single, str) and single:
        ids.append(single)

    many = lead.meta_data.get("session_ids")
    if isinstance(many, list):
        ids.extend([s for s in many if isinstance(s, str) and s])

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for item in ids:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


# ==================== Lead Management ====================

@router.get("/leads")
async def get_leads(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[LeadStatus] = None,
    search: Optional[str] = None,
):
    """
    Get all qualified leads (with email or phone) with filtering and pagination.
    ✨ Only shows leads that have provided contact information.
    
    Query Parameters:
    - skip: Pagination offset (default: 0)
    - limit: Results per page (default: 50, max: 100)
    - status: Filter by lead status (NEW, ENGAGED, QUALIFIED, CONTACTED, CONVERTED, ABANDONED)
    - search: Search by email or name
    """
    try:
        query = select(Lead)
        
        # ✨ Only show leads that have provided contact info (email OR phone)
        query = query.where(
            (Lead.email.isnot(None)) | (Lead.phone.isnot(None))
        )
        
        # Apply status filter
        if status:
            query = query.where(Lead.status == status)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Lead.email.ilike(search_term)) | 
                (Lead.name.ilike(search_term)) |
                (Lead.company_name.ilike(search_term))
            )
        
        # Order by created_at descending
        query = query.order_by(desc(Lead.created_at))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        leads = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(Lead.id)).where(
            (Lead.email.isnot(None)) | (Lead.phone.isnot(None))
        )
        if status:
            count_query = count_query.where(Lead.status == status)
        if search:
            search_term = f"%{search}%"
            count_query = count_query.where(
                (Lead.email.ilike(search_term)) | 
                (Lead.name.ilike(search_term)) |
                (Lead.company_name.ilike(search_term))
            )
        
        result_count = await db.execute(count_query)
        total_count = result_count.scalar()
        
        # Calculate real message count for each lead
        leads_data = []
        for lead in leads:
            session_ids = _lead_session_ids(lead)

            count_where = [Conversation.lead_id == lead.id]
            if session_ids:
                count_where.append(Conversation.session_id.in_(session_ids))

            # Count USER messages from all conversations linked to this lead
            msg_count_result = await db.execute(
                select(func.count(Message.id))
                .select_from(Message)
                .join(Conversation, Message.conversation_id == Conversation.id)
                .where(or_(*count_where))
                .where(Message.role == MessageRole.USER)
            )
            linked_count = int(msg_count_result.scalar() or 0)

            # For historical leads created before proper conversation-linking,
            # fallback to engagement metrics persisted in meta_data.
            message_count = max(linked_count, _safe_meta_message_count(lead))
            
            leads_data.append({
                "id": str(lead.id),
                "email": lead.email,
                "name": lead.name,
                "phone": lead.phone,
                "company_name": lead.company_name,
                "status": lead.status,
                "message_count": message_count,  # ✨ Real count from database
                "created_at": lead.created_at.isoformat(),
                "updated_at": lead.updated_at.isoformat(),
                "contacted_at": lead.contacted_at.isoformat() if lead.contacted_at else None,
            })
        
        return {
            "data": leads_data,
            "total": total_count,
            "skip": skip,
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        raise HTTPException(status_code=500, detail="Error fetching leads")


@router.get("/leads/{lead_id}")
async def get_lead_detail(
    lead_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed view of a specific lead with conversation history"""
    try:
        result = await db.execute(
            select(Lead)
            .where(Lead.id == lead_id)
        )
        lead = result.scalars().first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Get conversations for this lead
        result_conv = await db.execute(
            select(Conversation)
            .where(Conversation.lead_id == lead_id)
            .order_by(desc(Conversation.created_at))
        )
        conversations = result_conv.scalars().all()
        
        session_ids = _lead_session_ids(lead)
        count_where = [Conversation.lead_id == lead.id]
        if session_ids:
            count_where.append(Conversation.session_id.in_(session_ids))

        # Count total messages for this lead (user messages)
        msg_count_result = await db.execute(
            select(func.count(Message.id))
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(or_(*count_where))
            .where(Message.role == MessageRole.USER)
        )
        linked_count = int(msg_count_result.scalar() or 0)
        message_count = max(linked_count, _safe_meta_message_count(lead))
        
        return {
            "id": str(lead.id),
            "email": lead.email,
            "name": lead.name,
            "phone": lead.phone,
            "company_name": lead.company_name,
            "status": lead.status,
            "message_count": message_count,  # ✨ Real count
            "meta_data": lead.meta_data,
            "created_at": lead.created_at.isoformat(),
            "updated_at": lead.updated_at.isoformat(),
            "contacted_at": lead.contacted_at.isoformat() if lead.contacted_at else None,
            "conversation_count": len(conversations),
            "conversations": [
                {
                    "id": str(conv.id),
                    "session_id": conv.session_id,
                    "title": conv.title,
                    "status": conv.status,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                }
                for conv in conversations
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lead detail: {e}")
        raise HTTPException(status_code=500, detail="Error fetching lead detail")


@router.patch("/leads/{lead_id}")
async def update_lead(
    lead_id: str,
    update_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update lead information
    
    Allowed fields:
    - status: LeadStatus enum value
    - email: string
    - name: string
    - phone: string
    - company_name: string
    - contacted_at: ISO datetime or null
    """
    try:
        result = await db.execute(
            select(Lead)
            .where(Lead.id == lead_id)
        )
        lead = result.scalars().first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Update allowed fields
        allowed_fields = {"status", "email", "name", "phone", "company_name", "contacted_at"}
        for field, value in update_data.items():
            if field in allowed_fields:
                if field == "status" and value:
                    setattr(lead, field, LeadStatus(value))
                else:
                    setattr(lead, field, value)
        
        await db.commit()
        await db.refresh(lead)
        
        return {
            "message": "Lead updated successfully",
            "lead": {
                "id": str(lead.id),
                "email": lead.email,
                "name": lead.name,
                "phone": lead.phone,
                "company_name": lead.company_name,
                "status": lead.status,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lead: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error updating lead")


@router.put("/leads/{lead_id}/name")
async def capture_lead_name(
    lead_id: str,
    request: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Capture lead identity from public chat form
    Simpler endpoint for public capture without auth
    
    Body: {"name": "Jean Dupont", "company_name": "ACME"}
    """
    try:
        name = request.get("name", "").strip()
        company_name = request.get("company_name", "").strip()
        
        if not name or len(name) < 2:
            raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
        
        result = await db.execute(
            select(Lead)
            .where(Lead.id == lead_id)
        )
        lead = result.scalars().first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead.name = name
        if company_name:
            lead.company_name = company_name
        await db.commit()
        await db.refresh(lead)
        
        return {
            "message": "Identity captured successfully",
            "lead": {
                "id": str(lead.id),
                "email": lead.email,
                "name": lead.name,
                "phone": lead.phone,
                "company_name": lead.company_name,
                "status": lead.status,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error capturing name: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error capturing name")


@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a lead (soft delete by setting status to ABANDONED)"""
    try:
        result = await db.execute(
            select(Lead)
            .where(Lead.id == lead_id)
        )
        lead = result.scalars().first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead.status = LeadStatus.ABANDONED
        await db.commit()
        
        return {"message": "Lead marked as abandoned"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lead: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting lead")


# ==================== Analytics ====================

@router.get("/analytics/leads")
async def get_leads_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get analytics for qualified leads (with email or phone)"""
    try:
        # Filter for qualified leads only (with contact info)
        contact_filter = (Lead.email.isnot(None)) | (Lead.phone.isnot(None))
        
        # Count by status (only for leads with contact info)
        status_counts = {}
        for status in LeadStatus:
            result = await db.execute(
                select(func.count(Lead.id))
                .where(contact_filter)
                .where(Lead.status == status)
            )
            status_counts[status.value] = result.scalar() or 0
        
        # Total qualified leads (with email or phone)
        result = await db.execute(
            select(func.count(Lead.id))
            .where(contact_filter)
        )
        total_leads = result.scalar() or 0
        
        # Leads with email
        result = await db.execute(
            select(func.count(Lead.id))
            .where((Lead.email.isnot(None)) & contact_filter)
        )
        leads_with_email = result.scalar() or 0

        # Leads with phone
        result = await db.execute(
            select(func.count(Lead.id))
            .where((Lead.phone.isnot(None)) & contact_filter)
        )
        leads_with_phone = result.scalar() or 0

        # Key funnel counts
        engaged_leads = status_counts.get("ENGAGED", 0)
        qualified_leads = status_counts.get("QUALIFIED", 0)
        contacted_leads = status_counts.get("CONTACTED", 0)
        converted_leads = status_counts.get("CONVERTED", 0)
        
        # Leads created today (qualified leads only)
        from datetime import datetime, timedelta
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(func.count(Lead.id))
            .where(contact_filter)
            .where(Lead.created_at >= today_start)
        )
        created_today = result.scalar() or 0
        
        return {
            "total_leads": total_leads,
            "leads_with_email": leads_with_email,
            "leads_with_phone": leads_with_phone,
            "leads_created_today": created_today,
            "by_status": status_counts,
            "funnel": {
                "engaged": engaged_leads,
                "qualified": qualified_leads,
                "contacted": contacted_leads,
                "converted": converted_leads,
            },
            "conversion_rate": (status_counts.get("CONVERTED", 0) / total_leads * 100) if total_leads > 0 else 0,
        }
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching analytics")


# ==================== Activity Logs ====================

@router.get("/logs")
async def get_activity_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    action_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    conversation_id: Optional[str] = None,
    resource_type: Optional[str] = None,
):
    """
    Get activity logs with pagination and filters.
    
    Query Parameters:
    - skip: Pagination offset (default: 0)
    - limit: Results per page (default: 50, max: 100)
    - action_type: Filter by action type (EMAIL, CRM, TICKET, SCORING, NOTIFICATION)
    - start_date: Filter by start date (ISO format)
    - end_date: Filter by end date (ISO format)
    - conversation_id: Filter by conversation ID
    - resource_type: Filter by resource type (e.g., 'lead', 'conversation')
    """
    try:
        from app.models.action import Action, ActionType, ActionStatus
        
        query = select(Action).options(selectinload(Action.conversation))
        
        # Filter by action_type if provided
        if action_type:
            query = query.where(Action.action_type == action_type)
        
        # Filter by date range
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.where(Action.created_at >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.where(Action.created_at <= end_dt)
            except ValueError:
                pass
        
        # Filter by conversation_id if provided
        if conversation_id:
            query = query.where(Action.conversation_id == conversation_id)
        
        # Filter by resource_type if provided (from payload)
        if resource_type:
            query = query.where(
                Action.payload["resource_type"].astext == resource_type
            )
        
        # Get total count before pagination
        count_query = select(func.count(Action.id))
        if action_type:
            count_query = count_query.where(Action.action_type == action_type)
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                count_query = count_query.where(Action.created_at >= start_dt)
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                count_query = count_query.where(Action.created_at <= end_dt)
            except ValueError:
                pass
        if conversation_id:
            count_query = count_query.where(Action.conversation_id == conversation_id)
        
        result_count = await db.execute(count_query)
        total_count = result_count.scalar() or 0
        
        # Apply pagination and order
        query = query.order_by(desc(Action.created_at))
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        actions = result.scalars().all()
        
        # Format response
        items = []
        for action in actions:
            payload = action.payload or {}
            result_data = action.result or {}
            
            item = {
                "id": action.id,
                "action_type": action.action_type.value if action.action_type else None,
                "status": action.status.value if action.status else None,
                "resource_type": payload.get("resource_type"),
                "resource_id": payload.get("resource_id"),
                "resource_name": payload.get("resource_name"),
                "details": payload.get("details"),
                "payload": payload,
                "result": result_data,
                "created_at": action.created_at,
                "executed_at": action.executed_at,
                "user_id": action.conversation.user_id if action.conversation else None,
            }
            items.append(item)
        
        return {
            "items": items,
            "total": total_count,
            "skip": skip,
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"Error fetching activity logs: {e}")
        raise HTTPException(status_code=500, detail="Error fetching activity logs")


# ==================== Lead Update (PUT) ====================

@router.put("/leads/{lead_id}")
async def update_lead_put(
    lead_id: str,
    update_request: LeadUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update lead properties.
    
    Body Parameters:
    - name: Optional lead name
    - phone: Optional phone number
    - company_name: Optional company name
    - status: Optional lead status (NEW, ENGAGED, QUALIFIED, CONTACTED, CONVERTED, ABANDONED)
    """
    try:
        from app.models.action import Action, ActionType, ActionStatus
        
        # Get existing lead
        result = await db.execute(
            select(Lead)
            .where(Lead.id == lead_id)
        )
        lead = result.scalars().first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Store old values for action logging
        old_values = {
            "name": lead.name,
            "phone": lead.phone,
            "company_name": lead.company_name,
            "status": lead.status.value if lead.status else None,
        }
        
        # Update only provided fields
        new_values = {}
        if update_request.name is not None:
            lead.name = update_request.name
            new_values["name"] = update_request.name
        
        if update_request.phone is not None:
            lead.phone = update_request.phone
            new_values["phone"] = update_request.phone
        
        if update_request.company_name is not None:
            lead.company_name = update_request.company_name
            new_values["company_name"] = update_request.company_name
        
        if update_request.status is not None:
            lead.status = update_request.status
            new_values["status"] = update_request.status.value
        
        # Commit changes
        await db.commit()
        await db.refresh(lead)
        
        return {
            "id": str(lead.id),
            "email": lead.email,
            "name": lead.name,
            "phone": lead.phone,
            "company_name": lead.company_name,
            "status": lead.status.value,
            "updated_at": lead.updated_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lead: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error updating lead")


# ==================== Conversation Actions ====================

@router.get("/conversations/{conversation_id}/logs")
async def get_conversation_logs(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all actions triggered in a conversation.
    
    Returns all emails, CRM updates, tickets, scoring results, and notifications
    for a specific conversation.
    
    Path Parameters:
    - conversation_id: UUID of the conversation
    """
    try:
        from app.models.action import Action, ActionType, ActionStatus
        
        # Verify conversation exists
        conv_result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
        )
        conversation = conv_result.scalars().first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Admin endpoint: can view any conversation (authenticated users only)
        # Note: this is admin-only due to /admin/ prefix
        
        # Get all actions for this conversation
        actions_result = await db.execute(
            select(Action)
            .where(Action.conversation_id == conversation_id)
            .order_by(desc(Action.created_at))
        )
        actions = actions_result.scalars().all()
        
        # Format response
        items = []
        for action in actions:
            item = {
                "id": action.id,
                "action_type": action.action_type.value if action.action_type else None,
                "status": action.status.value if action.status else None,
                "triggered_at": action.created_at.isoformat(),
                "executed_at": action.executed_at,
                "payload": action.payload or {},
                "result": action.result or {},
            }
            items.append(item)
        
        return {
            "items": items,
            "conversation_id": conversation_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation logs: {e}")
        raise HTTPException(status_code=500, detail="Error fetching conversation logs")


# ==================== Lead Export ====================

@router.post("/leads/export")
async def export_leads(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[LeadStatus] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
):
    """
    Export filtered leads to CSV file.
    
    Query Parameters:
    - status: Filter by lead status
    - date_from: Filter by start date (ISO format)
    - date_to: Filter by end date (ISO format)
    - search: Search by email, name, or company
    
    Returns:
    - CSV file download with columns: id, email, name, phone, company_name, status, message_count, created_at, last_contacted_at
    """
    try:
        # Build query
        query = select(Lead)
        
        # Only show leads with contact info
        query = query.where(
            (Lead.email.isnot(None)) | (Lead.phone.isnot(None))
        )
        
        # Filter by status
        if status:
            query = query.where(Lead.status == status)
        
        # Filter by date range
        if date_from:
            try:
                start_dt = datetime.fromisoformat(date_from)
                query = query.where(Lead.created_at >= start_dt)
            except ValueError:
                pass
        
        if date_to:
            try:
                end_dt = datetime.fromisoformat(date_to)
                query = query.where(Lead.created_at <= end_dt)
            except ValueError:
                pass
        
        # Filter by search text
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Lead.email.ilike(search_term)) |
                (Lead.name.ilike(search_term)) |
                (Lead.company_name.ilike(search_term))
            )
        
        # Order by created_at
        query = query.order_by(desc(Lead.created_at))
        
        # Execute query
        result = await db.execute(query)
        leads = result.scalars().all()
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "id",
                "email",
                "name",
                "phone",
                "company_name",
                "status",
                "message_count",
                "created_at",
                "last_contacted_at",
            ]
        )
        writer.writeheader()
        
        # Write lead rows
        for lead in leads:
            message_count = _safe_meta_message_count(lead)
            
            writer.writerow({
                "id": str(lead.id),
                "email": lead.email or "",
                "name": lead.name or "",
                "phone": lead.phone or "",
                "company_name": lead.company_name or "",
                "status": lead.status.value,
                "message_count": message_count,
                "created_at": lead.created_at.isoformat() if lead.created_at else "",
                "last_contacted_at": lead.contacted_at.isoformat() if lead.contacted_at else "",
            })
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"leads_export_{timestamp}.csv"
        
        # Get CSV content
        csv_content = output.getvalue()
        output.close()
        
        # Return as response
        return Response(
            content=csv_content.encode('utf-8'),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        logger.error(f"Error exporting leads: {e}")
        raise HTTPException(status_code=500, detail="Error exporting leads")
