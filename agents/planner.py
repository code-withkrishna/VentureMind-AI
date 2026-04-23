from __future__ import annotations

import json
from dataclasses import asdict

from core.config import PRODUCT_BRIEF
from core.models import AgentMessage, EvaluationReport, MemoryHit, PlanStep, ResearchPlan
from core.providers import LLMClient

ALLOWED_TOOLS = {"web_search", "news_search", "calculator"}


class PlannerAgent:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def create_plan(
        self,
        question: str,
        related_memories: list[MemoryHit],
        correlation_id: str,
        evaluation: EvaluationReport | None = None,
    ) -> AgentMessage:
        fallback_plan = self._fallback_plan(question, evaluation)
        system_prompt = (
            "You are the planner_agent inside VentureMind AI, a multi-agent startup validation system. "
            "Break the question into a small number of tool-driven steps. "
            "Choose only from web_search, news_search, or calculator. "
            "Keep the plan concise, explainable, and grounded in market, competitor, and feasibility evidence."
        )
        user_prompt = (
            f"Startup idea:\n{question}\n\n"
            f"Use case:\n{json.dumps(PRODUCT_BRIEF, indent=2)}\n\n"
            f"Relevant memory:\n{self._memory_digest(related_memories)}\n\n"
            f"Evaluator feedback:\n{self._evaluation_digest(evaluation)}\n\n"
            "Return JSON with keys: plan_summary, steps.\n"
            "Each step must include: step_id, objective, tool_name, query, success_criteria.\n"
            "Prefer 2 to 4 steps.\n"
            "Use news_search for recent market shifts and web_search for demand, competitor, or benchmark evidence.\n"
            "The ideal plan covers market demand, competitors or alternatives, and startup feasibility.\n"
            "If evaluator feedback exists, focus only on closing the identified gaps."
        )

        try:
            payload = self.llm.complete_json(system_prompt, user_prompt, fallback=asdict(fallback_plan))
        except Exception:
            payload = asdict(fallback_plan)
        plan = self._build_plan(payload, fallback_plan)
        return AgentMessage(
            sender="planner_agent",
            recipient="orchestrator",
            message_type="research_plan",
            payload=asdict(plan),
            correlation_id=correlation_id,
        )

    def _build_plan(self, payload: dict, fallback_plan: ResearchPlan) -> ResearchPlan:
        if not isinstance(payload, dict):
            return fallback_plan

        raw_steps = payload.get("steps")
        steps: list[PlanStep] = []
        if isinstance(raw_steps, list):
            for index, step in enumerate(raw_steps, start=1):
                if not isinstance(step, dict):
                    continue
                tool_name = str(step.get("tool_name") or "web_search").strip().lower()
                if tool_name not in ALLOWED_TOOLS:
                    tool_name = "web_search"
                query = str(step.get("query") or "").strip()
                if not query:
                    continue
                steps.append(
                    PlanStep(
                        step_id=str(step.get("step_id") or f"step_{index}"),
                        objective=str(step.get("objective") or "Collect stronger evidence."),
                        tool_name=tool_name,
                        query=query,
                        success_criteria=str(
                            step.get("success_criteria") or "Return credible, decision-useful evidence."
                        ),
                    )
                )

        if not steps:
            steps = fallback_plan.steps

        plan_summary = str(payload.get("plan_summary") or fallback_plan.plan_summary).strip()
        return ResearchPlan(
            use_case=PRODUCT_BRIEF["name"],
            problem_statement=PRODUCT_BRIEF["problem_statement"],
            target_users=list(PRODUCT_BRIEF["target_users"]),
            why_it_matters=PRODUCT_BRIEF["why_it_matters"],
            plan_summary=plan_summary,
            steps=steps[:4],
        )

    def _fallback_plan(
        self,
        question: str,
        evaluation: EvaluationReport | None = None,
    ) -> ResearchPlan:
        if evaluation is not None and evaluation.suggested_queries:
            steps = [
                PlanStep(
                    step_id=f"reflection_{index}",
                    objective="Close an evidence gap identified by the evaluator.",
                    tool_name="news_search" if "latest" in query.lower() or "recent" in query.lower() else "web_search",
                    query=query,
                    success_criteria="Return fresher or more decision-ready evidence.",
                )
                for index, query in enumerate(evaluation.suggested_queries[:3], start=1)
            ]
            plan_summary = "Refine the evidence base using the evaluator's follow-up questions."
        else:
            steps = [
                PlanStep(
                    step_id="step_1",
                    objective="Assess market demand and startup timing.",
                    tool_name="web_search",
                    query=f"{question} market demand startup trend",
                    success_criteria="Return evidence about demand, urgency, and market movement.",
                ),
                PlanStep(
                    step_id="step_2",
                    objective="Map competitors and substitutes.",
                    tool_name="web_search",
                    query=f"{question} competitors alternatives startup",
                    success_criteria="Return visible competitors, substitutes, or crowded categories.",
                ),
                PlanStep(
                    step_id="step_3",
                    objective="Check feasibility, risk, and recent market signals.",
                    tool_name="news_search",
                    query=f"{question} startup risks funding adoption latest",
                    success_criteria="Return practical risks, adoption signals, and recent developments.",
                ),
            ]
            plan_summary = "Validate demand, map competition, and test feasibility before issuing an investor-style verdict."

        return ResearchPlan(
            use_case=PRODUCT_BRIEF["name"],
            problem_statement=PRODUCT_BRIEF["problem_statement"],
            target_users=list(PRODUCT_BRIEF["target_users"]),
            why_it_matters=PRODUCT_BRIEF["why_it_matters"],
            plan_summary=plan_summary,
            steps=steps,
        )

    @staticmethod
    def _memory_digest(related_memories: list[MemoryHit]) -> str:
        if not related_memories:
            return "No relevant prior runs."
        lines = []
        for memory in related_memories[:3]:
            lines.append(
                f"- {memory.created_at}: {memory.user_question} "
                f"(confidence {memory.confidence}, similarity {memory.score:.2f})"
            )
        return "\n".join(lines)

    @staticmethod
    def _evaluation_digest(evaluation: EvaluationReport | None) -> str:
        if evaluation is None:
            return "No evaluator feedback yet."
        return json.dumps(asdict(evaluation), indent=2)
