from __future__ import annotations

from dataclasses import asdict

from core.config import Settings
from core.models import AgentMessage, PlanStep, SourceRecord, ToolObservation
from tools.search import SerperSearchTool


class CompetitorAgent:
    def __init__(self, settings: Settings) -> None:
        self.search_tool = SerperSearchTool(settings)

    def execute(self, message: AgentMessage) -> AgentMessage:
        step = self._build_step(message.payload.get("step", {}))
        try:
            sources = self.search_tool.search(step.query, mode=step.tool_name)
            observation = ToolObservation(
                step_id=step.step_id,
                objective=step.objective,
                tool_name=step.tool_name,
                query=step.query,
                status="completed",
                summary=self._summarize_sources(step.query, sources),
                data_points=self._extract_data_points(sources),
                sources=sources,
            )
        except Exception as exc:
            observation = ToolObservation(
                step_id=step.step_id,
                objective=step.objective,
                tool_name=step.tool_name,
                query=step.query,
                status="failed",
                summary=f"Competitor analysis failed for `{step.query}`.",
                data_points=[],
                sources=[],
                error=str(exc),
            )

        return AgentMessage(
            sender="competitor_agent",
            recipient="orchestrator",
            message_type="competitor_observation",
            payload=asdict(observation),
            correlation_id=message.correlation_id,
        )

    @staticmethod
    def _build_step(payload: dict) -> PlanStep:
        return PlanStep(
            step_id=str(payload.get("step_id") or "step_unknown"),
            objective=str(payload.get("objective") or "Analyze competitors."),
            tool_name=str(payload.get("tool_name") or "web_search"),
            query=str(payload.get("query") or "").strip(),
            success_criteria=str(payload.get("success_criteria") or "Return competitor evidence."),
        )

    @staticmethod
    def _summarize_sources(query: str, sources: list[SourceRecord]) -> str:
        if not sources:
            return f"No competitor sources were returned for `{query}`."
        return (
            f"Collected {len(sources)} competitor and alternative signals for `{query}` to map positioning pressure."
        )

    @staticmethod
    def _extract_data_points(sources: list[SourceRecord]) -> list[str]:
        points = []
        for source in sources[:4]:
            title = source.title.strip() or source.url
            snippet = source.snippet.strip()
            if snippet:
                points.append(f"{title}: {snippet}")
            else:
                points.append(title)
        return points
