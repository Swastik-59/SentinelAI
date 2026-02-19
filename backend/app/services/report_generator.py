"""
SentinelAI — PDF Report Generator

Generates professional investigation reports for cases including:
- Case summary & risk scores
- LLM explanation
- Fraud signal breakdown
- Investigation timeline (case notes)
- Investigator details

Uses reportlab for PDF generation.
"""

import io
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not installed — PDF export disabled")


# ── Risk level colours ─────────────────────────────────────────────────────

RISK_COLORS = {
    "LOW": colors.HexColor("#22c55e"),
    "MEDIUM": colors.HexColor("#eab308"),
    "HIGH": colors.HexColor("#f97316"),
    "CRITICAL": colors.HexColor("#ef4444"),
}


def generate_case_pdf(
    case: Dict[str, Any],
    notes: List[Dict[str, Any]],
) -> bytes:
    """
    Generate a PDF report for an investigation case.
    Returns raw PDF bytes.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is not installed. Run: pip install reportlab")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    # Custom styles
    styles.add(ParagraphStyle(
        "SentinelTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#334155"),
        spaceBefore=14,
        spaceAfter=6,
        borderWidth=0,
    ))
    styles.add(ParagraphStyle(
        "BodySmall",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#475569"),
        leading=13,
    ))
    styles.add(ParagraphStyle(
        "NoteText",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#334155"),
        leading=12,
        leftIndent=10,
    ))

    elements = []

    # ── Header ─────────────────────────────────────────────────────────────
    elements.append(Paragraph("SentinelAI — Investigation Report", styles["SentinelTitle"]))
    elements.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        styles["BodySmall"],
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1")))
    elements.append(Spacer(1, 8))

    # ── Case Summary ───────────────────────────────────────────────────────
    elements.append(Paragraph("Case Summary", styles["SectionHeader"]))

    risk_level = case.get("risk_level", "LOW")
    risk_color = RISK_COLORS.get(risk_level, colors.black)

    summary_data = [
        ["Case ID", case.get("id", "N/A")],
        ["Status", case.get("status", "OPEN")],
        ["Risk Level", risk_level],
        ["Risk Score", f"{case.get('risk_score', 0):.4f}"],
        ["AI Probability", f"{case.get('ai_probability', 0):.1%}"],
        ["Fraud Probability", f"{case.get('fraud_probability', 0):.1%}"],
        ["Assigned To", case.get("assigned_to") or "Unassigned"],
        ["Client", case.get("client_id") or "N/A"],
        ["Created", case.get("created_at", "N/A")],
        ["Last Updated", case.get("updated_at", "N/A")],
    ]

    table = Table(summary_data, colWidths=[120, 380])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#334155")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#475569")),
        ("TEXTCOLOR", (1, 2), (1, 2), risk_color),  # Risk level color
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 8))

    # ── Escalation Reason ──────────────────────────────────────────────────
    escalation = case.get("escalation_reason")
    if escalation:
        elements.append(Paragraph("Escalation Reason", styles["SectionHeader"]))
        elements.append(Paragraph(escalation, styles["BodySmall"]))
        elements.append(Spacer(1, 6))

    # ── Explanation ────────────────────────────────────────────────────────
    result = case.get("result") or {}
    explanation = result.get("explanation", "")
    if explanation:
        elements.append(Paragraph("LLM Analysis / Explanation", styles["SectionHeader"]))
        # Wrap long text
        for para in explanation.split("\n"):
            para = para.strip()
            if para:
                elements.append(Paragraph(para, styles["BodySmall"]))
                elements.append(Spacer(1, 3))
        elements.append(Spacer(1, 6))

    # ── Fraud Signals ──────────────────────────────────────────────────────
    fraud_signals = result.get("fraud_signals", {})
    if any(fraud_signals.get(cat, {}).get("count", 0) > 0 for cat in ("urgency", "financial_redirection", "impersonation")):
        elements.append(Paragraph("Fraud Signal Breakdown", styles["SectionHeader"]))
        signal_data = [["Category", "Score", "Count", "Keywords"]]
        for cat_key, cat_label in [
            ("urgency", "Urgency Language"),
            ("financial_redirection", "Financial Redirection"),
            ("impersonation", "Impersonation"),
        ]:
            sig = fraud_signals.get(cat_key, {})
            kw_str = ", ".join(sig.get("keywords", [])[:5])
            signal_data.append([
                cat_label,
                f"{sig.get('score', 0):.0%}",
                str(sig.get("count", 0)),
                kw_str or "None",
            ])

        sig_table = Table(signal_data, colWidths=[120, 50, 50, 280])
        sig_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#475569")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(sig_table)
        elements.append(Spacer(1, 8))

    # ── Details ────────────────────────────────────────────────────────────
    details = result.get("details", [])
    if details:
        elements.append(Paragraph("Analysis Details", styles["SectionHeader"]))
        for d in details:
            elements.append(Paragraph(f"• {d}", styles["BodySmall"]))
        elements.append(Spacer(1, 8))

    # ── Investigation Timeline ─────────────────────────────────────────────
    if notes:
        elements.append(Paragraph("Investigation Timeline", styles["SectionHeader"]))
        for note in notes:
            ts = note.get("timestamp", "")
            author = note.get("author", "Unknown")
            text = note.get("note", "")
            elements.append(Paragraph(
                f"<b>{ts}</b> — <i>{author}</i>",
                styles["BodySmall"],
            ))
            elements.append(Paragraph(text, styles["NoteText"]))
            elements.append(Spacer(1, 4))

    # ── Footer ─────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1")))
    elements.append(Paragraph(
        "This report was generated by SentinelAI — Banking Fraud Defense Platform. "
        "Confidential. For authorized personnel only.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7,
                       textColor=colors.HexColor("#94a3b8"), alignment=1),
    ))

    doc.build(elements)
    return buffer.getvalue()
