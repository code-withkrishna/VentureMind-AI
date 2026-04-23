from __future__ import annotations

import json
from dataclasses import asdict

from core.models import AgentMessage, EvaluationReport, FinalBrief, MemoryHit, ResearchPlan, ToolObservation
from core.providers import LLMClient


class ReportAgent:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def generate(
        self,
        question: str,
        plan: ResearchPlan,
        observations: list[ToolObservation],
        evaluation: EvaluationReport,
        decision: dict[str, object],
        related_memories: list[MemoryHit],
        workflow_steps: list[str],
        correlation_id: str,
    ) -> AgentMessage:
        fallback = self._fallback_brief(
            question,
            observations,
            evaluation,
            decision,
        )
        system_prompt = (
            "You are the report_agent inside VentureMind AI, a multi-agent startup validation system. "
            "Convert startup research into a crisp investor-style decision artifact. "
            "Use only the supplied evidence, keep the output structured, avoid hype, and do not fabricate numbers."
        )
        user_prompt = (
            f"Startup idea:\n{question}\n\n"
            f"Use case:\n{plan.use_case}\n"
            f"Problem statement:\n{plan.problem_statement}\n"
            f"Target users:\n{', '.join(plan.target_users)}\n"
            f"Why it matters:\n{plan.why_it_matters}\n\n"
            f"Plan summary:\n{plan.plan_summary}\n\n"
            f"Decision:\n{json.dumps(decision, indent=2)}\n\n"
            f"Evaluation:\n{json.dumps(asdict(evaluation), indent=2)}\n\n"
            f"Workflow steps:\n{json.dumps(workflow_steps, indent=2)}\n\n"
            f"Observations:\n{self._observation_digest(observations)}\n\n"
            f"Related memory:\n{self._memory_digest(related_memories)}\n\n"
            "Return JSON with keys: title, executive_summary, key_findings, recommended_actions, open_questions, "
            "market_analysis, competitor_analysis, swot. "
            "The swot object must contain strengths, weaknesses, opportunities, threats as arrays of short strings."
        )

        try:
            payload = self.llm.complete_json(system_prompt, user_prompt, fallback=asdict(fallback))
        except Exception:
            payload = asdict(fallback)
        brief = self._build_brief(payload, fallback, question, decision)
        return AgentMessage(
            sender="report_agent",
            recipient="orchestrator",
            message_type="startup_report",
            payload=asdict(brief),
            correlation_id=correlation_id,
        )

    def _build_brief(
        self,
        payload: dict,
        fallback: FinalBrief,
        question: str,
        decision: dict[str, object],
    ) -> FinalBrief:
        if not isinstance(payload, dict):
            return fallback

        key_findings = payload.get("key_findings")
        if not isinstance(key_findings, list):
            key_findings = fallback.key_findings

        recommended_actions = payload.get("recommended_actions")
        if not isinstance(recommended_actions, list):
            recommended_actions = fallback.recommended_actions

        open_questions = payload.get("open_questions")
        if not isinstance(open_questions, list):
            open_questions = fallback.open_questions

        swot = payload.get("swot")
        if not isinstance(swot, dict):
            swot = fallback.swot

        return FinalBrief(
            title=str(payload.get("title") or fallback.title),
            executive_summary=str(payload.get("executive_summary") or fallback.executive_summary),
            key_findings=self._normalize_string_list(key_findings, fallback.key_findings, limit=5),
            recommended_actions=self._normalize_string_list(
                recommended_actions,
                fallback.recommended_actions,
                limit=5,
            ),
            open_questions=self._normalize_string_list(open_questions, fallback.open_questions, limit=4),
            startup_idea=question,
            market_analysis=self._normalize_text_block(
                payload.get("market_analysis"),
                fallback.market_analysis,
            ),
            competitor_analysis=self._normalize_text_block(
                payload.get("competitor_analysis"),
                fallback.competitor_analysis,
            ),
            swot={
                "strengths": self._normalize_string_list(swot.get("strengths", []), fallback.swot.get("strengths", [])),
                "weaknesses": self._normalize_string_list(swot.get("weaknesses", []), fallback.swot.get("weaknesses", [])),
                "opportunities": self._normalize_string_list(
                    swot.get("opportunities", []),
                    fallback.swot.get("opportunities", []),
                ),
                "threats": self._normalize_string_list(swot.get("threats", []), fallback.swot.get("threats", [])),
            },
            final_decision={**decision},
        )

    @staticmethod
    def _fallback_brief(
        question: str,
        observations: list[ToolObservation],
        evaluation: EvaluationReport,
        decision: dict[str, object],
    ) -> FinalBrief:
        market_points = []
        competitor_points = []
        for observation in observations:
            if any(token in f"{observation.objective} {observation.query}".lower() for token in {"competitor", "alternative", "competition"}):
                competitor_points.extend(observation.data_points[:2])
            else:
                market_points.extend(observation.data_points[:2])

        market_analysis = " ".join(market_points[:2]).strip() or (
            "Market demand signals are still emerging, so the business case depends on stronger founder interviews and sharper problem validation."
        )
        competitor_analysis = " ".join(competitor_points[:2]).strip() or (
            "The competitive landscape is not fully mapped yet, but the product will need clearer differentiation against existing alternatives."
        )

        strengths = list(evaluation.strengths[:2]) or ["The system collected enough evidence to form an initial decision."]
        weaknesses = list(evaluation.gaps[:2]) or ["The opportunity still needs deeper validation on customer willingness to pay."]
        opportunities = [
            "A sharper niche positioning could increase credibility and speed up early validation.",
            "Founder interviews can quickly tighten the problem statement and buying trigger.",
        ]
        threats = [
            "Crowded startup tooling can make differentiation difficult without a narrow wedge.",
            "Weak evidence depth can lead to false positives if the market is not validated directly.",
        ]

        score = int(decision.get("score", 0))
        verdict = str(decision.get("final_verdict") or "Moderate")
        confidence = int(decision.get("confidence", 0))

        return FinalBrief(
            title=f"VentureMind AI Report: {question}",
            executive_summary=(
                f"VentureMind AI rated this startup idea {score}/100 with a {verdict.lower()} verdict "
                f"at {confidence}% confidence. The opportunity is shaped by demand validation, competitive pressure, and execution risk."
            ),
            key_findings=[
                market_analysis,
                competitor_analysis,
                str(decision.get("reasoning") or "Decision logic combined demand, competition, and risk."),
            ],
            recommended_actions=[
                "Interview target users before building broad product scope.",
                "Define one narrow wedge that is visibly better than current alternatives.",
                "Test willingness to pay with a lightweight validation offer or concierge MVP.",
            ],
            open_questions=[
                "Who is the first narrow customer segment that feels this pain most urgently?",
                "What measurable result would make the product clearly better than current alternatives?",
            ],
            startup_idea=question,
            market_analysis=market_analysis,
            competitor_analysis=competitor_analysis,
            swot={
                "strengths": strengths,
                "weaknesses": weaknesses,
                "opportunities": opportunities,
                "threats": threats,
            },
            final_decision={**decision},
        )

    @staticmethod
    def _observation_digest(observations: list[ToolObservation]) -> str:
        digested = []
        for observation in observations[-8:]:
            digested.append(
                {
                    "objective": observation.objective,
                    "query": observation.query,
                    "summary": observation.summary,
                    "data_points": observation.data_points[:3],
                    "sources": [source.title for source in observation.sources[:3]],
                    "status": observation.status,
                }
            )
        return json.dumps(digested, indent=2)

    @staticmethod
    def _memory_digest(related_memories: list[MemoryHit]) -> str:
        if not related_memories:
            return "No related historical memory."
        return json.dumps(
            [
                {
                    "question": memory.user_question,
                    "summary": memory.summary,
                    "score": round(memory.score, 2),
                }
                for memory in related_memories[:3]
            ],
            indent=2,
        )

    @staticmethod
    def _normalize_string_list(
        raw_items: object,
        fallback_items: list[str],
        *,
        limit: int = 4,
    ) -> list[str]:
        if not isinstance(raw_items, list):
            raw_items = fallback_items

        normalized = []
        for item in raw_items:
            text = ReportAgent._normalize_inline_value(item)
            if text:
                normalized.append(text)
        return normalized[:limit] or list(fallback_items)[:limit]

    @staticmethod
    def _normalize_text_block(value: object, fallback: str) -> str:
        if isinstance(value, str):
            text = value.strip()
            return text or fallback

        if isinstance(value, list):
            lines = [
                f"- {text}"
                for text in (ReportAgent._normalize_inline_value(item) for item in value)
                if text
            ]
            return "\n".join(lines) or fallback

        if isinstance(value, dict):
            lines = []
            for key, item in value.items():
                text = ReportAgent._normalize_inline_value(item)
                if not text:
                    continue
                label = str(key).replace("_", " ").strip().title()
                lines.append(f"- {label}: {text}")
            return "\n".join(lines) or fallback

        if value is None:
            return fallback
        return str(value)

    @staticmethod
    def _normalize_inline_value(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            items = [
                ReportAgent._normalize_inline_value(item)
                for item in value
            ]
            return ", ".join(item for item in items if item)
        if isinstance(value, dict):
            parts = []
            for key, item in value.items():
                text = ReportAgent._normalize_inline_value(item)
                if text:
                    label = str(key).replace("_", " ").strip()
                    parts.append(f"{label}: {text}")
            return "; ".join(parts)
        return str(value).strip()
