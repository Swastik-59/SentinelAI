"""
SentinelAI — Document Detection Router

POST /analyze/document
- Accepts PDF file upload
- Extracts text from PDF
- Runs full text analysis + fraud scoring pipeline
- Returns structured document-level fraud analysis
"""

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.services.inference import analyze_text_pipeline
from app.services.fraud_scorer import compute_fraud_risk
from app.services.explainability import generate_explanation
from app.utils.preprocessing import (
    extract_text_from_pdf,
    clean_text,
    truncate_text,
    compute_hash,
    validate_pdf,
)
from app.database import insert_audit_log, create_case
from app.services.escalation import evaluate_escalation

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_PDF_SIZE = 20 * 1024 * 1024  # 20 MB


# ── Response Schema ────────────────────────────────────────────────────────

class DocumentAnalysisResponse(BaseModel):
    ai_probability: float
    fraud_probability: float
    fraud_risk_score: float
    risk_score: float
    risk_level: str
    highlighted_phrases: List[str]
    explanation: str
    details: List[str]
    extracted_text_preview: str = Field(..., description="First 500 chars of extracted text")
    page_count: int
    stylometric_features: Dict[str, float]
    fraud_signals: Dict[str, Any]
    case_id: Optional[str] = None
    escalation_reason: Optional[str] = None


# ── Endpoint ───────────────────────────────────────────────────────────────

@router.post("/document", response_model=DocumentAnalysisResponse)
async def analyze_document_endpoint(file: UploadFile = File(...)):
    """
    Analyse a PDF document for AI-generated fraud content.
    
    Pipeline:
    1. Validate and read PDF
    2. Extract text from all pages
    3. Run text analysis pipeline
    4. Compute fraud risk
    5. Generate explainable output
    """
    try:
        # Validate
        if not validate_pdf(file.content_type):
            raise HTTPException(
                status_code=400,
                detail=f"Expected a PDF file, got: {file.content_type}"
            )

        pdf_bytes = await file.read()
        if len(pdf_bytes) > MAX_PDF_SIZE:
            raise HTTPException(status_code=400, detail="PDF exceeds 20 MB size limit")
        if len(pdf_bytes) < 100:
            raise HTTPException(status_code=400, detail="PDF appears to be empty or corrupt")

        # Extract text
        extracted_text = extract_text_from_pdf(pdf_bytes)
        if not extracted_text or len(extracted_text.strip()) < 20:
            raise HTTPException(
                status_code=422,
                detail="Could not extract sufficient text from the PDF. "
                       "The file may be image-based or encrypted."
            )

        # Count pages
        try:
            from PyPDF2 import PdfReader
            import io
            page_count = len(PdfReader(io.BytesIO(pdf_bytes)).pages)
        except Exception:
            page_count = 0

        # Truncate and clean for analysis
        text = truncate_text(clean_text(extracted_text), max_length=10000)

        # Run unified inference pipeline (AI + Fraud ML models + LLM explanation)
        pipeline_result = await analyze_text_pipeline(text)

        # Keyword-based fraud signal scoring
        fraud_result = compute_fraud_risk(text, pipeline_result["ai_probability"])

        # Rule-based explainability (highlighted phrases, details)
        combined = {**pipeline_result, **fraud_result}
        explanation_data = generate_explanation(combined)

        # Prefer LLM explanation when available, fall back to rule-based
        explanation_text = (
            pipeline_result.get("explanation")
            or explanation_data.get("summary", "")
        )

        # Build response
        input_hash = compute_hash(pdf_bytes)
        response_data = {
            "ai_probability": pipeline_result["ai_probability"],
            "fraud_probability": pipeline_result["fraud_probability"],
            "fraud_risk_score": fraud_result["fraud_risk_score"],
            "risk_score": pipeline_result["risk_score"],
            "risk_level": pipeline_result["risk_level"],
            "highlighted_phrases": explanation_data["highlighted_phrases"],
            "explanation": explanation_text,
            "details": explanation_data["details"],
            "extracted_text_preview": extracted_text[:500],
            "page_count": page_count,
            "stylometric_features": pipeline_result["stylometric_features"],
            "fraud_signals": fraud_result["signals"],
        }

        await insert_audit_log(
            input_type="document",
            input_hash=input_hash,
            ai_probability=pipeline_result["ai_probability"],
            fraud_risk_score=fraud_result["fraud_risk_score"],
            risk_level=pipeline_result["risk_level"],
            result=response_data,
        )

        # Auto-create case on elevated risk
        escalation = evaluate_escalation(
            risk_score=pipeline_result["risk_score"],
            ai_probability=pipeline_result["ai_probability"],
            fraud_probability=pipeline_result["fraud_probability"],
            risk_level=pipeline_result["risk_level"],
        )
        if escalation["should_create_case"]:
            case_id = await create_case(
                content_hash=input_hash,
                risk_score=pipeline_result["risk_score"],
                ai_probability=pipeline_result["ai_probability"],
                fraud_probability=pipeline_result["fraud_probability"],
                risk_level=pipeline_result["risk_level"],
                status=escalation["status"],
                escalation_reason=escalation["escalation_reason"],
                result=response_data,
            )
            response_data["case_id"] = case_id
            response_data["escalation_reason"] = escalation["escalation_reason"]
            logger.info(f"Auto-created case {case_id} — {escalation['alert_type']}")

        return DocumentAnalysisResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Document analysis failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
