from __future__ import annotations

from io import BytesIO
from typing import Any


def generate_pdf_report(data: dict[str, Any]) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError as exc:  # pragma: no cover - runtime dependency path
        raise RuntimeError(
            "reportlab is required for PDF export. Install dependencies from requirements.txt."
        ) from exc

    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=letter, topMargin=36, bottomMargin=30)
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    body_style = styles["BodyText"]
    body_style.leading = 16
    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["BodyText"],
        backColor=colors.HexColor("#f4f8fb"),
        borderColor=colors.HexColor("#d9e5ef"),
        borderWidth=1,
        borderPadding=10,
        leading=16,
        spaceAfter=12,
    )

    final_decision = data.get("final_decision", {})
    scenario_analysis = data.get("scenario_analysis", [])
    swot = data.get("swot", {})

    story = [
        Paragraph("VentureMind AI Report", title_style),
        Spacer(1, 12),
        Paragraph(f"<b>Startup Idea:</b> {data.get('idea', 'Unknown startup idea')}", body_style),
        Spacer(1, 10),
        Paragraph(
            (
                f"<b>Final Score:</b> {final_decision.get('score', 0)} / 100<br/>"
                f"<b>Verdict:</b> {final_decision.get('final_verdict', 'Moderate')}<br/>"
                f"<b>Confidence:</b> {final_decision.get('confidence', 0)}%"
            ),
            callout_style,
        ),
        Paragraph("Market Analysis", heading_style),
        Paragraph(str(data.get("market_analysis", "No market analysis available.")), body_style),
        Spacer(1, 10),
        Paragraph("Competitor Insights", heading_style),
        Paragraph(str(data.get("competitor_analysis", "No competitor analysis available.")), body_style),
        Spacer(1, 10),
        Paragraph("SWOT Analysis", heading_style),
        Paragraph(_format_swot_block(swot), body_style),
        Spacer(1, 10),
        Paragraph("Final Decision", heading_style),
        Paragraph(_format_decision_block(final_decision), body_style),
        Spacer(1, 10),
        Paragraph("Investor Scenario Studio", heading_style),
        Paragraph(_format_scenarios_block(scenario_analysis), body_style),
    ]

    document.build(story)
    return buffer.getvalue()


def _format_swot_block(swot: dict[str, Any]) -> str:
    sections = []
    for label in ("strengths", "weaknesses", "opportunities", "threats"):
        items = swot.get(label, []) if isinstance(swot, dict) else []
        if not isinstance(items, list):
            items = []
        body = "<br/>".join(f"• {item}" for item in items) or "• None captured."
        sections.append(f"<b>{label.title()}:</b><br/>{body}")
    return "<br/><br/>".join(sections)


def _format_decision_block(final_decision: dict[str, Any]) -> str:
    return (
        f"<b>Demand:</b> {final_decision.get('market_demand', 'Medium')}<br/>"
        f"<b>Competition:</b> {final_decision.get('competition', 'Medium')}<br/>"
        f"<b>Risk:</b> {final_decision.get('risk', 'Medium')}<br/>"
        f"<b>Reasoning:</b> {final_decision.get('reasoning', 'No decision reasoning available.')}"
    )


def _format_scenarios_block(scenarios: Any) -> str:
    if not isinstance(scenarios, list) or not scenarios:
        return "No scenario analysis available."

    rows = []
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue
        rows.append(
            (
                f"<b>{scenario.get('name', 'Scenario')}:</b> "
                f"Score {scenario.get('score', 0)}, Verdict {scenario.get('verdict', 'Moderate')}, "
                f"Demand {scenario.get('market_demand', 'Medium')}, "
                f"Competition {scenario.get('competition', 'Medium')}, "
                f"Risk {scenario.get('risk', 'Medium')}. "
                f"{scenario.get('summary', '')}"
            )
        )
    return "<br/><br/>".join(rows) or "No scenario analysis available."
