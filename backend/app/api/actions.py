from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.action_service import action_service
from app.models.action import Action, ActionType, ActionStatus

router = APIRouter()

class ActionCreate(BaseModel):
    conversation_id: uuid.UUID
    action_type: ActionType
    payload: Dict[str, Any]

class ActionResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    action_type: ActionType
    status: ActionStatus
    payload: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    executed_at: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.post("/", response_model=ActionResponse)
async def create_action(
    action_in: ActionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new manual action."""
    action = await action_service.create_action(
        db, 
        action_in.conversation_id, 
        action_in.action_type, 
        action_in.payload
    )
    return action

@router.post("/{action_id}/execute", response_model=ActionResponse)
async def execute_action(
    action_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Execute a pending action manually."""
    try:
        await action_service.execute_action(db, action_id)
        from sqlalchemy import select
        result = await db.execute(select(Action).filter(Action.id == action_id))
        action = result.scalars().first()
        return action
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

@router.get("/conversation/{conversation_id}", response_model=List[ActionResponse])
async def get_conversation_actions(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all actions for a specific conversation."""
    from sqlalchemy import select
    result = await db.execute(
        select(Action)
        .filter(Action.conversation_id == conversation_id)
        .order_by(Action.created_at.desc())
    )
    return result.scalars().all()
