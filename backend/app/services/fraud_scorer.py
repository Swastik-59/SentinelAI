"""
SentinelAI — Fraud Risk Scoring Engine

Combines AI-generation probability with fraud-intent signals:
1. Urgency keyword detection
2. Financial redirection language
3. Impersonation phrase detection
4. Final risk score computation & classification
"""

import re
from typing import Dict, Any, List, Tuple


# ── Fraud Signal Dictionaries ─────────────────────────────────────────────

URGENCY_KEYWORDS = [
    "urgent", "immediately", "right away", "asap", "time-sensitive",
    "act now", "limited time", "expires today", "within 24 hours",
    "deadline", "final notice", "last chance", "don't delay",
    "respond immediately", "action required", "critical alert",
    "account suspended", "account locked", "verify now",
    "failure to respond", "will be terminated", "suspension notice",
]

FINANCIAL_REDIRECTION = [
    "wire transfer", "send money", "transfer funds", "bank account",
    "routing number", "account number", "payment details",
    "updated bank details", "new payment instructions",
    "pay to this account", "updated billing", "revised invoice",
    "payment portal", "click here to pay", "authorize payment",
    "refund processing", "claim your refund", "settlement amount",
    "cryptocurrency", "bitcoin wallet", "gift card",
    "western union", "moneygram", "zelle", "venmo",
]

IMPERSONATION_PHRASES = [
    "this is your bank", "from the fraud department",
    "official notice from", "federal reserve", "irs notification",
    "social security administration", "your account manager",
    "compliance department", "security team", "it department",
    "ceo", "cfo", "managing director", "board of directors",
    "on behalf of", "authorized representative",
    "government agency", "law enforcement", "court order",
    "legal action", "arrest warrant", "federal investigation",
]


def _find_matches(text: str, patterns: List[str]) -> List[Tuple[str, int, int]]:
    """
    Find all occurrences of patterns in the text.
    Returns list of (matched_phrase, start_index, end_index).
    """
    text_lower = text.lower()
    matches = []
    for pattern in patterns:
        start = 0
        while True:
            idx = text_lower.find(pattern, start)
            if idx == -1:
                break
            matches.append((pattern, idx, idx + len(pattern)))
            start = idx + 1
    return matches


def detect_urgency(text: str) -> Dict[str, Any]:
    """Detect urgency/pressure language."""
    matches = _find_matches(text, URGENCY_KEYWORDS)
    unique = list(set(m[0] for m in matches))
    score = min(len(unique) * 0.15, 1.0)
    return {"keywords": unique, "score": round(score, 4), "count": len(unique)}


def detect_financial_redirection(text: str) -> Dict[str, Any]:
    """Detect financial redirection and payment manipulation language."""
    matches = _find_matches(text, FINANCIAL_REDIRECTION)
    unique = list(set(m[0] for m in matches))
    score = min(len(unique) * 0.2, 1.0)
    return {"keywords": unique, "score": round(score, 4), "count": len(unique)}


def detect_impersonation(text: str) -> Dict[str, Any]:
    """Detect impersonation and authority-spoofing language."""
    matches = _find_matches(text, IMPERSONATION_PHRASES)
    unique = list(set(m[0] for m in matches))
    score = min(len(unique) * 0.2, 1.0)
    return {"keywords": unique, "score": round(score, 4), "count": len(unique)}


def classify_risk_level(score: float) -> str:
    """
    Classify fraud risk into discrete levels.
    
    LOW:      0.0 – 0.3
    MEDIUM:   0.3 – 0.6
    HIGH:     0.6 – 0.8
    CRITICAL: 0.8 – 1.0
    """
    if score >= 0.8:
        return "CRITICAL"
    elif score >= 0.6:
        return "HIGH"
    elif score >= 0.3:
        return "MEDIUM"
    else:
        return "LOW"


def compute_fraud_risk(text: str, ai_probability: float) -> Dict[str, Any]:
    """
    Compute the final fraud risk score by combining:
    - AI generation probability (weighted 40%)
    - Urgency signals (weighted 20%)
    - Financial redirection signals (weighted 25%)
    - Impersonation signals (weighted 15%)
    
    Returns comprehensive fraud analysis.
    """
    urgency = detect_urgency(text)
    financial = detect_financial_redirection(text)
    impersonation = detect_impersonation(text)

    # Weighted combination
    fraud_intent_score = (
        urgency["score"] * 0.30
        + financial["score"] * 0.40
        + impersonation["score"] * 0.30
    )

    # Final risk score: blend AI probability with fraud intent
    fraud_risk_score = (
        ai_probability * 0.40
        + fraud_intent_score * 0.60
    )

    # Clamp to [0, 1]
    fraud_risk_score = round(min(max(fraud_risk_score, 0.0), 1.0), 4)
    risk_level = classify_risk_level(fraud_risk_score)

    # Collect all flagged phrases
    all_suspicious_phrases = (
        urgency["keywords"]
        + financial["keywords"]
        + impersonation["keywords"]
    )

    return {
        "fraud_risk_score": fraud_risk_score,
        "risk_level": risk_level,
        "fraud_intent_score": round(fraud_intent_score, 4),
        "signals": {
            "urgency": urgency,
            "financial_redirection": financial,
            "impersonation": impersonation,
        },
        "suspicious_phrases": all_suspicious_phrases,
    }
