from __future__ import annotations

from html import escape
from typing import Any

from core.models import TraceEvent

_STEP_STAGE_INDEX = {
    "planning": 0,
    "market_research": 1,
    "competitor_analysis": 2,
    "evaluation": 3,
    "decision": 4,
    "report": 4,
    "storage": 4,
}

_ANALYSIS_STAGE_INDEX = {
    "market_research": 0,
    "competitor_analysis": 1,
    "evaluation": 2,
    "decision": 3,
    "report": 3,
    "storage": 3,
}

_ANALYSIS_STEPS = [
    ("Market Analysis", "Pulling demand and timing signals"),
    ("Competitor Analysis", "Mapping rivals and substitutes"),
    ("Risk Evaluation", "Stress-testing execution risk"),
    ("Investment Decision", "Packaging the final verdict"),
]


def workflow_html(workflow_steps: list[str], events: list[TraceEvent]) -> str:
    active_index = _active_step_index(events, len(workflow_steps))
    cards = []
    for index, label in enumerate(workflow_steps):
        if index < active_index:
            status = "Done"
            background = "rgba(46, 204, 113, 0.14)"
            border = "rgba(46, 204, 113, 0.32)"
            color = "#9ff0bb"
        elif index == active_index:
            status = "Live"
            background = "rgba(255, 159, 67, 0.18)"
            border = "rgba(255, 159, 67, 0.42)"
            color = "#ffd0a1"
        else:
            status = "Queued"
            background = "rgba(11, 26, 42, 0.88)"
            border = "rgba(154, 176, 196, 0.18)"
            color = "#dce9f5"

        cards.append(
            f"""
            <div style="padding:0.85rem 0.95rem;border-radius:16px;border:1px solid {border};background:{background};margin-bottom:0.55rem;">
                <div style="font-size:0.72rem;letter-spacing:0.14em;text-transform:uppercase;color:#9ab0c4;margin-bottom:0.25rem;">{status}</div>
                <div style="font-weight:600;color:{color};">{escape(label)}</div>
            </div>
            """
        )
    return "".join(cards)


def analysis_stepper_html(events: list[TraceEvent]) -> str:
    active_index = _analysis_active_index(events)
    cards = []
    for index, (label, detail) in enumerate(_ANALYSIS_STEPS):
        if index < active_index:
            status = "Done"
            background = "linear-gradient(180deg, rgba(38, 166, 91, 0.18), rgba(17, 50, 35, 0.72))"
            border = "rgba(46, 204, 113, 0.34)"
            accent = "#9ff0bb"
        elif index == active_index:
            status = "Live"
            background = "linear-gradient(180deg, rgba(255, 159, 67, 0.20), rgba(44, 28, 12, 0.84))"
            border = "rgba(255, 159, 67, 0.38)"
            accent = "#ffd0a1"
        else:
            status = "Queued"
            background = "linear-gradient(180deg, rgba(12, 28, 44, 0.94), rgba(8, 18, 31, 0.84))"
            border = "rgba(154, 176, 196, 0.16)"
            accent = "#dce9f5"

        cards.append(
            f"""
            <div style="padding:1rem;border-radius:18px;border:1px solid {border};background:{background};min-height:128px;">
                <div style="font-size:0.72rem;letter-spacing:0.14em;text-transform:uppercase;color:#9ab0c4;margin-bottom:0.45rem;">{status}</div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:700;color:{accent};margin-bottom:0.35rem;">{escape(label)}</div>
                <div style="color:#c8d8e8;line-height:1.55;font-size:0.92rem;">{escape(detail)}</div>
            </div>
            """
        )
    return (
        '<div style="display:grid;grid-template-columns:repeat(4, minmax(0, 1fr));gap:0.8rem;">'
        + "".join(cards)
        + "</div>"
    )


def verdict_banner_html(final_decision: dict[str, Any]) -> str:
    score = int(final_decision.get("score", 0))
    confidence = int(final_decision.get("confidence", 0))
    risk = str(final_decision.get("risk", "Medium"))
    verdict = str(final_decision.get("final_verdict", "Moderate"))
    action = _decision_action(verdict)
    color = _sentiment_color("verdict", verdict)
    background = _verdict_background(verdict)
    description = _verdict_description(verdict)

    return f"""
    <div style="padding:1.35rem 1.45rem;border-radius:24px;border:1px solid rgba(255,255,255,0.10);background:{background};box-shadow:0 20px 48px rgba(0,0,0,0.24);margin-bottom:0.8rem;">
        <div style="display:flex;justify-content:space-between;gap:1.2rem;align-items:flex-start;flex-wrap:wrap;">
            <div>
                <div style="font-size:0.76rem;letter-spacing:0.16em;text-transform:uppercase;color:#d7e6f4;margin-bottom:0.5rem;">Final Investor Signal</div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:2.5rem;font-weight:700;color:white;line-height:1;">{escape(action)}</div>
                <div style="margin-top:0.55rem;color:#edf5fb;font-size:1rem;line-height:1.6;max-width:620px;">{escape(description)}</div>
            </div>
            <div style="padding:0.85rem 1rem;border-radius:18px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.12);min-width:240px;">
                <div style="font-size:0.72rem;letter-spacing:0.14em;text-transform:uppercase;color:#d7e6f4;margin-bottom:0.25rem;">Live Verdict</div>
                <div style="font-size:1.15rem;font-weight:700;color:{color};margin-bottom:0.4rem;">{escape(verdict)}</div>
                <div style="display:flex;justify-content:space-between;gap:1rem;color:#eef4fb;font-size:0.96rem;">
                    <span>Score <strong>{score}/100</strong></span>
                    <span>Confidence <strong>{confidence}%</strong></span>
                    <span>Risk <strong>{escape(risk)}</strong></span>
                </div>
            </div>
        </div>
    </div>
    """


def decision_card_html(final_decision: dict[str, Any], title: str = "VentureMind Verdict") -> str:
    score = int(final_decision.get("score", 0))
    confidence = int(final_decision.get("confidence", 0))
    demand = str(final_decision.get("market_demand", "Medium"))
    competition = str(final_decision.get("competition", "Medium"))
    risk = str(final_decision.get("risk", "Medium"))
    verdict = str(final_decision.get("final_verdict", "Moderate"))
    reasoning = str(final_decision.get("reasoning", "No decision reasoning available."))

    verdict_color = _sentiment_color("verdict", verdict)
    demand_color = _sentiment_color("positive", demand)
    competition_color = _sentiment_color("negative", competition)
    risk_color = _sentiment_color("negative", risk)

    return f"""
    <div style="padding:1.15rem 1.2rem;border-radius:22px;border:1px solid rgba(255,255,255,0.12);background:linear-gradient(135deg, rgba(10,20,34,0.96), rgba(17,37,57,0.94));box-shadow:0 18px 44px rgba(0,0,0,0.18);">
        <div style="font-size:0.78rem;letter-spacing:0.16em;text-transform:uppercase;color:#ff9f43;margin-bottom:0.4rem;">{escape(title)}</div>
        <div style="color:white;font-family:'Space Grotesk',sans-serif;font-size:1.45rem;font-weight:700;margin-bottom:0.85rem;">{score} / 100</div>
        <div style="display:grid;grid-template-columns:repeat(2, minmax(0, 1fr));gap:0.55rem;margin-bottom:0.9rem;">
            {_metric_chip("Demand", demand, demand_color)}
            {_metric_chip("Competition", competition, competition_color)}
            {_metric_chip("Risk", risk, risk_color)}
            {_metric_chip("Confidence", f"{confidence}%", "#7dd3fc")}
        </div>
        <div style="padding:0.7rem 0.8rem;border-radius:16px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);margin-bottom:0.85rem;">
            <div style="font-size:0.75rem;letter-spacing:0.14em;text-transform:uppercase;color:#9ab0c4;margin-bottom:0.2rem;">Final Verdict</div>
            <div style="font-size:1.05rem;font-weight:700;color:{verdict_color};">{escape(_verdict_label(verdict))}</div>
        </div>
        <div style="color:#dce9f5;line-height:1.55;font-size:0.96rem;">{escape(reasoning)}</div>
    </div>
    """


def decision_heatmap_html(final_decision: dict[str, Any]) -> str:
    demand_score = int(final_decision.get("demand_score", _score_from_label(final_decision.get("market_demand", "Medium"))))
    competition_score = int(
        final_decision.get("competition_score", _score_from_label(final_decision.get("competition", "Medium")))
    )
    risk_score = int(final_decision.get("risk_score", _score_from_label(final_decision.get("risk", "Medium"))))
    rows = [
        ("Demand Strength", demand_score, "#86efac"),
        ("Competition Pressure", competition_score, "#fbbf24"),
        ("Execution Risk", risk_score, "#fda4af"),
    ]
    bars = []
    for label, score, color in rows:
        bars.append(
            f"""
            <div style="margin-bottom:0.85rem;">
                <div style="display:flex;justify-content:space-between;gap:1rem;margin-bottom:0.25rem;">
                    <div style="color:#dce9f5;font-weight:600;">{escape(label)}</div>
                    <div style="color:{color};font-weight:700;">{score}/100</div>
                </div>
                <div style="height:10px;border-radius:999px;background:rgba(255,255,255,0.06);overflow:hidden;">
                    <div style="height:10px;border-radius:999px;width:{score}%;background:{color};"></div>
                </div>
            </div>
            """
        )
    return (
        '<div style="padding:1rem 1rem 0.95rem 1rem;border-radius:18px;border:1px solid rgba(154,176,196,0.16);background:rgba(9,17,31,0.72);backdrop-filter:blur(10px);margin-bottom:0.8rem;">'
        '<div style="color:#ff9f43;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;margin-bottom:0.25rem;">Decision Heatmap</div>'
        '<div style="color:white;font-family:\'Space Grotesk\',sans-serif;font-size:1.1rem;font-weight:700;margin-bottom:0.6rem;">Why the score landed here</div>'
        + "".join(bars)
        + "</div>"
    )


def investor_scenarios_html(scenarios: list[dict[str, Any]]) -> str:
    cards = []
    for scenario in scenarios:
        delta = int(scenario.get("delta", 0))
        delta_prefix = "+" if delta > 0 else ""
        verdict_color = _sentiment_color("verdict", str(scenario.get("verdict", "Moderate")))
        cards.append(
            f"""
            <div style="padding:0.95rem;border-radius:16px;border:1px solid rgba(154,176,196,0.16);background:rgba(11,26,42,0.86);">
                <div style="display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;margin-bottom:0.45rem;">
                    <div>
                        <div style="color:white;font-weight:700;">{escape(str(scenario.get("name", "Scenario")))}</div>
                        <div style="color:#9ab0c4;font-size:0.9rem;">{escape(str(scenario.get("summary", "")))}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:white;font-family:'Space Grotesk',sans-serif;font-size:1.2rem;font-weight:700;">{int(scenario.get("score", 0))}</div>
                        <div style="color:{verdict_color};font-size:0.85rem;font-weight:700;">{escape(str(scenario.get("verdict", "Moderate")))}</div>
                    </div>
                </div>
                <div style="display:flex;justify-content:space-between;gap:0.8rem;font-size:0.9rem;color:#dce9f5;flex-wrap:wrap;">
                    <span>Demand: {escape(str(scenario.get("market_demand", "Medium")))}</span>
                    <span>Competition: {escape(str(scenario.get("competition", "Medium")))}</span>
                    <span>Risk: {escape(str(scenario.get("risk", "Medium")))}</span>
                </div>
                <div style="margin-top:0.55rem;color:#ffcf99;font-size:0.88rem;font-weight:700;">Score shift: {delta_prefix}{delta}</div>
            </div>
            """
        )
    return (
        '<div style="padding:1rem 1rem 0.95rem 1rem;border-radius:18px;border:1px solid rgba(154,176,196,0.16);background:rgba(9,17,31,0.72);backdrop-filter:blur(10px);margin-bottom:0.8rem;">'
        '<div style="color:#ff9f43;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;margin-bottom:0.25rem;">Investor Scenario Studio</div>'
        '<div style="color:white;font-family:\'Space Grotesk\',sans-serif;font-size:1.1rem;font-weight:700;margin-bottom:0.6rem;">How the verdict changes under pressure</div>'
        '<div style="display:grid;grid-template-columns:repeat(3, minmax(0, 1fr));gap:0.75rem;">'
        + "".join(cards)
        + "</div></div>"
    )


def section_card_html(label: str, title: str, body: str) -> str:
    return f"""
    <div style="padding:1rem 1rem 0.95rem 1rem;border-radius:18px;border:1px solid rgba(154,176,196,0.16);background:rgba(9,17,31,0.72);backdrop-filter:blur(10px);margin-bottom:0.8rem;">
        <div style="color:#ff9f43;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;margin-bottom:0.25rem;">{escape(label)}</div>
        <div style="color:white;font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:700;margin-bottom:0.35rem;">{escape(title)}</div>
        <div style="color:#dce9f5;line-height:1.6;">{escape(body)}</div>
    </div>
    """


def swot_html(swot: dict[str, list[str]]) -> str:
    sections = []
    palette = {
        "strengths": "#7dd3fc",
        "weaknesses": "#fda4af",
        "opportunities": "#86efac",
        "threats": "#fdba74",
    }
    for key, color in palette.items():
        items = swot.get(key, []) if isinstance(swot, dict) else []
        if not isinstance(items, list):
            items = []
        body = "".join(f"<li>{escape(str(item))}</li>" for item in items) or "<li>None surfaced yet.</li>"
        sections.append(
            f"""
            <div style="padding:0.9rem;border-radius:16px;border:1px solid rgba(154,176,196,0.14);background:rgba(11,26,42,0.86);">
                <div style="font-size:0.76rem;letter-spacing:0.14em;text-transform:uppercase;color:{color};margin-bottom:0.35rem;">{escape(key)}</div>
                <ul style="margin:0;padding-left:1rem;color:#dce9f5;line-height:1.55;">{body}</ul>
            </div>
            """
        )
    return (
        '<div style="display:grid;grid-template-columns:repeat(2, minmax(0, 1fr));gap:0.8rem;">'
        + "".join(sections)
        + "</div>"
    )


def _active_step_index(events: list[TraceEvent], step_count: int) -> int:
    if not events:
        return 0
    latest = events[-1]
    if latest.stage == "storage":
        return step_count
    return _STEP_STAGE_INDEX.get(latest.stage, 0)


def _analysis_active_index(events: list[TraceEvent]) -> int:
    if not events:
        return 0
    latest = next((event for event in reversed(events) if event.stage in _ANALYSIS_STAGE_INDEX), None)
    if latest is None:
        return 0
    if latest.stage == "storage":
        return len(_ANALYSIS_STEPS)
    return _ANALYSIS_STAGE_INDEX.get(latest.stage, 0)


def _metric_chip(label: str, value: str, color: str) -> str:
    return (
        f'<div style="padding:0.6rem 0.7rem;border-radius:14px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);">'
        f'<div style="font-size:0.72rem;letter-spacing:0.12em;text-transform:uppercase;color:#9ab0c4;margin-bottom:0.1rem;">{escape(label)}</div>'
        f'<div style="font-weight:700;color:{color};">{escape(value)}</div>'
        "</div>"
    )


def _decision_action(verdict: str) -> str:
    if verdict == "Strong":
        return "BUILD"
    if verdict == "Moderate":
        return "CAUTION"
    return "REJECT"


def _verdict_label(verdict: str) -> str:
    if verdict == "Strong":
        return "Worth Pursuing"
    if verdict == "Moderate":
        return "Promising but Needs Validation"
    return "Weak Opportunity Right Now"


def _verdict_description(verdict: str) -> str:
    if verdict == "Strong":
        return "The market signal is compelling enough to justify moving forward, with focused execution."
    if verdict == "Moderate":
        return "The idea has promise, but founders should validate core assumptions before committing major runway."
    return "The downside currently outweighs the upside, so this idea should be reworked or deprioritized."


def _verdict_background(verdict: str) -> str:
    if verdict == "Strong":
        return "linear-gradient(135deg, rgba(17, 86, 47, 0.96), rgba(12, 31, 22, 0.96))"
    if verdict == "Moderate":
        return "linear-gradient(135deg, rgba(130, 90, 13, 0.96), rgba(40, 28, 12, 0.96))"
    return "linear-gradient(135deg, rgba(125, 33, 33, 0.96), rgba(36, 16, 16, 0.96))"


def _sentiment_color(mode: str, value: str) -> str:
    normalized = value.strip().lower()
    if mode == "positive":
        if normalized == "high":
            return "#86efac"
        if normalized == "medium":
            return "#fde68a"
        return "#fda4af"
    if mode == "negative":
        if normalized == "high":
            return "#fda4af"
        if normalized == "medium":
            return "#fde68a"
        return "#86efac"
    if mode == "verdict":
        if normalized == "strong":
            return "#86efac"
        if normalized == "moderate":
            return "#fde68a"
        return "#fda4af"
    return "#dce9f5"


def _score_from_label(value: Any) -> int:
    normalized = str(value).strip().lower()
    if normalized == "high":
        return 78
    if normalized == "medium":
        return 55
    return 30
