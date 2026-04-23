from __future__ import annotations

from core.models import AgentMessage, EvaluationReport, ResearchPlan, ToolObservation

_POSITIVE_DEMAND_TERMS = {
    "growing",
    "growth",
    "adoption",
    "demand",
    "urgent",
    "pain",
    "manual",
    "inefficiency",
    "expanding",
    "underserved",
}

_COMPETITION_TERMS = {
    "competitor",
    "competition",
    "crowded",
    "saturated",
    "incumbent",
    "leader",
    "alternative",
    "platform",
}

_RISK_TERMS = {
    "risk",
    "regulation",
    "compliance",
    "expensive",
    "slow",
    "uncertain",
    "trust",
    "failure",
    "difficult",
}


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
        market_observations = [
            observation for observation in observations if not self._is_competitor_observation(observation)
        ]
        competitor_observations = [
            observation for observation in observations if self._is_competitor_observation(observation)
        ]
        combined_text = self._combined_text(observations)

        demand_signal_count = self._term_hits(combined_text, _POSITIVE_DEMAND_TERMS)
        competition_signal_count = self._term_hits(combined_text, _COMPETITION_TERMS)
        risk_signal_count = self._term_hits(combined_text, _RISK_TERMS)
        source_count = sum(len(observation.sources) for observation in observations)
        failed_steps = sum(1 for observation in observations if observation.status != "completed")

        demand_score = min(
            100,
            30
            + demand_signal_count * 8
            + len(market_observations) * 6
            + min(source_count, 6) * 4
            + max(evaluation.confidence - 50, 0) // 2,
        )
        competition_score = min(
            100,
            20
            + competition_signal_count * 10
            + len(competitor_observations) * 12
            + max(len(competitor_observations) - 1, 0) * 6,
        )
        risk_score = min(
            100,
            18
            + risk_signal_count * 9
            + competition_signal_count * 4
            + len(evaluation.gaps) * 12
            + failed_steps * 14
            + max(60 - evaluation.confidence, 0) // 2,
        )

        weighted_score = int(
            round(
                demand_score * 0.5
                + (100 - competition_score) * 0.3
                + (100 - risk_score) * 0.2
            )
        )
        score = max(0, min(100, weighted_score))
        confidence = max(
            0,
            min(
                100,
                int(
                    round(
                        evaluation.confidence * 0.7
                        + min(source_count, 6) * 4
                        - failed_steps * 6
                    )
                ),
            ),
        )

        market_demand = self._label_from_score(demand_score)
        competition = self._label_from_score(competition_score)
        risk = self._label_from_score(risk_score)
        if score >= 72:
            final_verdict = "Strong"
        elif score >= 48:
            final_verdict = "Moderate"
        else:
            final_verdict = "Weak"

        reasoning = (
            f"VentureMind scored '{question}' at {score}/100 after weighting demand most heavily, "
            f"then applying penalties for competition and execution risk. Demand reads as {market_demand.lower()} "
            f"because the research plan surfaced {len(market_observations)} market-oriented evidence steps and "
            f"{source_count} total sources. Competition is {competition.lower()} based on visible alternatives and "
            f"positioning pressure in the evidence. Risk is {risk.lower()} because the evaluator flagged "
            f"{len(evaluation.gaps)} unresolved gaps and {failed_steps} failed steps."
        )

        return {
            "score": score,
            "market_demand": market_demand,
            "competition": competition,
            "risk": risk,
            "final_verdict": final_verdict,
            "confidence": confidence,
            "reasoning": reasoning,
            "plan_summary": plan.plan_summary,
            "demand_score": demand_score,
            "competition_score": competition_score,
            "risk_score": risk_score,
            "why_this_decision": [
                f"Demand strength scored {demand_score}/100 after weighing market evidence volume and signal quality.",
                f"Competition pressure scored {competition_score}/100 based on visible alternatives and incumbent density.",
                f"Execution risk scored {risk_score}/100 because evaluator gaps and failed steps reduce certainty.",
            ],
            "decision_breakdown": {
                "demand_weight": 0.5,
                "competition_penalty_weight": 0.3,
                "risk_penalty_weight": 0.2,
                "demand_score": demand_score,
                "competition_score": competition_score,
                "risk_score": risk_score,
            },
        }

    @staticmethod
    def _combined_text(observations: list[ToolObservation]) -> str:
        return " ".join(
            " ".join(
                [
                    observation.objective,
                    observation.query,
                    observation.summary,
                    " ".join(observation.data_points),
                    " ".join(
                        f"{source.title} {source.snippet}"
                        for source in observation.sources
                    ),
                ]
            )
            for observation in observations
        ).lower()

    @staticmethod
    def _term_hits(text: str, terms: set[str]) -> int:
        return sum(text.count(term) for term in terms)

    @staticmethod
    def _label_from_score(score: int) -> str:
        if score >= 70:
            return "High"
        if score >= 40:
            return "Medium"
        return "Low"

    @staticmethod
    def _is_competitor_observation(observation: ToolObservation) -> bool:
        combined = f"{observation.objective} {observation.query}".lower()
        return any(token in combined for token in {"competitor", "competition", "alternative"})
