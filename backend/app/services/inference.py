"""
SentinelAI — Inference Service

Provides the unified text analysis pipeline:
1. Extract stylometric features
2. AI probability prediction (from ML model)
3. Fraud probability prediction (from ML model)
4. Combined risk score: risk_score = (0.6 * fraud) + (0.4 * ai)
5. LLM-generated explanation (via Ollama Mistral)

Returns a complete analysis result dict for the API response.
"""

import logging
import numpy as np
from typing import Dict, Any, Optional

from app.services.model_loader import get_ai_model, get_fraud_model
from app.services.llm_service import generate_explanation as llm_explain

logger = logging.getLogger(__name__)

# ── Feature Extraction (inline to avoid circular imports) ─────────────────
# We reuse the same logic from ai/utils/feature_engineering.py
import re
import string
import math

STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "out", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "because", "but", "and", "or",
    "if", "while", "this", "that", "these", "those", "i", "me", "my",
    "we", "our", "you", "your", "he", "him", "his", "she", "her",
    "it", "its", "they", "them", "their", "what", "which", "who",
    "about", "up", "down", "any", "every",
})

FEATURE_NAMES = [
    "avg_sentence_length",
    "sentence_length_variance",
    "punctuation_frequency",
    "stopword_ratio",
    "uppercase_ratio",
    "word_count",
    "lexical_diversity",
]


def _split_sentences(text: str) -> list:
    """Split text into sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if len(s.strip()) > 0]


def extract_features(text: str) -> Dict[str, float]:
    """Extract stylometric features from text."""
    if not text or not text.strip():
        return {name: 0.0 for name in FEATURE_NAMES}

    sentences = _split_sentences(text)
    words = text.split()

    if not words:
        return {name: 0.0 for name in FEATURE_NAMES}

    sentence_lengths = [len(s.split()) for s in sentences] if sentences else [0]
    avg_sentence_length = float(np.mean(sentence_lengths))
    sentence_length_variance = float(np.var(sentence_lengths))

    punct_count = sum(1 for ch in text if ch in string.punctuation)
    punctuation_frequency = punct_count / len(text) if text else 0.0

    lower_words = [w.lower().strip(string.punctuation) for w in words]
    lower_words = [w for w in lower_words if w]
    stopword_count = sum(1 for w in lower_words if w in STOPWORDS)
    stopword_ratio = stopword_count / len(lower_words) if lower_words else 0.0

    alpha_chars = [ch for ch in text if ch.isalpha()]
    uppercase_count = sum(1 for ch in alpha_chars if ch.isupper())
    uppercase_ratio = uppercase_count / len(alpha_chars) if alpha_chars else 0.0

    word_count = float(len(words))

    unique_words = set(lower_words)
    lexical_diversity = len(unique_words) / len(lower_words) if lower_words else 0.0

    return {
        "avg_sentence_length": round(avg_sentence_length, 4),
        "sentence_length_variance": round(sentence_length_variance, 4),
        "punctuation_frequency": round(punctuation_frequency, 4),
        "stopword_ratio": round(stopword_ratio, 4),
        "uppercase_ratio": round(uppercase_ratio, 4),
        "word_count": round(word_count, 4),
        "lexical_diversity": round(lexical_diversity, 4),
    }


def _features_to_vector(features: Dict[str, float]) -> np.ndarray:
    """Convert feature dict to numpy vector."""
    return np.array([[features.get(name, 0.0) for name in FEATURE_NAMES]])


# ── Risk Classification ───────────────────────────────────────────────────

def classify_risk_level(score: float) -> str:
    """Classify risk score into a human-readable level."""
    if score >= 0.8:
        return "CRITICAL"
    elif score >= 0.6:
        return "HIGH"
    elif score >= 0.3:
        return "MEDIUM"
    else:
        return "LOW"


# ── Rule-Based Fallbacks ──────────────────────────────────────────────────

def _rule_based_ai_probability(features: Dict[str, float]) -> float:
    """Heuristic AI detection when no model is available."""
    score = 0.0
    if features["sentence_length_variance"] < 20:
        score += 0.25
    elif features["sentence_length_variance"] < 50:
        score += 0.10
    if features["stopword_ratio"] > 0.45:
        score += 0.10
    if features["lexical_diversity"] < 0.5:
        score += 0.15
    if 0.03 < features["punctuation_frequency"] < 0.08:
        score += 0.10
    if features["uppercase_ratio"] < 0.03:
        score += 0.10
    return min(score, 0.95)


def _rule_based_fraud_probability(features: Dict[str, float]) -> float:
    """Heuristic fraud detection when no model is available."""
    score = 0.0
    if features["avg_sentence_length"] < 14:
        score += 0.15
    if features["sentence_length_variance"] < 15:
        score += 0.10
    if features["punctuation_frequency"] > 0.07:
        score += 0.10
    if features["uppercase_ratio"] > 0.05:
        score += 0.15
    if features["word_count"] < 100:
        score += 0.10
    return min(score, 0.95)


# ── Main Inference Pipeline ───────────────────────────────────────────────

async def analyze_text_pipeline(text: str) -> Dict[str, Any]:
    """
    Full text analysis pipeline:
    1. Extract features
    2. Predict AI probability
    3. Predict fraud probability
    4. Compute combined risk score
    5. Generate LLM explanation

    Returns complete analysis result.
    """
    # Step 1: Extract features
    features = extract_features(text)
    feature_vector = _features_to_vector(features)

    # Step 2: AI probability
    ai_model = get_ai_model()
    if ai_model is not None:
        try:
            proba = ai_model.predict_proba(feature_vector)[0]
            ai_probability = float(proba[1]) if len(proba) > 1 else float(proba[0])
        except Exception as e:
            logger.warning("AI model prediction failed: %s", e)
            ai_probability = _rule_based_ai_probability(features)
    else:
        ai_probability = _rule_based_ai_probability(features)

    # Step 3: Fraud probability
    fraud_model = get_fraud_model()
    if fraud_model is not None:
        try:
            proba = fraud_model.predict_proba(feature_vector)[0]
            fraud_probability = float(proba[1]) if len(proba) > 1 else float(proba[0])
        except Exception as e:
            logger.warning("Fraud model prediction failed: %s", e)
            fraud_probability = _rule_based_fraud_probability(features)
    else:
        fraud_probability = _rule_based_fraud_probability(features)

    # Step 4: Combined risk score
    risk_score = round((0.6 * fraud_probability) + (0.4 * ai_probability), 4)
    risk_score = min(max(risk_score, 0.0), 1.0)
    risk_level = classify_risk_level(risk_score)

    # Step 5: LLM explanation (async, non-blocking)
    explanation = ""
    try:
        explanation = await llm_explain(
            text=text[:500],
            ai_probability=ai_probability,
            fraud_probability=fraud_probability,
            risk_score=risk_score,
            risk_level=risk_level,
        )
    except Exception as e:
        logger.warning("LLM explanation failed: %s", e)
        explanation = _generate_fallback_explanation(
            ai_probability, fraud_probability, risk_score, risk_level
        )

    if not explanation:
        explanation = _generate_fallback_explanation(
            ai_probability, fraud_probability, risk_score, risk_level
        )

    return {
        "ai_probability": round(ai_probability, 4),
        "fraud_probability": round(fraud_probability, 4),
        "risk_score": round(risk_score, 4),
        "risk_level": risk_level,
        "explanation": explanation,
        "stylometric_features": features,
    }


def _generate_fallback_explanation(
    ai_prob: float, fraud_prob: float, risk_score: float, risk_level: str
) -> str:
    """Generate a structured explanation when LLM is unavailable."""
    parts = []

    if risk_level == "CRITICAL":
        parts.append(
            f"CRITICAL RISK (score: {risk_score:.2f}). "
            "This content exhibits strong indicators of AI-generated fraud. "
            "Immediate review and escalation recommended."
        )
    elif risk_level == "HIGH":
        parts.append(
            f"HIGH RISK (score: {risk_score:.2f}). "
            "Multiple fraud indicators detected. Manual review strongly recommended."
        )
    elif risk_level == "MEDIUM":
        parts.append(
            f"MEDIUM RISK (score: {risk_score:.2f}). "
            "Some suspicious patterns detected. Further investigation may be warranted."
        )
    else:
        parts.append(
            f"LOW RISK (score: {risk_score:.2f}). "
            "No significant fraud indicators detected."
        )

    if ai_prob > 0.7:
        parts.append(f"AI generation probability is high ({ai_prob:.0%}).")
    elif ai_prob > 0.4:
        parts.append(f"AI generation probability is moderate ({ai_prob:.0%}).")

    if fraud_prob > 0.7:
        parts.append(f"Fraud probability is high ({fraud_prob:.0%}).")
    elif fraud_prob > 0.4:
        parts.append(f"Fraud probability is moderate ({fraud_prob:.0%}).")

    return " ".join(parts)
