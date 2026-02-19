"""
SentinelAI — Risk Escalation Engine

Determines escalation status and reason based on analysis scores:
- risk_score >= 0.8          → ESCALATED + critical risk reason
- High fraud + low AI        → human-crafted fraud alert
- High AI + low fraud        → synthetic content suspicious alert
- risk_level >= MEDIUM       → auto-create case

Returns escalation metadata to attach to cases.
"""

from typing import Dict, Any, Optional


def evaluate_escalation(
    risk_score: float,
    ai_probability: float,
    fraud_probability: float,
    risk_level: str,
) -> Dict[str, Any]:
    """
    Evaluate whether an analysis result should trigger escalation.

    Returns:
        {
            "should_create_case": bool,
            "status": str,              # OPEN | ESCALATED
            "escalation_reason": str | None,
            "alert_type": str | None,   # human_crafted_fraud | synthetic_suspicious | critical_risk
        }
    """
    should_create_case = risk_level in ("MEDIUM", "HIGH", "CRITICAL")
    status = "OPEN"
    escalation_reason: Optional[str] = None
    alert_type: Optional[str] = None

    # Critical risk → auto-escalate
    if risk_score >= 0.8:
        status = "ESCALATED"
        alert_type = "critical_risk"
        escalation_reason = (
            f"Auto-escalated: Combined risk score {risk_score:.2f} exceeds critical threshold (0.80). "
            f"AI probability: {ai_probability:.1%}, Fraud probability: {fraud_probability:.1%}. "
            "Immediate senior review required."
        )

    # High fraud but low AI → human-crafted fraud
    elif fraud_probability >= 0.6 and ai_probability < 0.3:
        status = "ESCALATED"
        alert_type = "human_crafted_fraud"
        escalation_reason = (
            f"Human-crafted fraud alert: High fraud probability ({fraud_probability:.1%}) "
            f"with low AI generation ({ai_probability:.1%}). This suggests a deliberate, "
            "manually composed fraudulent communication — potentially more sophisticated "
            "than automated attempts."
        )

    # High AI but low fraud → synthetic suspicious
    elif ai_probability >= 0.6 and fraud_probability < 0.3:
        status = "ESCALATED"
        alert_type = "synthetic_suspicious"
        escalation_reason = (
            f"Synthetic content alert: High AI generation probability ({ai_probability:.1%}) "
            f"with low direct fraud indicators ({fraud_probability:.1%}). Content appears to be "
            "AI-generated and may be used for social engineering, impersonation, or "
            "to bypass content validation systems."
        )

    # High risk level but not critical
    elif risk_level == "HIGH":
        status = "OPEN"
        escalation_reason = (
            f"High risk detected: risk_score={risk_score:.2f}, "
            f"AI={ai_probability:.1%}, Fraud={fraud_probability:.1%}. "
            "Queued for analyst review."
        )

    # Medium risk
    elif risk_level == "MEDIUM":
        status = "OPEN"
        escalation_reason = (
            f"Medium risk detected: risk_score={risk_score:.2f}. "
            "Case created for monitoring."
        )

    return {
        "should_create_case": should_create_case,
        "status": status,
        "escalation_reason": escalation_reason,
        "alert_type": alert_type,
    }
