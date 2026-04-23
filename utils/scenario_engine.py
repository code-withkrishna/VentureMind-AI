from __future__ import annotations

from typing import Any


def build_investor_scenarios(final_decision: dict[str, Any]) -> list[dict[str, Any]]:
    demand_score = _component_score(final_decision, "demand_score", "market_demand", positive=True)
    competition_score = _component_score(final_decision, "competition_score", "competition", positive=False)
    risk_score = _component_score(final_decision, "risk_score", "risk", positive=False)
    confidence = int(final_decision.get("confidence", 0))

    scenario_specs = [
        {
            "name": "Base Case",
            "delta": 0,
            "summary": "Current market conditions based on the collected evidence.",
            "demand_shift": 0,
            "competition_shift": 0,
            "risk_shift": 0,
            "confidence_shift": 0,
        },
        {
            "name": "Bull Case",
            "delta": 0,
            "summary": "Assumes faster adoption, clearer pain, and lower go-to-market friction.",
            "demand_shift": 12,
            "competition_shift": -8,
            "risk_shift": -10,
            "confidence_shift": 5,
        },
        {
            "name": "Bear Case",
            "delta": 0,
            "summary": "Assumes slower traction, sharper incumbent response, and harder execution.",
            "demand_shift": -14,
            "competition_shift": 10,
            "risk_shift": 12,
            "confidence_shift": -8,
        },
    ]

    scenarios = []
    base_score = int(final_decision.get("score", 0))
    for spec in scenario_specs:
        scenario_demand = _clamp(demand_score + spec["demand_shift"])
        scenario_competition = _clamp(competition_score + spec["competition_shift"])
        scenario_risk = _clamp(risk_score + spec["risk_shift"])
        if spec["name"] == "Base Case":
            scenario_score = base_score
            scenario_demand_label = str(final_decision.get("market_demand", _label_from_score(scenario_demand)))
            scenario_competition_label = str(
                final_decision.get("competition", _label_from_score(scenario_competition))
            )
            scenario_risk_label = str(final_decision.get("risk", _label_from_score(scenario_risk)))
            scenario_verdict = str(final_decision.get("final_verdict", _verdict_from_score(base_score)))
        else:
            scenario_score = _calculate_weighted_score(
                scenario_demand,
                scenario_competition,
                scenario_risk,
            )
            scenario_demand_label = _label_from_score(scenario_demand)
            scenario_competition_label = _label_from_score(scenario_competition)
            scenario_risk_label = _label_from_score(scenario_risk)
            scenario_verdict = _verdict_from_score(scenario_score)
        scenarios.append(
            {
                "name": spec["name"],
                "score": scenario_score,
                "delta": scenario_score - base_score,
                "confidence": _clamp(confidence + spec["confidence_shift"]),
                "market_demand": scenario_demand_label,
                "competition": scenario_competition_label,
                "risk": scenario_risk_label,
                "verdict": scenario_verdict,
                "summary": spec["summary"],
            }
        )
    return scenarios


def _component_score(
    final_decision: dict[str, Any],
    numeric_key: str,
    label_key: str,
    *,
    positive: bool,
) -> int:
    if numeric_key in final_decision:
        return _clamp(int(final_decision[numeric_key]))

    label = str(final_decision.get(label_key, "Medium")).strip().lower()
    if positive:
        mapping = {"high": 78, "medium": 56, "low": 30}
    else:
        mapping = {"high": 74, "medium": 52, "low": 28}
    return mapping.get(label, 52)


def _calculate_weighted_score(demand_score: int, competition_score: int, risk_score: int) -> int:
    return _clamp(
        int(
            round(
                demand_score * 0.5
                + (100 - competition_score) * 0.3
                + (100 - risk_score) * 0.2
            )
        )
    )


def _label_from_score(score: int) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def _verdict_from_score(score: int) -> str:
    if score >= 72:
        return "Strong"
    if score >= 48:
        return "Moderate"
    return "Weak"


def _clamp(value: int) -> int:
    return max(0, min(100, value))
