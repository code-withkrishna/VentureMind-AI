from __future__ import annotations

from dataclasses import asdict

from core.config import Settings
from core.models import AgentMessage, PlanStep, SourceRecord, ToolObservation
from tools.search import SerperSearchTool


class MarketAgent:
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
                summary=f"Market research failed for `{step.query}`.",
                data_points=[],
                sources=[],
                error=str(exc),
            )

        return AgentMessage(
            sender="market_agent",
            recipient="orchestrator",
            message_type="market_observation",
            payload=asdict(observation),
            correlation_id=message.correlation_id,
        )

    @staticmethod
    def _build_step(payload: dict) -> PlanStep:
        return PlanStep(
            step_id=str(payload.get("step_id") or "step_unknown"),
            objective=str(payload.get("objective") or "Collect market evidence."),
            tool_name=str(payload.get("tool_name") or "web_search"),
            query=str(payload.get("query") or "").strip(),
            success_criteria=str(payload.get("success_criteria") or "Return market evidence."),
        )

    @staticmethod
    def _summarize_sources(query: str, sources: list[SourceRecord]) -> str:
        if not sources:
            return f"No market sources were returned for `{query}`."
        return (
            f"Collected {len(sources)} market signals for `{query}` with emphasis on demand, timing, and startup viability."
        )

    @staticmethod
    def _extract_data_points(sources: list[SourceRecord]) -> list[str]:
        points = []
        for source in sources[:4]:
            snippet = source.snippet.strip()
            if snippet:
                points.append(f"{source.title}: {snippet}")
            else:
                points.append(source.title)
        return points
