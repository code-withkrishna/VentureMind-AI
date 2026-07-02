from __future__ import annotations

from core.models import AgentMessage, EvaluationReport, ResearchPlan, ToolObservation

# ── Demand signal vocabulary ─────────────────────────────────────────────────
_DEMAND_POSITIVE = {
    "growing", "growth", "adoption", "demand", "urgent", "pain", "manual",
    "inefficiency", "expanding", "underserved", "billion", "million", "market",
    "revenue", "subscription", "paying", "enterprise", "smb", "shortage",
    "waitlist", "funded", "investment", "traction", "retention",
}
_DEMAND_NEGATIVE = {
    "declining", "shrinking", "saturated", "niche", "limited", "stagnant",
    "commoditised", "unprofitable", "free", "open-source", "legacy",
}

# ── Competition vocabulary ────────────────────────────────────────────────────
_COMPETITION_HIGH = {
    "competitor", "competition", "crowded", "saturated", "incumbent", "leader",
    "alternative", "dominant", "well-funded", "moat", "switching-cost",
    "monopoly", "duopoly", "network-effect",
}
_COMPETITION_FRAGMENTED = {
    "fragmented", "niche", "underserved", "white-space", "greenfield",
    "early-stage", "emerging", "no-clear-leader",
}

# ── Risk vocabulary ───────────────────────────────────────────────────────────
_RISK_HIGH = {
    "risk", "regulation", "compliance", "expensive", "slow", "uncertain",
    "trust", "failure", "difficult", "privacy", "gdpr", "hipaa", "fda",
    "hardware", "integration", "churn", "commoditise", "margin", "burn",
}
_RISK_MITIGATING = {
    "proven", "validated", "pilot", "contract", "loi", "patent", "moat",
    "exclusive", "proprietary", "defensible", "recurring",
}

# ── Verdict narrative library ─────────────────────────────────────────────────
_BUILD_NARRATIVES = [
    "Market pull is visible and the competitive landscape has defensible entry points.",
    "Demand signals are strong and execution risk is within manageable bounds.",
    "Evidence favours moving to an MVP — the market window appears open.",
]
_CAUTION_NARRATIVES = [
    "Demand is real but execution complexity or competition warrants de-risking before committing runway.",
    "Promising signal with meaningful gaps — validate the riskiest assumption first.",
    "The idea has merit but the market or risk profile needs a sharper wedge strategy.",
]
_REJECT_NARRATIVES = [
    "Demand is unclear, competition is entrenched, or execution risk outweighs expected return.",
    "Evidence does not yet justify committing a founding team's time and capital.",
    "Rework the positioning or pivot the problem before re-validating.",
]


class DecisionAgent:

    def decide(
        self,
        question: str,
        plan: ResearchPlan,
        observations: list[ToolObservation],
        evaluation: EvaluationReport,
        correlation_id: str,
    ) -> AgentMessage:
        decision = self._build_decision(question, plan, observations, evaluation)
        return AgentMessage(
            sender="decision_agent",
            recipient="orchestrator",
            message_type="startup_decision",
            payload=decision,
            correlation_id=correlation_id,
        )

    def _build_decision(
        self,
        question: str,
        plan: ResearchPlan,
        observations: list[ToolObservation],
        evaluation: EvaluationReport,
    ) -> dict[str, object]:
        market_obs = [o for o in observations if not self._is_competitor(o)]
        comp_obs   = [o for o in observations if self._is_competitor(o)]
        text       = self._combined_text(observations)

        demand_pos = self._hits(text, _DEMAND_POSITIVE)
        demand_neg = self._hits(text, _DEMAND_NEGATIVE)
        comp_high  = self._hits(text, _COMPETITION_HIGH)
        comp_frag  = self._hits(text, _COMPETITION_FRAGMENTED)
        risk_high  = self._hits(text, _RISK_HIGH)
        risk_mit   = self._hits(text, _RISK_MITIGATING)

        source_count = sum(len(o.sources) for o in observations)
        failed_steps = sum(1 for o in observations if o.status != "completed")
        evidence_quality = min(source_count, 8)

        # ── Demand score (0–100) ─────────────────────────────────────────────
        demand_score = min(100, max(0, int(
            30
            + demand_pos * 7
            - demand_neg * 5
            + len(market_obs) * 5
            + evidence_quality * 3
            + max(evaluation.confidence - 50, 0) // 3
        )))

        # ── Competition score (0=low pressure, 100=high pressure) ───────────
        competition_score = min(100, max(0, int(
            20
            + comp_high * 9
            - comp_frag * 6
            + len(comp_obs) * 10
            + max(len(comp_obs) - 1, 0) * 5
        )))

        # ── Risk score (0=low risk, 100=high risk) ───────────────────────────
        risk_score = min(100, max(0, int(
            18
            + risk_high * 8
            - risk_mit * 5
            + comp_high * 3
            + len(evaluation.gaps) * 10
            + failed_steps * 12
            + max(60 - evaluation.confidence, 0) // 3
        )))

        # ── Composite weighted score ─────────────────────────────────────────
        weighted = int(round(
            demand_score * 0.50
            + (100 - competition_score) * 0.30
            + (100 - risk_score) * 0.20
        ))
        score = max(0, min(100, weighted))

        # ── Confidence ───────────────────────────────────────────────────────
        confidence = max(0, min(100, int(round(
            evaluation.confidence * 0.65
            + evidence_quality * 4
            - failed_steps * 7
        ))))

        # ── Labels ───────────────────────────────────────────────────────────
        market_demand = self._label(demand_score)
        competition   = self._label(competition_score)
        risk          = self._label(risk_score)

        if score >= 72:
            final_verdict = "Strong"
            narrative     = _BUILD_NARRATIVES[demand_pos % len(_BUILD_NARRATIVES)]
            action        = "BUILD"
        elif score >= 48:
            final_verdict = "Moderate"
            narrative     = _CAUTION_NARRATIVES[risk_high % len(_CAUTION_NARRATIVES)]
            action        = "CAUTION"
        else:
            final_verdict = "Weak"
            narrative     = _REJECT_NARRATIVES[failed_steps % len(_REJECT_NARRATIVES)]
            action        = "REJECT"

        # ── Human-readable reasoning ─────────────────────────────────────────
        demand_note = (
            f"demand is {market_demand.lower()} — {demand_pos} positive signals vs {demand_neg} headwinds"
        )
        comp_note = (
            f"competition reads {competition.lower()} — {comp_high} incumbent signals, "
            f"{comp_frag} fragmentation signals"
        )
        risk_note = (
            f"execution risk is {risk.lower()} — {len(evaluation.gaps)} evaluator gaps, "
            f"{failed_steps} failed research steps, {risk_mit} de-risking signals"
        )
        reasoning = (
            f"{narrative} Specifically: {demand_note}; {comp_note}; {risk_note}. "
            f"Composite score: {score}/100 (demand ×0.5, competition penalty ×0.3, "
            f"risk penalty ×0.2). Evidence confidence: {confidence}%."
        )

        return {
            "score":            score,
            "market_demand":    market_demand,
            "competition":      competition,
            "risk":             risk,
            "final_verdict":    final_verdict,
            "action":           action,
            "confidence":       confidence,
            "reasoning":        reasoning,
            "plan_summary":     plan.plan_summary,
            "demand_score":     demand_score,
            "competition_score": competition_score,
            "risk_score":       risk_score,
            "source_count":     source_count,
            "evidence_quality": evidence_quality,
            "why_this_decision": [
                f"Demand scored {demand_score}/100: {demand_pos} positive demand signals across {len(market_obs)} market research steps.",
                f"Competition scored {competition_score}/100: {comp_high} incumbent signals from {len(comp_obs)} competitor analysis steps.",
                f"Risk scored {risk_score}/100: {len(evaluation.gaps)} open gaps flagged by the evaluator agent.",
                f"Final composite: {score}/100 using 50/30/20 demand/competition/risk weighting.",
            ],
            "decision_breakdown": {
                "demand_weight": 0.5,
                "competition_penalty_weight": 0.3,
                "risk_penalty_weight": 0.2,
                "demand_score":      demand_score,
                "competition_score": competition_score,
                "risk_score":        risk_score,
                "demand_signals":    demand_pos,
                "demand_headwinds":  demand_neg,
                "risk_signals":      risk_high,
                "risk_mitigators":   risk_mit,
            },
        }

    @staticmethod
    def _combined_text(observations: list[ToolObservation]) -> str:
        return " ".join(
            " ".join([
                o.objective, o.query, o.summary,
                " ".join(o.data_points),
                " ".join(f"{s.title} {s.snippet}" for s in o.sources),
            ])
            for o in observations
        ).lower()

    @staticmethod
    def _hits(text: str, terms: set[str]) -> int:
        return sum(text.count(t) for t in terms)

    @staticmethod
    def _label(score: int) -> str:
        if score >= 70: return "High"
        if score >= 40: return "Medium"
        return "Low"

    @staticmethod
    def _is_competitor(o: ToolObservation) -> bool:
        return any(t in f"{o.objective} {o.query}".lower()
                   for t in {"competitor", "competition", "alternative"})
