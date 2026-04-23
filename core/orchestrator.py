from __future__ import annotations

import uuid
from dataclasses import asdict

from agents.competitor_agent import CompetitorAgent
from agents.decision_agent import DecisionAgent
from agents.evaluator import EvaluatorAgent
from agents.market_agent import MarketAgent
from agents.planner import PlannerAgent
from agents.report_agent import ReportAgent
from agents.tool_agent import ToolAgent
from core.config import Settings
from core.logger import TraceRecorder, configure_logging
from core.models import (
    AgentMessage,
    EvaluationReport,
    FinalBrief,
    MemoryHit,
    PlanStep,
    ResearchPlan,
    ResearchRunResult,
    SourceRecord,
    ToolObservation,
)
from core.providers import LLMClient
from memory.store import MemoryStore

WORKFLOW_STEPS = [
    "Planning...",
    "Running Market Research Agent...",
    "Analyzing Competitors...",
    "Evaluating Feasibility...",
    "Generating Final Report...",
]


class AgentathonOrchestrator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.logger = configure_logging(self.settings)
        self.llm = LLMClient(self.settings)
        self.memory = MemoryStore(self.settings)
        self.planner = PlannerAgent(self.llm)
        self.market_agent = MarketAgent(self.settings)
        self.competitor_agent = CompetitorAgent(self.settings)
        self.tool_agent = ToolAgent(self.settings)
        self.evaluator = EvaluatorAgent(self.llm, self.settings.confidence_threshold)
        self.decision_agent = DecisionAgent()
        self.report_agent = ReportAgent(self.llm)

    def run(self, user_question: str, event_callback=None) -> ResearchRunResult:
        question = user_question.strip()
        if not question:
            raise ValueError("A startup idea is required.")

        run_id = uuid.uuid4().hex[:12]
        trace = TraceRecorder(self.settings, run_id, self.logger, callback=event_callback)
        workflow_steps = list(WORKFLOW_STEPS)

        trace.record("intake", "Startup idea accepted", question, {"idea": question})

        related_memories = self.memory.find_related_runs(question, limit=3)
        trace.record(
            "memory",
            "Loaded long-term memory",
            f"Found {len(related_memories)} relevant prior runs.",
            {"memory_hits": [asdict(item) for item in related_memories]},
        )

        plan_message = self.planner.create_plan(question, related_memories, run_id)
        plan = self._hydrate_plan(plan_message.payload)
        trace.record(
            "planning",
            WORKFLOW_STEPS[0],
            plan.plan_summary,
            {"agent": "planner_agent", "steps": [asdict(step) for step in plan.steps]},
        )

        observations: list[ToolObservation] = []
        last_evaluation: EvaluationReport | None = None
        executed_queries: set[str] = set()

        for iteration in range(self.settings.max_reasoning_loops + 1):
            new_steps = [step for step in plan.steps if step.query.lower() not in executed_queries]
            if not new_steps:
                trace.record(
                    "planning",
                    "Planning complete",
                    "The planner proposed only queries that were already executed.",
                    {"agent": "planner_agent"},
                )
                break

            for step in new_steps:
                executed_queries.add(step.query.lower())
                stage, title, agent_name = self._step_descriptor(step)
                trace.record(
                    stage,
                    title,
                    step.query,
                    {"agent": agent_name, "step_id": step.step_id, "objective": step.objective},
                )
                tool_message = self._execute_step(step, run_id)
                observation = self._hydrate_observation(tool_message.payload)
                observations.append(observation)
                trace.record(
                    stage,
                    f"{agent_name} captured evidence",
                    observation.summary,
                    {
                        "status": observation.status,
                        "sources": [asdict(source) for source in observation.sources[:3]],
                        "error": observation.error,
                    },
                )

            evaluation_message = self.evaluator.evaluate(question, plan, observations, run_id)
            last_evaluation = self._hydrate_evaluation(evaluation_message.payload)
            trace.record(
                "evaluation",
                WORKFLOW_STEPS[3],
                last_evaluation.reasoning_summary,
                {
                    "agent": "evaluator_agent",
                    "confidence": last_evaluation.confidence,
                    "ready_to_finalize": last_evaluation.ready_to_finalize,
                    "gaps": last_evaluation.gaps,
                    "suggested_queries": last_evaluation.suggested_queries,
                },
            )

            if last_evaluation.ready_to_finalize:
                break
            if iteration >= self.settings.max_reasoning_loops:
                trace.record(
                    "evaluation",
                    "Reflection budget exhausted",
                    "The orchestrator reached the maximum reasoning depth and will produce the best available startup decision.",
                    {"agent": "evaluator_agent"},
                )
                break

            plan_message = self.planner.create_plan(
                question,
                related_memories,
                run_id,
                evaluation=last_evaluation,
            )
            plan = self._hydrate_plan(plan_message.payload)
            trace.record(
                "planning",
                f"Planning refinement loop {iteration + 1}",
                plan.plan_summary,
                {"agent": "planner_agent", "steps": [asdict(step) for step in plan.steps]},
            )

        if last_evaluation is None:
            last_evaluation = EvaluationReport(
                ready_to_finalize=False,
                confidence=35,
                reasoning_summary="No usable evidence was collected, so the startup decision is operating with low confidence.",
                strengths=[],
                gaps=["No successful tool observations were recorded."],
                suggested_queries=[],
            )

        decision_message = self.decision_agent.decide(
            question,
            plan,
            observations,
            last_evaluation,
            run_id,
        )
        final_decision = self._hydrate_decision(decision_message.payload)
        trace.record(
            "decision",
            "Computing final decision...",
            str(final_decision.get("reasoning") or "Decision score generated."),
            {"agent": "decision_agent", "final_decision": final_decision},
        )

        report_message = self.report_agent.generate(
            question,
            plan,
            observations,
            last_evaluation,
            final_decision,
            related_memories,
            workflow_steps,
            run_id,
        )
        final_brief = self._hydrate_final_brief(report_message.payload, question, final_decision)
        final_markdown = self._render_markdown(final_brief, last_evaluation, observations)
        trace.record(
            "report",
            WORKFLOW_STEPS[4],
            final_brief.title,
            {
                "agent": "report_agent",
                "verdict": final_brief.final_decision.get("final_verdict"),
                "score": final_brief.final_decision.get("score"),
            },
        )
        trace.record(
            "storage",
            "Persisting trace and memory",
            "Saving the run to long-term memory for retrieval in future sessions.",
            {"trace_path": str(trace.output_path)},
        )

        trace_path = str(trace.output_path)
        result = ResearchRunResult(
            run_id=run_id,
            use_case=plan.use_case,
            problem_statement=plan.problem_statement,
            target_users=plan.target_users,
            why_it_matters=plan.why_it_matters,
            user_question=question,
            plan=plan,
            observations=observations,
            evaluation=last_evaluation,
            final_brief=final_brief,
            final_markdown=final_markdown,
            trace=list(trace.events),
            related_memories=related_memories,
            trace_path=trace_path,
            workflow_steps=workflow_steps,
        )
        trace.save()
        self.memory.save_run(result)
        result.trace = list(trace.events)
        result.trace_path = trace_path
        return result

    def _execute_step(self, step: PlanStep, correlation_id: str) -> AgentMessage:
        message = AgentMessage(
            sender="orchestrator",
            recipient="agent",
            message_type="tool_request",
            payload={"step": asdict(step)},
            correlation_id=correlation_id,
        )
        if step.tool_name == "calculator":
            return self.tool_agent.execute(message)
        if self._is_competitor_step(step):
            return self.competitor_agent.execute(message)
        return self.market_agent.execute(message)

    @staticmethod
    def _step_descriptor(step: PlanStep) -> tuple[str, str, str]:
        if step.tool_name == "calculator":
            return ("market_research", "Running Market Research Agent...", "market_agent")
        if AgentathonOrchestrator._is_competitor_step(step):
            return ("competitor_analysis", WORKFLOW_STEPS[2], "competitor_agent")
        return ("market_research", WORKFLOW_STEPS[1], "market_agent")

    @staticmethod
    def _is_competitor_step(step: PlanStep) -> bool:
        combined = f"{step.objective} {step.query}".lower()
        return any(token in combined for token in {"competitor", "competition", "alternative"})

    @staticmethod
    def _hydrate_plan(payload: dict) -> ResearchPlan:
        steps = [
            PlanStep(
                step_id=str(step.get("step_id") or "step_unknown"),
                objective=str(step.get("objective") or "Collect evidence."),
                tool_name=str(step.get("tool_name") or "web_search"),
                query=str(step.get("query") or ""),
                success_criteria=str(step.get("success_criteria") or "Collect evidence."),
            )
            for step in payload.get("steps", [])
            if isinstance(step, dict)
        ]
        return ResearchPlan(
            use_case=str(payload.get("use_case") or "VentureMind AI"),
            problem_statement=str(payload.get("problem_statement") or ""),
            target_users=[str(user) for user in payload.get("target_users", [])],
            why_it_matters=str(payload.get("why_it_matters") or ""),
            plan_summary=str(payload.get("plan_summary") or ""),
            steps=steps,
        )

    @staticmethod
    def _hydrate_observation(payload: dict) -> ToolObservation:
        sources = [
            SourceRecord(
                title=str(source.get("title") or "Untitled result"),
                url=str(source.get("url") or ""),
                snippet=str(source.get("snippet") or ""),
                source=str(source.get("source") or ""),
                published_at=str(source.get("published_at") or ""),
            )
            for source in payload.get("sources", [])
            if isinstance(source, dict)
        ]
        return ToolObservation(
            step_id=str(payload.get("step_id") or "step_unknown"),
            objective=str(payload.get("objective") or ""),
            tool_name=str(payload.get("tool_name") or ""),
            query=str(payload.get("query") or ""),
            status=str(payload.get("status") or "failed"),
            summary=str(payload.get("summary") or ""),
            data_points=[str(item) for item in payload.get("data_points", [])],
            sources=sources,
            error=str(payload.get("error")) if payload.get("error") else None,
        )

    @staticmethod
    def _hydrate_evaluation(payload: dict) -> EvaluationReport:
        try:
            confidence = int(payload.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0
        return EvaluationReport(
            ready_to_finalize=bool(payload.get("ready_to_finalize")),
            confidence=confidence,
            reasoning_summary=str(payload.get("reasoning_summary") or ""),
            strengths=[str(item) for item in payload.get("strengths", [])],
            gaps=[str(item) for item in payload.get("gaps", [])],
            suggested_queries=[str(item) for item in payload.get("suggested_queries", [])],
        )

    @staticmethod
    def _hydrate_decision(payload: dict) -> dict[str, object]:
        if not isinstance(payload, dict):
            return {
                "score": 0,
                "market_demand": "Low",
                "competition": "Medium",
                "risk": "High",
                "final_verdict": "Weak",
                "confidence": 0,
                "reasoning": "No decision payload was available.",
            }
        return {
            "score": int(payload.get("score", 0)),
            "market_demand": str(payload.get("market_demand") or "Low"),
            "competition": str(payload.get("competition") or "Medium"),
            "risk": str(payload.get("risk") or "High"),
            "final_verdict": str(payload.get("final_verdict") or "Weak"),
            "confidence": int(payload.get("confidence", 0)),
            "reasoning": str(payload.get("reasoning") or ""),
        }

    @staticmethod
    def _hydrate_final_brief(
        payload: dict,
        question: str,
        final_decision: dict[str, object],
    ) -> FinalBrief:
        if not isinstance(payload, dict):
            return FinalBrief(
                title=f"VentureMind AI Report: {question}",
                executive_summary="The system generated a fallback report because the final report payload was unavailable.",
                key_findings=[],
                recommended_actions=[],
                open_questions=[],
                startup_idea=question,
                market_analysis="Market analysis unavailable.",
                competitor_analysis="Competitor analysis unavailable.",
                swot={
                    "strengths": [],
                    "weaknesses": [],
                    "opportunities": [],
                    "threats": [],
                },
                final_decision=final_decision,
            )

        swot = payload.get("swot")
        if not isinstance(swot, dict):
            swot = {
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "threats": [],
            }

        return FinalBrief(
            title=str(payload.get("title") or f"VentureMind AI Report: {question}"),
            executive_summary=str(payload.get("executive_summary") or ""),
            key_findings=[str(item) for item in payload.get("key_findings", [])][:5],
            recommended_actions=[str(item) for item in payload.get("recommended_actions", [])][:5],
            open_questions=[str(item) for item in payload.get("open_questions", [])][:4],
            startup_idea=str(payload.get("startup_idea") or question),
            market_analysis=str(payload.get("market_analysis") or ""),
            competitor_analysis=str(payload.get("competitor_analysis") or ""),
            swot={
                "strengths": [str(item) for item in swot.get("strengths", [])][:4],
                "weaknesses": [str(item) for item in swot.get("weaknesses", [])][:4],
                "opportunities": [str(item) for item in swot.get("opportunities", [])][:4],
                "threats": [str(item) for item in swot.get("threats", [])][:4],
            },
            final_decision=payload.get("final_decision") if isinstance(payload.get("final_decision"), dict) else final_decision,
        )

    @staticmethod
    def _render_markdown(
        brief: FinalBrief,
        evaluation: EvaluationReport,
        observations: list[ToolObservation],
    ) -> str:
        sources = AgentathonOrchestrator._unique_sources(observations)
        source_lines = []
        for source in sources:
            title = source.title.strip() or source.url
            if source.url:
                suffix = f" - {source.source}" if source.source else ""
                if source.published_at:
                    suffix += f" ({source.published_at})"
                source_lines.append(f"- [{title}]({source.url}){suffix}")
            else:
                source_lines.append(f"- {title}")

        strengths = "\n".join(f"- {item}" for item in brief.swot.get("strengths", [])) or "- No strengths identified yet."
        weaknesses = "\n".join(f"- {item}" for item in brief.swot.get("weaknesses", [])) or "- No weaknesses identified yet."
        opportunities = "\n".join(f"- {item}" for item in brief.swot.get("opportunities", [])) or "- No opportunities identified yet."
        threats = "\n".join(f"- {item}" for item in brief.swot.get("threats", [])) or "- No threats identified yet."
        findings = "\n".join(f"- {item}" for item in brief.key_findings) or "- Evidence was limited."
        actions = "\n".join(f"- {item}" for item in brief.recommended_actions) or "- No follow-up actions were generated."
        open_questions = "\n".join(f"- {item}" for item in brief.open_questions) or "- No open questions were recorded."
        sources_block = "\n".join(source_lines) or "- No external sources were captured."
        decision = brief.final_decision

        return (
            f"# {brief.title}\n\n"
            f"**Startup Idea:** {brief.startup_idea}\n\n"
            "## VentureMind Verdict\n\n"
            f"- Score: {decision.get('score', 0)}/100\n"
            f"- Market Demand: {decision.get('market_demand', 'Low')}\n"
            f"- Competition: {decision.get('competition', 'Medium')}\n"
            f"- Risk: {decision.get('risk', 'High')}\n"
            f"- Verdict: {decision.get('final_verdict', 'Weak')}\n"
            f"- Confidence: {decision.get('confidence', 0)}%\n\n"
            "## Executive Summary\n\n"
            f"{brief.executive_summary}\n\n"
            "## Market Analysis\n\n"
            f"{brief.market_analysis}\n\n"
            "## Competitor Analysis\n\n"
            f"{brief.competitor_analysis}\n\n"
            "## SWOT Analysis\n\n"
            "### Strengths\n"
            f"{strengths}\n\n"
            "### Weaknesses\n"
            f"{weaknesses}\n\n"
            "### Opportunities\n"
            f"{opportunities}\n\n"
            "### Threats\n"
            f"{threats}\n\n"
            "## Key Findings\n\n"
            f"{findings}\n\n"
            "## Recommended Actions\n\n"
            f"{actions}\n\n"
            "## Evaluator Signals\n\n"
            f"- Confidence gate: {evaluation.confidence}/100\n"
            f"- Reasoning: {evaluation.reasoning_summary}\n\n"
            "## Open Questions\n\n"
            f"{open_questions}\n\n"
            "## Sources\n\n"
            f"{sources_block}\n"
        )

    @staticmethod
    def _unique_sources(observations: list[ToolObservation]) -> list[SourceRecord]:
        seen: dict[str, SourceRecord] = {}
        for observation in observations:
            for source in observation.sources:
                key = source.url or source.title
                if key not in seen:
                    seen[key] = source
        return list(seen.values())[:12]
