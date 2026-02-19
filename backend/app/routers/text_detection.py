"""
SentinelAI — Text Detection Router

POST /analyze/text
- Accepts raw text
- Runs ML-based AI detection + fraud detection pipeline
- Returns AI probability, fraud probability, risk score, explanation
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.services.inference import analyze_text_pipeline
from app.services.fraud_scorer import compute_fraud_risk
from app.services.explainability import generate_explanation
from app.utils.preprocessing import clean_text, compute_text_hash
from app.database import insert_audit_log, create_case
from app.services.escalation import evaluate_escalation

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response Schemas ─────────────────────────────────────────────

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000, description="Raw text to analyse")


class TextAnalysisResponse(BaseModel):
    ai_probability: float
    fraud_probability: float
    fraud_risk_score: float
    risk_score: float
    risk_level: str
    highlighted_phrases: List[str]
    explanation: str
    details: List[str]
    stylometric_features: Dict[str, float]
    fraud_signals: Dict[str, Any]
    case_id: Optional[str] = None
    escalation_reason: Optional[str] = None


# ── Endpoint ───────────────────────────────────────────────────────────────

@router.post("/text", response_model=TextAnalysisResponse)
async def analyze_text_endpoint(request: TextAnalysisRequest):
    """
    Analyse text for AI-generation probability and fraud risk.
    Uses ML models when available, with rule-based fallback.
    """
    try:
        text = clean_text(request.text)
        if len(text) < 10:
            raise HTTPException(status_code=400, detail="Text too short after cleaning")

        # Run new ML inference pipeline
        inference_result = await analyze_text_pipeline(text)

        # Also run keyword-based fraud scoring for signals
        fraud_result = compute_fraud_risk(text, inference_result["ai_probability"])

        # Generate detailed explanation
        combined = {
            **inference_result,
            **fraud_result,
        }
        explanation_result = generate_explanation(combined)

        input_hash = compute_text_hash(text)
        response_data = {
            "ai_probability": inference_result["ai_probability"],
            "fraud_probability": inference_result.get("fraud_probability", 0.0),
            "fraud_risk_score": fraud_result["fraud_risk_score"],
            "risk_score": inference_result["risk_score"],
            "risk_level": inference_result["risk_level"],
            "highlighted_phrases": explanation_result["highlighted_phrases"],
            "explanation": inference_result.get("explanation", explanation_result["summary"]),
            "details": explanation_result["details"],
            "stylometric_features": inference_result["stylometric_features"],
            "fraud_signals": fraud_result["signals"],
        }

        await insert_audit_log(
            input_type="text",
            input_hash=input_hash,
            ai_probability=inference_result["ai_probability"],
            fraud_risk_score=fraud_result["fraud_risk_score"],
            risk_level=inference_result["risk_level"],
            result=response_data,
        )

        # Auto-create case on elevated risk
        escalation = evaluate_escalation(
            risk_score=inference_result["risk_score"],
            ai_probability=inference_result["ai_probability"],
            fraud_probability=inference_result.get("fraud_probability", 0.0),
            risk_level=inference_result["risk_level"],
        )
        if escalation["should_create_case"]:
            case_id = await create_case(
                content_hash=input_hash,
                risk_score=inference_result["risk_score"],
                ai_probability=inference_result["ai_probability"],
                fraud_probability=inference_result.get("fraud_probability", 0.0),
                risk_level=inference_result["risk_level"],
                status=escalation["status"],
                escalation_reason=escalation["escalation_reason"],
                result=response_data,
            )
            response_data["case_id"] = case_id
            response_data["escalation_reason"] = escalation["escalation_reason"]
            logger.info(f"Auto-created case {case_id} — {escalation['alert_type']}")

        return TextAnalysisResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Text analysis failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
