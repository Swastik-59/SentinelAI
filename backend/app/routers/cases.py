"""
SentinelAI — Case Management Router

POST   /cases/create          — Create a new investigation case
GET    /cases                  — List cases with filters
GET    /cases/{id}             — Get case details + notes
PATCH  /cases/{id}/status      — Update case status (RBAC-gated)
POST   /cases/{id}/notes       — Add investigator note
POST   /cases/{id}/export      — Generate PDF report
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import io

from app.database import (
    create_case, get_case, get_cases, update_case_status,
    add_case_note, get_case_notes,
)
from app.services.auth import get_current_user, require_role
from app.services.report_generator import generate_case_pdf

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────

class CaseCreateRequest(BaseModel):
    content_hash: str
    risk_score: float
    ai_probability: float
    fraud_probability: float
    risk_level: str
    escalation_reason: Optional[str] = None
    client_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class CaseStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(OPEN|UNDER_REVIEW|ESCALATED|RESOLVED|FALSE_POSITIVE)$")
    assigned_to: Optional[str] = None


class CaseNoteRequest(BaseModel):
    note: str = Field(..., min_length=1, max_length=5000)


class CaseNoteResponse(BaseModel):
    id: int
    case_id: str
    author: str
    note: str
    timestamp: str


class CaseResponse(BaseModel):
    id: str
    content_hash: Optional[str]
    risk_score: float
    ai_probability: float
    fraud_probability: float
    risk_level: str
    status: str
    assigned_to: Optional[str]
    escalation_reason: Optional[str]
    client_id: Optional[str]
    result: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str
    notes: Optional[List[CaseNoteResponse]] = None


class CaseListResponse(BaseModel):
    cases: List[CaseResponse]
    count: int


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/create", response_model=CaseResponse)
async def create_case_endpoint(
    request: CaseCreateRequest,
    user=Depends(get_current_user),
):
    """Create a new investigation case manually."""
    case_id = await create_case(
        content_hash=request.content_hash,
        risk_score=request.risk_score,
        ai_probability=request.ai_probability,
        fraud_probability=request.fraud_probability,
        risk_level=request.risk_level,
        escalation_reason=request.escalation_reason,
        client_id=request.client_id,
        result=request.result,
    )
    case = await get_case(case_id)
    if not case:
        raise HTTPException(status_code=500, detail="Failed to create case")
    return CaseResponse(**case)


@router.get("", response_model=CaseListResponse)
async def list_cases_endpoint(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Filter by status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    client_id: Optional[str] = Query(None, description="Filter by client"),
    user=Depends(get_current_user),
):
    """List investigation cases with optional filters."""
    cases = await get_cases(
        limit=limit, offset=offset,
        status=status, risk_level=risk_level, client_id=client_id,
    )
    return CaseListResponse(cases=[CaseResponse(**c) for c in cases], count=len(cases))


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case_endpoint(
    case_id: str,
    user=Depends(get_current_user),
):
    """Get a single case with its investigation notes."""
    case = await get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    notes = await get_case_notes(case_id)
    return CaseResponse(**case, notes=[CaseNoteResponse(**n) for n in notes])


@router.patch("/{case_id}/status", response_model=CaseResponse)
async def update_status_endpoint(
    case_id: str,
    request: CaseStatusUpdate,
    user=Depends(get_current_user),
):
    """
    Update case status. RBAC rules:
    - RESOLVED / FALSE_POSITIVE: requires reviewer or admin
    - Other statuses: any authenticated user
    """
    # Enforce RBAC for resolution statuses
    if request.status in ("RESOLVED", "FALSE_POSITIVE"):
        if not user or user.get("role") not in ("reviewer", "admin"):
            raise HTTPException(
                status_code=403,
                detail="Only reviewers or admins can mark cases as RESOLVED or FALSE_POSITIVE",
            )

    case = await get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    success = await update_case_status(case_id, request.status, request.assigned_to)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update case")

    # Auto-add status change note
    author = user["username"] if user else "system"
    await add_case_note(
        case_id, author,
        f"Status changed to {request.status}" +
        (f" — assigned to {request.assigned_to}" if request.assigned_to else ""),
    )

    updated = await get_case(case_id)
    notes = await get_case_notes(case_id)
    return CaseResponse(**updated, notes=[CaseNoteResponse(**n) for n in notes])


@router.post("/{case_id}/notes", response_model=CaseNoteResponse)
async def add_note_endpoint(
    case_id: str,
    request: CaseNoteRequest,
    user=Depends(get_current_user),
):
    """Add an investigator note to a case."""
    case = await get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    author = user["username"] if user else "anonymous"
    note_id = await add_case_note(case_id, author, request.note)

    notes = await get_case_notes(case_id)
    for n in notes:
        if n["id"] == note_id:
            return CaseNoteResponse(**n)

    return CaseNoteResponse(
        id=note_id, case_id=case_id, author=author,
        note=request.note, timestamp="",
    )


@router.post("/{case_id}/export")
async def export_case_pdf(
    case_id: str,
    user=Depends(get_current_user),
):
    """Generate and download a PDF investigation report for a case."""
    case = await get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    notes = await get_case_notes(case_id)

    try:
        pdf_bytes = generate_case_pdf(case, notes)
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e))

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="sentinel_case_{case_id[:8]}.pdf"',
        },
    )
