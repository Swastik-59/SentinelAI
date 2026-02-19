"""
SentinelAI — Fraud Trend Analytics Router

GET /analytics/overview — Dashboard-grade analytics: fraud trends, AI %, resolution time, keywords
"""

import logging
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from app.database import get_analytics_overview
from app.services.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────

class FraudPerDay(BaseModel):
    date: str
    count: int


class AnalyticsOverview(BaseModel):
    fraud_per_day: List[FraudPerDay]
    ai_fraud_percentage: float
    risk_breakdown: Dict[str, int]
    type_breakdown: Dict[str, int]
    case_status: Dict[str, int]
    avg_resolution_hours: Optional[float]
    top_fraud_keywords: List[Dict[str, Any]]
    total_cases: int
    total_escalated: int


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/overview", response_model=AnalyticsOverview)
async def analytics_overview_endpoint(
    days: int = Query(30, ge=1, le=365, description="Lookback window in days"),
    user=Depends(get_current_user),
):
    """
    Aggregated analytics for the fraud investigation dashboard.
    Returns trends, risk breakdowns, resolution metrics, and keyword analysis.
    """
    data = await get_analytics_overview(days=days)
    return AnalyticsOverview(**data)
