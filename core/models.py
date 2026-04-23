from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentMessage:
    sender: str
    recipient: str
    message_type: str
    payload: dict[str, Any]
    correlation_id: str
    timestamp: str = field(default_factory=utc_now)


@dataclass
class PlanStep:
    step_id: str
    objective: str
    tool_name: str
    query: str
    success_criteria: str


@dataclass
class ResearchPlan:
    use_case: str
    problem_statement: str
    target_users: list[str]
    why_it_matters: str
    plan_summary: str
    steps: list[PlanStep]


@dataclass
class SourceRecord:
    title: str
    url: str
    snippet: str
    source: str
    published_at: str = ""


@dataclass
class ToolObservation:
    step_id: str
    objective: str
    tool_name: str
    query: str
    status: str
    summary: str
    data_points: list[str]
    sources: list[SourceRecord]
    error: str | None = None


@dataclass
class EvaluationReport:
    ready_to_finalize: bool
    confidence: int
    reasoning_summary: str
    strengths: list[str]
    gaps: list[str]
    suggested_queries: list[str]


@dataclass
class MemoryHit:
    run_id: str
    created_at: str
    user_question: str
    summary: str
    confidence: int
    score: float


@dataclass
class FinalBrief:
    title: str
    executive_summary: str
    key_findings: list[str]
    recommended_actions: list[str]
    open_questions: list[str]
    startup_idea: str = ""
    market_analysis: str = ""
    competitor_analysis: str = ""
    swot: dict[str, list[str]] = field(
        default_factory=lambda: {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
        }
    )
    final_decision: dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceEvent:
    stage: str
    title: str
    details: str
    metadata: dict[str, Any]
    timestamp: str = field(default_factory=utc_now)


@dataclass
class ResearchRunResult:
    run_id: str
    use_case: str
    problem_statement: str
    target_users: list[str]
    why_it_matters: str
    user_question: str
    plan: ResearchPlan
    observations: list[ToolObservation]
    evaluation: EvaluationReport
    final_brief: FinalBrief
    final_markdown: str
    trace: list[TraceEvent]
    related_memories: list[MemoryHit]
    trace_path: str
    workflow_steps: list[str] = field(default_factory=list)
