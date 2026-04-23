from __future__ import annotations

import json
from dataclasses import asdict

from core.models import AgentMessage, EvaluationReport, ResearchPlan, ToolObservation
from core.providers import LLMClient


class EvaluatorAgent:
    def __init__(self, llm: LLMClient, confidence_threshold: int) -> None:
        self.llm = llm
        self.confidence_threshold = confidence_threshold

    def evaluate(
        self,
        question: str,
        plan: ResearchPlan,
        observations: list[ToolObservation],
        correlation_id: str,
    ) -> AgentMessage:
        fallback = self._heuristic_evaluation(question, observations)
        system_prompt = (
            "You are the evaluator_agent in VentureMind AI. "
            "Judge whether the collected evidence is strong enough to produce a decision-grade startup validation report. "
            "Be strict about source quality, source diversity, and obvious evidence gaps."
        )
        user_prompt = (
            f"Startup idea:\n{question}\n\n"
            f"Plan summary:\n{plan.plan_summary}\n\n"
            "Observations:\n"
            f"{self._observations_digest(observations)}\n\n"
            "Return JSON with keys: ready_to_finalize, confidence, reasoning_summary, strengths, gaps, suggested_queries.\n"
            "If evidence is weak, set ready_to_finalize to false and produce 1 to 3 suggested follow-up queries."
        )

        try:
            payload = self.llm.complete_json(system_prompt, user_prompt, fallback=asdict(fallback))
        except Exception:
            payload = asdict(fallback)
        evaluation = self._build_evaluation(payload, fallback, observations)
        return AgentMessage(
            sender="evaluator_agent",
            recipient="orchestrator",
            message_type="evaluation_report",
            payload=asdict(evaluation),
            correlation_id=correlation_id,
        )

    def _build_evaluation(
        self,
        payload: dict,
        fallback: EvaluationReport,
        observations: list[ToolObservation],
    ) -> EvaluationReport:
        if not isinstance(payload, dict):
            return fallback

        strengths = payload.get("strengths")
        if not isinstance(strengths, list):
            strengths = fallback.strengths

        gaps = payload.get("gaps")
        if not isinstance(gaps, list):
            gaps = fallback.gaps

        suggested_queries = payload.get("suggested_queries")
        if not isinstance(suggested_queries, list):
            suggested_queries = fallback.suggested_queries

        failed_steps = any(observation.status != "completed" for observation in observations)
        source_count = sum(len(observation.sources) for observation in observations)
        payload_confidence = self._parse_confidence(payload.get("confidence"))
        use_fallback_confidence = payload_confidence is None or (
            payload_confidence <= 0 and fallback.confidence > 0 and source_count >= 4 and not failed_steps
        )
        confidence_value = fallback.confidence if use_fallback_confidence else payload_confidence

        ready_to_finalize = bool(payload.get("ready_to_finalize", fallback.ready_to_finalize))
        if use_fallback_confidence and fallback.ready_to_finalize and not failed_steps:
            ready_to_finalize = True
        if failed_steps or source_count < 3 or confidence_value < self.confidence_threshold:
            ready_to_finalize = False

        return EvaluationReport(
            ready_to_finalize=ready_to_finalize,
            confidence=max(0, min(100, confidence_value)),
            reasoning_summary=str(payload.get("reasoning_summary") or fallback.reasoning_summary),
            strengths=[str(item) for item in strengths][:4],
            gaps=[str(item) for item in gaps][:4],
            suggested_queries=[str(item) for item in suggested_queries][:3],
        )

    @staticmethod
    def _parse_confidence(value: object) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _heuristic_evaluation(
        self,
        question: str,
        observations: list[ToolObservation],
    ) -> EvaluationReport:
        source_count = sum(len(observation.sources) for observation in observations)
        unique_publishers = {
            source.source
            for observation in observations
            for source in observation.sources
        }
        failed_steps = sum(1 for observation in observations if observation.status != "completed")
        confidence = min(92, 42 + source_count * 6 + len(unique_publishers) * 4 - failed_steps * 10)
        ready = source_count >= 4 and len(unique_publishers) >= 2 and failed_steps == 0 and confidence >= self.confidence_threshold

        gaps = []
        if source_count < 4:
            gaps.append("The evidence base is still thin.")
        if len(unique_publishers) < 2:
            gaps.append("Publisher diversity is weak.")
        if failed_steps:
            gaps.append("One or more tool steps failed.")

        suggested_queries = []
        if not ready:
            suggested_queries = [
                f"{question} market demand startup benchmark",
                f"{question} competitors alternatives startup",
                f"{question} startup risks adoption latest",
            ]

        reasoning_summary = (
            "The evaluator is using source count, source diversity, and tool success rate "
            "to decide whether the startup idea is ready for a final validation verdict."
        )
        return EvaluationReport(
            ready_to_finalize=ready,
            confidence=max(0, min(100, confidence)),
            reasoning_summary=reasoning_summary,
            strengths=[
                f"Collected {source_count} total sources.",
                f"Observed {len(unique_publishers)} distinct publishers.",
            ],
            gaps=gaps,
            suggested_queries=suggested_queries,
        )

    @staticmethod
    def _observations_digest(observations: list[ToolObservation]) -> str:
        if not observations:
            return "No observations collected."

        digested = []
        for observation in observations[-6:]:
            digested.append(
                {
                    "step_id": observation.step_id,
                    "tool_name": observation.tool_name,
                    "query": observation.query,
                    "status": observation.status,
                    "summary": observation.summary,
                    "data_points": observation.data_points[:3],
                    "sources": [source.title for source in observation.sources[:3]],
                    "error": observation.error,
                }
            )
        return json.dumps(digested, indent=2)
