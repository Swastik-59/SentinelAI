"""
SentinelAI — Model Loader Service

Loads trained ML models on application startup:
- ai_detector.pkl   → AI vs Human text classifier
- fraud_detector.pkl → Phishing vs Normal email classifier

Falls back to the legacy text_model.pkl if new models aren't available.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Any

import joblib

logger = logging.getLogger(__name__)

# ── Model Paths ───────────────────────────────────────────────────────────
# Primary: trained models from ai/models/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AI_MODEL_PATH = PROJECT_ROOT / "ai" / "models" / "ai_detector.pkl"
FRAUD_MODEL_PATH = PROJECT_ROOT / "ai" / "models" / "fraud_detector.pkl"

# Legacy fallback: backend/app/models/text_model.pkl
LEGACY_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "text_model.pkl"

# ── Model Cache ───────────────────────────────────────────────────────────
_ai_model: Optional[Any] = None
_fraud_model: Optional[Any] = None
_models_loaded: bool = False


def _load_model_file(path: Path, name: str) -> Optional[Any]:
    """Safely load a joblib model file."""
    if not path.exists():
        logger.warning("Model not found: %s (%s)", name, path)
        return None
    try:
        model = joblib.load(path)
        size_kb = os.path.getsize(path) / 1024
        logger.info("Loaded %s from %s (%.1f KB)", name, path, size_kb)
        return model
    except Exception as e:
        logger.error("Failed to load %s: %s", name, e)
        return None


def load_models() -> None:
    """
    Load all ML models into memory. Called once on application startup.
    """
    global _ai_model, _fraud_model, _models_loaded

    if _models_loaded:
        return

    logger.info("Loading ML models...")

    # Load AI detector
    _ai_model = _load_model_file(AI_MODEL_PATH, "AI Detector")
    if _ai_model is None:
        _ai_model = _load_model_file(LEGACY_MODEL_PATH, "Legacy Text Model")

    # Load Fraud detector
    _fraud_model = _load_model_file(FRAUD_MODEL_PATH, "Fraud Detector")

    _models_loaded = True
    logger.info(
        "Model loading complete — AI: %s, Fraud: %s",
        "loaded" if _ai_model else "fallback",
        "loaded" if _fraud_model else "fallback",
    )


def get_ai_model() -> Optional[Any]:
    """Return the loaded AI detection model (or None)."""
    if not _models_loaded:
        load_models()
    return _ai_model


def get_fraud_model() -> Optional[Any]:
    """Return the loaded fraud detection model (or None)."""
    if not _models_loaded:
        load_models()
    return _fraud_model


def models_available() -> dict:
    """Return status of loaded models."""
    return {
        "ai_detector": _ai_model is not None,
        "fraud_detector": _fraud_model is not None,
        "models_loaded": _models_loaded,
    }
