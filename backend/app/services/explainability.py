"""
SentinelAI — Explainability Module

Generates human-readable explanations of detection results:
- Why the text was flagged as AI-generated
- Which fraud signals were triggered
- Feature-level contributions to the final score
"""

from typing import Dict, Any, List


def _describe_stylometric(features: Dict[str, float], ai_probability: float = 0.0) -> List[str]:
    """
    Generate human-readable observations from stylometric features.
    Only flag AI-suggestive patterns when ai_probability actually supports it.
    """
    observations = []

    # Only describe AI-suggestive stylometric traits when the model agrees
    if ai_probability < 0.15:
        return observations

    # Sentence length variance (only meaningful with multiple sentences)
    variance = features.get("sentence_length_variance", 0)
    word_count = features.get("word_count", 0)
    avg_sentence_length = features.get("avg_sentence_length", 0)
    # Skip variance observation for very short texts (likely 1 sentence)
    if word_count > 50 and avg_sentence_length < word_count * 0.9:
        if variance < 15:
            observations.append(
                f"Very low sentence length variance ({variance:.1f}) — "
                "AI-generated text tends to have uniform sentence structure."
            )
        elif variance < 40:
            observations.append(
                f"Moderate sentence length variance ({variance:.1f}) — "
                "somewhat uniform, which can indicate machine generation."
            )

    # Lexical diversity
    diversity = features.get("lexical_diversity", 0)
    if diversity < 0.45:
        observations.append(
            f"Low lexical diversity ({diversity:.2f}) — "
            "repetitive vocabulary is a common trait of AI-generated text."
        )

    # Stopword ratio
    stopword_ratio = features.get("stopword_ratio", 0)
    if stopword_ratio > 0.48:
        observations.append(
            f"High stopword ratio ({stopword_ratio:.2f}) — "
            "AI models tend to over-use function words."
        )

    # Punctuation
    punct = features.get("punctuation_frequency", 0)
    if 0.03 < punct < 0.07:
        observations.append(
            f"Punctuation frequency ({punct:.3f}) is within the range "
            "typical of AI-generated prose."
        )

    return observations


def _describe_perplexity(perplexity: float) -> str:
    """Explain what the perplexity score means."""
    if perplexity < 40:
        return (
            f"Very low perplexity ({perplexity:.1f}). The text is highly predictable, "
            "strongly suggesting AI generation."
        )
    elif perplexity < 80:
        return (
            f"Low-to-moderate perplexity ({perplexity:.1f}). The text shows patterns "
            "consistent with AI-assisted writing."
        )
    elif perplexity < 150:
        return (
            f"Moderate perplexity ({perplexity:.1f}). The text has some unpredictable "
            "elements but cannot rule out AI generation."
        )
    else:
        return (
            f"High perplexity ({perplexity:.1f}). The text appears relatively "
            "unpredictable, more consistent with human writing."
        )


def _describe_fraud_signals(signals: Dict[str, Any]) -> List[str]:
    """Explain triggered fraud signals."""
    explanations = []

    urgency = signals.get("urgency", {})
    if urgency.get("count", 0) > 0:
        keywords = ", ".join(f'"{k}"' for k in urgency["keywords"][:5])
        explanations.append(
            f"⚠ Urgency language detected ({urgency['count']} indicators): {keywords}. "
            "Fraudulent communications often create artificial time pressure."
        )

    financial = signals.get("financial_redirection", {})
    if financial.get("count", 0) > 0:
        keywords = ", ".join(f'"{k}"' for k in financial["keywords"][:5])
        explanations.append(
            f"⚠ Financial redirection language ({financial['count']} indicators): {keywords}. "
            "This suggests an attempt to redirect funds or extract payment information."
        )

    impersonation = signals.get("impersonation", {})
    if impersonation.get("count", 0) > 0:
        keywords = ", ".join(f'"{k}"' for k in impersonation["keywords"][:5])
        explanations.append(
            f"⚠ Impersonation signals ({impersonation['count']} indicators): {keywords}. "
            "The text attempts to claim authority or institutional affiliation."
        )

    return explanations


def _describe_risk_level(risk_level: str, score: float) -> str:
    """Generate a summary statement based on risk level."""
    templates = {
        "CRITICAL": (
            f"🔴 CRITICAL RISK (score: {score:.2f}). "
            "This content exhibits strong indicators of AI-generated fraud. "
            "Immediate review and escalation recommended."
        ),
        "HIGH": (
            f"🟠 HIGH RISK (score: {score:.2f}). "
            "Multiple fraud indicators detected alongside AI-generation signals. "
            "Manual review strongly recommended."
        ),
        "MEDIUM": (
            f"🟡 MEDIUM RISK (score: {score:.2f}). "
            "Some suspicious patterns detected. "
            "Further investigation may be warranted."
        ),
        "LOW": (
            f"🟢 LOW RISK (score: {score:.2f}). "
            "No significant fraud indicators detected. "
            "Content appears within normal parameters."
        ),
    }
    return templates.get(risk_level, f"Risk score: {score:.2f}")


def generate_explanation(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a complete human-readable explanation from the analysis result.
    
    Input structure expected:
    {
        "ai_probability": float,
        "stylometric_features": dict,
        "perplexity": float,
        "fraud_risk_score": float,
        "risk_level": str,
        "signals": dict,
        "suspicious_phrases": list,
    }
    
    Returns:
    {
        "summary": str,
        "details": list[str],
        "highlighted_phrases": list[str],
    }
    """
    details = []

    # AI probability overview
    ai_prob = analysis_result.get("ai_probability", 0)
    if ai_prob > 0.7:
        details.append(
            f"AI generation probability is high ({ai_prob:.1%}), "
            "indicating this text was very likely produced by an AI model."
        )
    elif ai_prob > 0.4:
        details.append(
            f"AI generation probability is moderate ({ai_prob:.1%}), "
            "suggesting possible AI involvement in writing this text."
        )
    else:
        details.append(
            f"AI generation probability is low ({ai_prob:.1%}). "
            "The text appears to be human-authored."
        )

    # Stylometric observations
    stylo_features = analysis_result.get("stylometric_features", {})
    if stylo_features:
        details.extend(_describe_stylometric(stylo_features, ai_prob))

    # Perplexity (only include if actually computed)
    perplexity = analysis_result.get("perplexity")
    if perplexity is not None and perplexity > 0:
        details.append(_describe_perplexity(perplexity))

    # Fraud signals
    signals = analysis_result.get("signals", {})
    if signals:
        details.extend(_describe_fraud_signals(signals))

    # Risk summary
    risk_level = analysis_result.get("risk_level", "LOW")
    fraud_score = analysis_result.get("fraud_risk_score", 0)
    summary = _describe_risk_level(risk_level, fraud_score)

    return {
        "summary": summary,
        "details": details,
        "highlighted_phrases": analysis_result.get("suspicious_phrases", []),
    }


def generate_image_explanation(
    deepfake_probability: float,
    fraud_risk_score: float,
    risk_level: str,
    analysis_method: str,
) -> Dict[str, Any]:
    """Generate explanation for image analysis results."""
    details = []

    if deepfake_probability > 0.7:
        details.append(
            f"Deepfake probability is high ({deepfake_probability:.1%}). "
            "The image shows strong signs of AI generation or manipulation."
        )
    elif deepfake_probability > 0.4:
        details.append(
            f"Deepfake probability is moderate ({deepfake_probability:.1%}). "
            "Some artefacts suggest possible AI manipulation."
        )
    else:
        details.append(
            f"Deepfake probability is low ({deepfake_probability:.1%}). "
            "The image appears to be authentic."
        )

    details.append(f"Analysis method: {analysis_method}")

    summary = _describe_risk_level(risk_level, fraud_risk_score)

    return {
        "summary": summary,
        "details": details,
        "highlighted_phrases": [],
    }
