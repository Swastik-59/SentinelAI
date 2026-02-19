"""
SentinelAI — Image Detection Router

POST /analyze/image
- Accepts image file upload
- Runs deepfake detection pipeline
- Returns deepfake probability, fraud risk, explanation
"""

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any

from app.services.image_analyzer import analyze_image
from app.services.fraud_scorer import classify_risk_level
from app.services.explainability import generate_image_explanation
from app.utils.preprocessing import compute_hash, validate_image_format
from app.database import insert_audit_log

logger = logging.getLogger(__name__)

router = APIRouter()

# Maximum upload size: 10 MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024


# ── Response Schema ────────────────────────────────────────────────────────

class ImageAnalysisResponse(BaseModel):
    deepfake_probability: float
    fraud_risk_score: float
    risk_level: str
    explanation: str
    details: List[str]
    analysis_method: str


# ── Endpoint ───────────────────────────────────────────────────────────────

@router.post("/image", response_model=ImageAnalysisResponse)
async def analyze_image_endpoint(file: UploadFile = File(...)):
    """
    Analyse an image for deepfake / AI-generation indicators.
    
    Supported formats: JPEG, PNG, WebP, BMP, TIFF
    Max size: 10 MB
    """
    try:
        # Validate format
        if not validate_image_format(file.content_type):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format: {file.content_type}. "
                       f"Supported: JPEG, PNG, WebP, BMP, TIFF"
            )

        # Read file
        image_bytes = await file.read()
        if len(image_bytes) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=400, detail="Image exceeds 10 MB size limit")
        if len(image_bytes) < 100:
            raise HTTPException(status_code=400, detail="Image file appears to be empty or corrupt")

        # Run analysis
        result = analyze_image(image_bytes)

        # Compute fraud risk score (for images, primarily based on deepfake probability)
        deepfake_prob = result["deepfake_probability"]
        fraud_risk_score = round(deepfake_prob * 0.85, 4)  # Slight discount vs. text
        risk_level = classify_risk_level(fraud_risk_score)

        # Generate explanation
        explanation = generate_image_explanation(
            deepfake_probability=deepfake_prob,
            fraud_risk_score=fraud_risk_score,
            risk_level=risk_level,
            analysis_method=result["analysis_method"],
        )

        # Audit log
        input_hash = compute_hash(image_bytes)
        response_data = {
            "deepfake_probability": deepfake_prob,
            "fraud_risk_score": fraud_risk_score,
            "risk_level": risk_level,
            "explanation": explanation["summary"],
            "details": explanation["details"],
            "analysis_method": result["analysis_method"],
        }

        await insert_audit_log(
            input_type="image",
            input_hash=input_hash,
            ai_probability=deepfake_prob,
            fraud_risk_score=fraud_risk_score,
            risk_level=risk_level,
            result=response_data,
        )

        return ImageAnalysisResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Image analysis failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
