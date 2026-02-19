"""
SentinelAI — Audit Log Router

GET /audit/logs
- Retrieve past analysis results
- Filter by type, flagged status
- Paginated results
"""

import logging
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.database import get_audit_logs

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Response Schema ────────────────────────────────────────────────────────

class AuditLogEntry(BaseModel):
    id: int
    timestamp: str
    input_type: str
    ai_probability: float
    fraud_risk_score: float
    risk_level: str
    result: Dict[str, Any]
    flagged: bool


class AuditLogResponse(BaseModel):
    logs: List[AuditLogEntry]
    count: int


# ── Endpoint ───────────────────────────────────────────────────────────────

@router.get("/logs", response_model=AuditLogResponse)
async def get_logs(
    limit: int = Query(50, ge=1, le=500, description="Max entries to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    flagged_only: bool = Query(False, description="Only return HIGH/CRITICAL cases"),
    input_type: Optional[str] = Query(None, description="Filter by input type: text, image, document"),
):
    """
    Retrieve audit log entries with optional filtering.
    
    Parameters:
    - limit: maximum number of records (default 50)
    - offset: pagination offset
    - flagged_only: if true, only HIGH/CRITICAL risk entries
    - input_type: filter by 'text', 'image', or 'document'
    """
    try:
        logs = await get_audit_logs(
            limit=limit,
            offset=offset,
            flagged_only=flagged_only,
            input_type=input_type,
        )
        return AuditLogResponse(logs=logs, count=len(logs))
    except Exception as e:
        logger.exception("Failed to retrieve audit logs")
        return AuditLogResponse(logs=[], count=0)
