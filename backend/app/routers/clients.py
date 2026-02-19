"""
SentinelAI — Client Management Router

POST   /clients               — Register a corporate client
GET    /clients                — List all clients
GET    /clients/{id}/risk-summary  — Aggregated risk summary for a client
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.database import create_client, get_clients, get_client, get_client_risk_summary
from app.services.auth import get_current_user, require_role

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────

class ClientCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    industry: Optional[str] = None
    contact_email: Optional[str] = None


class ClientResponse(BaseModel):
    id: str
    name: str
    industry: Optional[str]
    contact_email: Optional[str]
    total_cases: int
    open_cases: int
    avg_risk_score: float
    created_at: str


class ClientListResponse(BaseModel):
    clients: List[ClientResponse]
    count: int


class ClientRiskSummary(BaseModel):
    client: ClientResponse
    risk_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    recent_cases: List[Dict[str, Any]]


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("", response_model=ClientResponse)
async def create_client_endpoint(
    request: ClientCreateRequest,
    user=Depends(require_role("reviewer")),
):
    """Register a new corporate client. Requires reviewer or admin role."""
    client_id = await create_client(
        name=request.name,
        industry=request.industry,
        contact_email=request.contact_email,
    )
    client = await get_client(client_id)
    if not client:
        raise HTTPException(status_code=500, detail="Failed to create client")
    return ClientResponse(**client)


@router.get("", response_model=ClientListResponse)
async def list_clients_endpoint(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user=Depends(get_current_user),
):
    """List all corporate clients."""
    clients = await get_clients(limit=limit, offset=offset)
    return ClientListResponse(
        clients=[ClientResponse(**c) for c in clients],
        count=len(clients),
    )


@router.get("/{client_id}/risk-summary", response_model=ClientRiskSummary)
async def client_risk_summary_endpoint(
    client_id: str,
    user=Depends(get_current_user),
):
    """Get aggregated risk profile and recent case activity for a client."""
    client = await get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    summary = await get_client_risk_summary(client_id)

    return ClientRiskSummary(
        client=ClientResponse(**client),
        risk_distribution=summary.get("risk_distribution", {}),
        status_distribution=summary.get("status_distribution", {}),
        recent_cases=summary.get("recent_cases", []),
    )
