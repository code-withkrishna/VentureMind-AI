from __future__ import annotations
from typing import Any


SCENARIO_SPECS = [
    {
        "name": "Base Case",
        "icon": "◆",
        "demand_shift": 0, "competition_shift": 0, "risk_shift": 0, "confidence_shift": 0,
        "summary": "Current market conditions based on collected evidence.",
        "implication": "Proceed with standard go-to-market planning.",
    },
    {
        "name": "Bull Case",
        "icon": "▲",
        "demand_shift": 14, "competition_shift": -10, "risk_shift": -12, "confidence_shift": 6,
        "summary": "Faster adoption, clear pain, low go-to-market friction, and a fragmented competitor field.",
        "implication": "Raise a pre-seed and move fast — the window is open.",
    },
    {
        "name": "Bear Case",
        "icon": "▼",
        "demand_shift": -16, "competition_shift": 12, "risk_shift": 14, "confidence_shift": -10,
        "summary": "Slower traction, sharper incumbent response, tougher execution than modelled.",
        "implication": "Validate a single wedge customer segment before committing runway.",
    },
    {
        "name": "Regulatory Headwind",
        "icon": "⚖",
        "demand_shift": -6, "competition_shift": 4, "risk_shift": 22, "confidence_shift": -8,
        "summary": "Key compliance burden materialises — GDPR, HIPAA, FDA, or sector-specific licensing.",
        "implication": "Map the regulatory surface area immediately. Budget 6–12 months for approvals.",
    },
    {
        "name": "Breakout Timing",
        "icon": "⚡",
        "demand_shift": 20, "competition_shift": -4, "risk_shift": -8, "confidence_shift": 8,
        "summary": "A platform shift or macro event (AI wave, new regulation, infrastructure unlock) dramatically accelerates demand.",
        "implication": "Position as the category-defining solution and move to Series A storytelling now.",
    },
]


def build_investor_scenarios(final_decision: dict[str, Any]) -> list[dict[str, Any]]:
    demand_score     = _component_score(final_decision, "demand_score",     "market_demand", positive=True)
    competition_score = _component_score(final_decision, "competition_score", "competition",  positive=False)
    risk_score       = _component_score(final_decision, "risk_score",       "risk",          positive=False)
    confidence       = int(final_decision.get("confidence", 0))
    base_score       = int(final_decision.get("score", 0))

    scenarios = []
    for spec in SCENARIO_SPECS:
        if spec["name"] == "Base Case":
            sc_score   = base_score
            sc_demand  = str(final_decision.get("market_demand", _label(demand_score)))
            sc_comp    = str(final_decision.get("competition",   _label(competition_score)))
            sc_risk    = str(final_decision.get("risk",          _label(risk_score)))
            sc_verdict = str(final_decision.get("final_verdict", _verdict(base_score)))
            sc_conf    = confidence
        else:
            sd = _clamp(demand_score      + spec["demand_shift"])
            sc = _clamp(competition_score + spec["competition_shift"])
            sr = _clamp(risk_score        + spec["risk_shift"])
            sc_score   = _weighted(sd, sc, sr)
            sc_demand  = _label(sd)
            sc_comp    = _label(sc)
            sc_risk    = _label(sr)
            sc_verdict = _verdict(sc_score)
            sc_conf    = _clamp(confidence + spec["confidence_shift"])

        scenarios.append({
            "name":        spec["name"],
            "icon":        spec["icon"],
            "score":       sc_score,
            "delta":       sc_score - base_score,
            "confidence":  sc_conf,
            "market_demand": sc_demand,
            "competition": sc_comp,
            "risk":        sc_risk,
            "verdict":     sc_verdict,
            "summary":     spec["summary"],
            "implication": spec["implication"],
        })
    return scenarios


def _component_score(fd: dict, numeric_key: str, label_key: str, *, positive: bool) -> int:
    if numeric_key in fd:
        return _clamp(int(fd[numeric_key]))
    label = str(fd.get(label_key, "Medium")).strip().lower()
    mapping = {"high": 78, "medium": 56, "low": 30} if positive else {"high": 74, "medium": 52, "low": 28}
    return mapping.get(label, 52)


def _weighted(demand: int, competition: int, risk: int) -> int:
    return _clamp(int(round(demand * 0.5 + (100 - competition) * 0.3 + (100 - risk) * 0.2)))


def _label(score: int) -> str:
    if score >= 70: return "High"
    if score >= 40: return "Medium"
    return "Low"


def _verdict(score: int) -> str:
    if score >= 72: return "Strong"
    if score >= 48: return "Moderate"
    return "Weak"


def _clamp(v: int) -> int:
    return max(0, min(100, v))
