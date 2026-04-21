"""Pydantic schemas for activity logs and exports"""

from pydantic import BaseModel, Field
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== Activity Log Schemas ====================

class ActivityLogResponse(BaseModel):
    """Schema for activity log response"""
    id: uuid.UUID
    action_type: str
    status: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    details: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    executed_at: Optional[datetime] = None
    user_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class ActivityLogList(BaseModel):
    """Schema for activity log list response"""
    items: List[ActivityLogResponse]
    total: int
    skip: int
    limit: int


# ==================== Lead Export Schemas ====================

class LeadExportRow(BaseModel):
    """Schema for lead export row (CSV)"""
    id: str
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: str
    message_count: int
    created_at: str
    last_contacted_at: Optional[str] = None
