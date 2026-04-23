from __future__ import annotations

from dataclasses import replace
from html import escape
import re
import time
from typing import Any

import streamlit as st

from core.config import PRODUCT_BRIEF, Settings
from core.models import ResearchRunResult, ToolObservation, TraceEvent
from core.orchestrator import AgentathonOrchestrator, WORKFLOW_STEPS
from ui.rendering import analysis_stepper_html
from utils.report_generator import generate_pdf_report
from utils.scenario_engine import build_investor_scenarios

EXAMPLE_PROMPTS = [
    "AI startup that helps college students choose careers using mentor calls and placement data.",
    "Fintech startup that automates invoice collections for SMBs in India.",
    "Healthcare startup that reduces clinic admin workload with voice-to-workflow AI.",
    "E-commerce tool that helps D2C brands predict stockouts and demand shifts.",
]

STAGE_PROGRESS = {
    "intake": 0.05,
    "memory": 0.12,
    "planning": 0.28,
    "market_research": 0.48,
    "competitor_analysis": 0.64,
    "evaluation": 0.78,
    "decision": 0.9,
    "report": 0.96,
    "storage": 1.0,
}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        :root {
            --bg-ink: #08111d;
            --ink: #eaf2fb;
            --muted: #9db0c7;
            --accent: #ff9f43;
            --cyan: #7dd3fc;
            --panel: rgba(9, 17, 31, 0.76);
            --panel-border: rgba(157, 176, 199, 0.18);
        }

        html, body, [class*="css"] {
            font-family: "IBM Plex Sans", sans-serif;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top left, rgba(255, 159, 67, 0.12), transparent 28%),
                radial-gradient(circle at top right, rgba(125, 211, 252, 0.12), transparent 24%),
                linear-gradient(180deg, #07101c 0%, #0d1e31 48%, #08111d 100%);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        h1, h2, h3 {
            font-family: "Space Grotesk", sans-serif;
            letter-spacing: -0.03em;
        }

        .hero-shell {
            padding: 1.8rem;
            border-radius: 28px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background:
                radial-gradient(circle at top right, rgba(255, 159, 67, 0.18), transparent 24%),
                linear-gradient(135deg, rgba(8, 17, 29, 0.94), rgba(17, 37, 57, 0.98));
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.28);
            margin-bottom: 0.8rem;
        }

        .hero-grid {
            display: grid;
            grid-template-columns: 1.35fr 0.65fr;
            gap: 1.2rem;
            align-items: start;
        }

        .hero-kicker {
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }

        .hero-title {
            color: white;
            font-size: 3rem;
            line-height: 1;
            margin: 0 0 0.5rem 0;
        }

        .hero-subtitle {
            color: #dce9f5;
            font-size: 1.18rem;
            margin: 0 0 0.55rem 0;
        }

        .hero-copy {
            color: #c8d8e8;
            line-height: 1.72;
            max-width: 860px;
            margin: 0;
        }

        .chip-row {
            display: flex;
            gap: 0.55rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }

        .hero-chip {
            padding: 0.45rem 0.72rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #dce9f5;
            font-size: 0.88rem;
            font-weight: 600;
        }

        .hero-stat {
            padding: 0.95rem 1rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 0.8rem;
        }

        .hero-stat-label {
            color: var(--muted);
            font-size: 0.75rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }

        .hero-stat-value {
            color: white;
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .hero-stat-copy {
            color: #c8d8e8;
            line-height: 1.55;
            font-size: 0.92rem;
            margin: 0;
        }

        .section-eyebrow {
            color: var(--accent);
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }

        .section-title {
            color: white;
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.55rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .section-copy {
            color: #c8d8e8;
            line-height: 1.6;
            margin-bottom: 0;
        }

        .glass-card {
            padding: 1rem 1.05rem;
            border-radius: 20px;
            border: 1px solid var(--panel-border);
            background: var(--panel);
            backdrop-filter: blur(12px);
            margin-bottom: 0.85rem;
        }

        .micro-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 0.9rem;
        }

        .micro-card {
            padding: 0.95rem;
            border-radius: 18px;
            background: rgba(11, 26, 42, 0.92);
            border: 1px solid var(--panel-border);
        }

        .micro-card h4 {
            color: white;
            margin: 0 0 0.3rem 0;
            font-size: 1rem;
        }

        .micro-card p {
            color: #c8d8e8;
            margin: 0;
            line-height: 1.6;
            font-size: 0.93rem;
        }

        .input-note {
            color: #c8d8e8;
            line-height: 1.65;
            font-size: 0.95rem;
        }

        .execution-status {
            padding: 0.8rem 0.95rem;
            border-radius: 14px;
            background: rgba(255, 159, 67, 0.12);
            border: 1px solid rgba(255, 159, 67, 0.18);
            color: #ffd7ad;
            margin: 0.7rem 0 0.8rem 0;
            font-weight: 600;
        }

        .trace-card {
            padding: 0.9rem 1rem;
            border-radius: 16px;
            background: rgba(11, 26, 42, 0.92);
            border: 1px solid var(--panel-border);
            margin-bottom: 0.65rem;
        }

        .trace-stage {
            color: var(--muted);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.2rem;
        }

        .trace-title {
            color: white;
            font-weight: 600;
            margin: 0;
        }

        .trace-copy {
            color: #dce9f5;
            margin: 0.25rem 0 0 0;
            line-height: 1.55;
        }

        .reasoning-callout {
            padding: 0.95rem 1rem;
            border-radius: 16px;
            background: rgba(125, 211, 252, 0.10);
            border: 1px solid rgba(125, 211, 252, 0.18);
            color: #dce9f5;
            line-height: 1.6;
            margin-bottom: 0.8rem;
        }

        .empty-state {
            padding: 1.2rem 1.25rem;
            border-radius: 20px;
            border: 1px dashed rgba(157, 176, 199, 0.24);
            background: rgba(9, 17, 31, 0.46);
            color: #c8d8e8;
            line-height: 1.7;
        }

        div[data-testid="metric-container"] {
            background: rgba(9, 17, 31, 0.74);
            border: 1px solid rgba(157, 176, 199, 0.18);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            box-shadow: none;
        }

        div[data-testid="metric-container"] label {
            color: #9db0c7;
        }

        div[data-testid="stForm"] {
            border: 1px solid rgba(157, 176, 199, 0.18);
            border-radius: 20px;
            padding: 1rem 1rem 0.6rem 1rem;
            background: rgba(9, 17, 31, 0.76);
        }

        div[data-testid="stForm"] textarea {
            background: rgba(5, 12, 22, 0.92);
            color: white;
            border-radius: 16px;
        }

        div[data-testid="stSidebar"] {
            background: rgba(6, 13, 23, 0.94);
        }

        button[kind="primary"], div[data-testid="stDownloadButton"] button {
            border-radius: 14px;
        }

        div[data-baseweb="tab-list"] {
            gap: 0.45rem;
        }

        button[data-baseweb="tab"] {
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.06);
            color: #dce9f5;
            padding: 0.45rem 0.85rem;
        }

        div[data-testid="stExpander"] {
            border: 1px solid rgba(157, 176, 199, 0.16);
            border-radius: 18px;
            background: rgba(9, 17, 31, 0.7);
            overflow: hidden;
        }

        .verdict-shell {
            padding: 1.5rem 1.6rem;
            border-radius: 28px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
            margin-bottom: 1rem;
        }

        .verdict-shell--build {
            background: linear-gradient(135deg, rgba(18, 92, 55, 0.96), rgba(8, 29, 21, 0.96));
        }

        .verdict-shell--caution {
            background: linear-gradient(135deg, rgba(128, 88, 14, 0.96), rgba(39, 28, 12, 0.96));
        }

        .verdict-shell--reject {
            background: linear-gradient(135deg, rgba(125, 33, 33, 0.96), rgba(37, 15, 15, 0.96));
        }

        .verdict-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.38rem 0.7rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.14);
            color: #f8fbfe;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 1rem;
        }

        .verdict-grid {
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 1rem;
            align-items: center;
        }

        .verdict-kicker {
            color: rgba(234, 242, 251, 0.82);
            font-size: 0.82rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        .verdict-action {
            color: white;
            font-family: "Space Grotesk", sans-serif;
            font-size: 3.2rem;
            font-weight: 700;
            line-height: 0.95;
            margin-bottom: 0.55rem;
        }

        .verdict-copy {
            color: #edf5fb;
            line-height: 1.65;
            margin: 0;
            max-width: 680px;
        }

        .verdict-scoreboard {
            padding: 1rem 1.05rem;
            border-radius: 22px;
            background: rgba(255, 255, 255, 0.09);
            border: 1px solid rgba(255, 255, 255, 0.14);
        }

        .verdict-score {
            color: white;
            font-family: "Space Grotesk", sans-serif;
            font-size: 3rem;
            font-weight: 700;
            line-height: 1;
            margin-bottom: 0.35rem;
        }

        .verdict-score span {
            font-size: 1rem;
            color: #d7e6f4;
        }

        .verdict-meta {
            color: #edf5fb;
            font-size: 0.98rem;
            line-height: 1.6;
        }

        .verdict-footnotes {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 0.9rem;
        }

        .verdict-footnotes span {
            padding: 0.38rem 0.7rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #f1f7fc;
            font-size: 0.84rem;
        }

        .workflow-list {
            display: grid;
            gap: 0.8rem;
        }

        .workflow-step {
            padding: 1rem 1.05rem;
            border-radius: 18px;
            border: 1px solid rgba(154, 176, 196, 0.16);
            background: rgba(9, 17, 31, 0.74);
        }

        .workflow-step--done {
            border-color: rgba(134, 239, 172, 0.25);
            background: rgba(17, 92, 55, 0.18);
        }

        .workflow-step--live {
            border-color: rgba(255, 159, 67, 0.28);
            background: rgba(130, 90, 13, 0.16);
        }

        .workflow-step-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.45rem;
        }

        .workflow-icon {
            font-size: 1.35rem;
        }

        .workflow-status {
            padding: 0.22rem 0.58rem;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .workflow-status--done {
            background: rgba(134, 239, 172, 0.16);
            color: #b5f5cb;
        }

        .workflow-status--live {
            background: rgba(255, 159, 67, 0.18);
            color: #ffd4a5;
        }

        .workflow-status--queued {
            background: rgba(157, 176, 199, 0.12);
            color: #dce9f5;
        }

        .workflow-title {
            color: white;
            font-size: 1.02rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .workflow-copy {
            color: #dce9f5;
            font-size: 0.93rem;
            line-height: 1.55;
            margin: 0;
        }

        .top-verdict-tag {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.36rem 0.72rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #f1f7fc;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.75rem;
        }

        .top-verdict-action {
            font-family: "Space Grotesk", sans-serif;
            font-size: 3.4rem;
            font-weight: 700;
            line-height: 0.95;
            margin: 0 0 0.35rem 0;
        }

        .top-verdict-action--build {
            color: #86efac;
        }

        .top-verdict-action--caution {
            color: #fde68a;
        }

        .top-verdict-action--reject {
            color: #fda4af;
        }

        .top-verdict-copy {
            color: #dce9f5;
            font-size: 1rem;
            line-height: 1.6;
            margin: 0;
            max-width: 620px;
        }

        .top-verdict-note {
            color: #9db0c7;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.3rem;
        }

        @media (max-width: 900px) {
            .hero-grid,
            .micro-grid,
            .verdict-grid {
                grid-template-columns: 1fr;
            }

            .hero-title,
            .verdict-action {
                font-size: 2.4rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_session_state() -> None:
    st.session_state.setdefault("idea_input", "")
    st.session_state.setdefault("latest_result", None)


def render_header() -> None:
    st.markdown(
        """
        <div class="hero-shell">
            <div class="hero-grid">
                <div>
                    <div class="hero-kicker">VentureMind AI</div>
                    <div class="hero-title">AI Investor Decision Engine</div>
                    <p class="hero-subtitle">Think like an investor before you build</p>
                    <p class="hero-copy">
                        VentureMind turns a rough startup concept into a visible investment decision. Multiple agents
                        research market demand, map competitors, score execution risk, and package the outcome as a
                        business-ready dashboard instead of a chat response.
                    </p>
                    <div class="chip-row">
                        <span class="hero-chip">Multi-Agent Workflow</span>
                        <span class="hero-chip">Deterministic Scoring</span>
                        <span class="hero-chip">What-If Simulator</span>
                        <span class="hero-chip">Investor-Style Report</span>
                    </div>
                </div>
                <div>
                    <div class="hero-stat">
                        <div class="hero-stat-label">Outcome</div>
                        <div class="hero-stat-value">Build / Caution / Reject</div>
                        <p class="hero-stat-copy">Judges and founders see the verdict in seconds, not paragraphs.</p>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-label">Signal</div>
                        <div class="hero-stat-value">Demand + Competition + Risk</div>
                        <p class="hero-stat-copy">The score is grounded in visible evidence and deterministic weighting.</p>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-label">Demo Moment</div>
                        <div class="hero-stat-value">Investor Scenario Studio</div>
                        <p class="hero-stat-copy">Stress-test how the decision changes if the market gets better or worse.</p>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()


def render_problem_frame() -> None:
    st.markdown(
        """
        <div class="section-eyebrow">Problem Frame</div>
        <div class="section-title">Why this matters before a single line of code is written</div>
        <p class="section-copy">
            VentureMind helps founders validate whether the pain is real, the market is large enough, and the competitive
            landscape is still open enough to justify building.
        </p>
        """,
        unsafe_allow_html=True,
    )

    cards = [
        ("Problem", PRODUCT_BRIEF["problem_statement"]),
        ("Target Users", ", ".join(PRODUCT_BRIEF["target_users"])),
        ("Why Now", PRODUCT_BRIEF["why_it_matters"]),
    ]
    columns = st.columns(3, gap="large")
    for column, (title, copy) in zip(columns, cards):
        with column:
            st.markdown(
                f"""
                <div class="glass-card">
                    <div class="section-eyebrow">{escape(title)}</div>
                    <p class="section-copy">{escape(copy)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_sidebar(resolved_settings: Settings | None, settings_error: Exception | None) -> tuple[int, int]:
    with st.sidebar:
        st.markdown("## Demo Controls")
        st.caption("Use a demo prompt or tune the reasoning depth without touching the backend.")

        st.markdown("### Quick Prompts")
        for index, prompt in enumerate(EXAMPLE_PROMPTS):
            if st.button(prompt, key=f"sidebar_prompt_{index}", use_container_width=True):
                st.session_state["idea_input"] = prompt

        default_loops = resolved_settings.max_reasoning_loops if resolved_settings else 2
        default_results = resolved_settings.search_results if resolved_settings else 5

        with st.expander("Advanced Settings", expanded=False):
            selected_loops = st.slider("Reflection loops", min_value=1, max_value=3, value=default_loops)
            selected_results = st.slider("Search results per query", min_value=3, max_value=6, value=default_results)

        with st.expander("Agent Map", expanded=False):
            st.markdown(
                "- `planner_agent` shapes the diligence plan.\n"
                "- `market_agent` gathers demand and timing signals.\n"
                "- `competitor_agent` maps rivals and substitute pressure.\n"
                "- `decision_agent` converts evidence into a deterministic verdict.\n"
                "- `report_agent` packages the output into dashboard and PDF form."
            )

        if settings_error is not None:
            st.error(str(settings_error))
            st.caption("Create `api.env` from `api.env.example` and add your API keys.")
        else:
            st.success("Environment loaded from `api.env`.")

    return selected_loops, selected_results


def render_input_section(settings_error: Exception | None) -> tuple[str, bool]:
    left_column, right_column = st.columns([1.2, 0.8], gap="large")

    with left_column:
        st.markdown(
            """
            <div class="section-eyebrow">Input Section</div>
            <div class="section-title">Describe the startup idea</div>
            <p class="section-copy">
                Write the idea in plain language. VentureMind will turn it into market research, competitor analysis,
                risk evaluation, and an investor-style decision.
            </p>
            """,
            unsafe_allow_html=True,
        )
        with st.form("startup_validation_form", clear_on_submit=False):
            startup_idea = st.text_area(
                "Enter your startup idea",
                key="idea_input",
                height=170,
                placeholder="Example: AI startup that helps independent clinics turn doctor conversations into completed admin workflows.",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button(
                "Analyze Startup",
                type="primary",
                use_container_width=True,
                disabled=settings_error is not None,
            )
        if settings_error is not None:
            st.caption("The environment must be configured before analysis can run.")

    with right_column:
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-eyebrow">What you get</div>
                <div class="section-title" style="font-size:1.2rem;">Investor-grade output in one pass</div>
                <p class="input-note">
                    The dashboard highlights the verdict, confidence, risk level, agent workflow, what-if scenarios,
                    and downloadable reports with minimal clutter.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        micro_cards = "".join(
            f"""
            <div class="micro-card">
                <h4>{escape(title)}</h4>
                <p>{escape(copy)}</p>
            </div>
            """
            for title, copy in [
                ("Fast Demo", "Use one of the sample prompts to show the flow immediately."),
                ("Visible Thinking", "Watch agents move from planning to market, competition, and risk."),
                ("What-If", "Adjust demand, competition, and risk live after the run."),
            ]
        )
        render_html_block(f'<div class="micro-grid">{micro_cards}</div>')

        st.markdown("### Demo Ideas")
        for index, prompt in enumerate(EXAMPLE_PROMPTS):
            if st.button(prompt, key=f"main_prompt_{index}", use_container_width=True):
                st.session_state["idea_input"] = prompt

    return startup_idea, submitted


def render_live_trace(events: list[TraceEvent]) -> str:
    cards = []
    for event in events[-5:]:
        cards.append(
            f"""
            <div class="trace-card">
                <div class="trace-stage">{escape(event.stage)}</div>
                <p class="trace-title">{escape(event.title)}</p>
                <p class="trace-copy">{escape(event.details)}</p>
            </div>
            """
        )
    return "".join(cards)


def build_structured_output(result: ResearchRunResult) -> dict[str, object]:
    scenario_analysis = build_investor_scenarios(result.final_brief.final_decision)
    return {
        "idea": result.final_brief.startup_idea or result.user_question,
        "key_findings": result.final_brief.key_findings,
        "market_analysis": result.final_brief.market_analysis,
        "competitor_analysis": result.final_brief.competitor_analysis,
        "swot": result.final_brief.swot,
        "final_decision": result.final_brief.final_decision,
        "scenario_analysis": scenario_analysis,
    }


HTML_BLOCK_RE = re.compile(r"<[a-zA-Z][^>]*>")
WORKFLOW_STAGE_INDEX = {
    "planning": 0,
    "market_research": 1,
    "competitor_analysis": 2,
    "evaluation": 3,
    "decision": 4,
    "report": 4,
    "storage": 5,
}
WORKFLOW_STEP_META = [
    ("🧭", "Planning...", "Turn the startup idea into a diligence plan."),
    ("📈", "Market Research...", "Collect demand, timing, and market momentum signals."),
    ("⚔️", "Competitor Analysis...", "Map rivals, substitutes, and crowding pressure."),
    ("🛡️", "Risk Evaluation...", "Pressure-test feasibility, confidence, and execution risk."),
    ("🏁", "Final Decision...", "Package the investor verdict into a demo-ready brief."),
]
ANIMATION_STEPS = [
    ("🧠", "Understanding idea..."),
    ("🔍", "Running market research..."),
    ("⚔️", "Analyzing competitors..."),
    ("📊", "Evaluating risk..."),
    ("✅", "Generating final decision..."),
]


def assess_run_quality(result: ResearchRunResult) -> dict[str, Any]:
    total_steps = len(result.observations)
    failed_steps = sum(1 for observation in result.observations if observation.status != "completed")
    source_count = sum(len(observation.sources) for observation in result.observations)
    try:
        evaluation_confidence = int(result.evaluation.confidence)
    except (TypeError, ValueError):
        evaluation_confidence = 0
    unique_publishers = {
        source.source.strip().lower()
        for observation in result.observations
        for source in observation.sources
        if source.source.strip()
    }
    reasons: list[str] = []

    if total_steps == 0:
        reasons.append("No research steps were executed.")
    elif failed_steps == total_steps:
        reasons.append("All live research steps failed, so the verdict is running on fallback logic.")
    elif failed_steps:
        reasons.append(f"{failed_steps} of {total_steps} research steps failed.")

    if source_count == 0:
        reasons.append("No external evidence was collected for this run.")
    elif source_count < 3:
        reasons.append("The evidence base is too thin for a submission-grade verdict.")

    if source_count and len(unique_publishers) < 2:
        reasons.append("Publisher diversity is limited, which weakens confidence.")

    if evaluation_confidence <= 0:
        reasons.append("The evaluator returned an invalid confidence score.")

    status = "healthy"
    if total_steps == 0 or source_count == 0 or failed_steps == total_steps:
        status = "blocked"
    elif reasons:
        status = "degraded"

    return {
        "status": status,
        "reasons": reasons,
        "source_count": source_count,
        "failed_steps": failed_steps,
        "total_steps": total_steps,
        "unique_publishers": len(unique_publishers),
    }


def render_html_block(html: str) -> None:
    html_renderer = getattr(st, "html", None)
    if callable(html_renderer):
        html_renderer(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def render_html_target(target: Any, html: str) -> None:
    html_renderer = getattr(target, "html", None)
    if callable(html_renderer):
        html_renderer(html)
    else:
        target.markdown(html, unsafe_allow_html=True)


def _contains_html(value: Any) -> bool:
    return bool(HTML_BLOCK_RE.search(str(value or "")))


def _as_text(value: Any, empty_message: str) -> str:
    text = str(value or "").strip()
    return text or empty_message


def _text_to_points(value: Any, *, max_items: int = 4) -> list[str]:
    text = str(value or "").replace("\r", "").strip()
    if not text:
        return []

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullet_lines = [line.lstrip("-*• ").strip() for line in lines if line.startswith(("-", "*", "•"))]
    if bullet_lines:
        return bullet_lines[:max_items]

    collapsed = " ".join(lines) if lines else text
    fragments = [
        fragment.strip(" -•")
        for fragment in re.split(r"(?<=[.!?])\s+|;\s+", collapsed)
        if fragment.strip(" -•")
    ]
    if not fragments:
        return [collapsed]
    return fragments[:max_items]


def render_bullet_list(items: list[str], *, empty_message: str) -> None:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        st.caption(empty_message)
        return
    for item in cleaned:
        st.markdown(f"- {item}")


def render_rich_text(value: Any, *, empty_message: str = "No details available.", bulletize: bool = False) -> None:
    text = _as_text(value, empty_message)
    if _contains_html(text):
        render_html_block(text)
        return
    if bulletize:
        render_bullet_list(_text_to_points(text), empty_message=empty_message)
        return
    st.markdown(text)


def render_section_intro(eyebrow: str, title: str, subtitle: str) -> None:
    render_html_block(
        f"""
        <div class="section-eyebrow">{escape(eyebrow)}</div>
        <div class="section-title">{escape(title)}</div>
        <p class="section-copy">{escape(subtitle)}</p>
        """
    )


def render_badge_row(badges: list[str]) -> None:
    chips = "".join(f'<span class="hero-chip">{escape(badge)}</span>' for badge in badges if badge)
    if chips:
        render_html_block(f'<div class="chip-row">{chips}</div>')


def render_verdict_card(
    final_decision: dict[str, Any],
    metrics: dict[str, Any],
    *,
    badge: str,
    source_count: int,
    memory_hits: int,
) -> None:
    verdict = str(final_decision.get("final_verdict", "Moderate"))
    tone = _verdict_tone(verdict)
    summary = _text_to_points(
        final_decision.get("reasoning") or _verdict_supporting_copy(verdict),
        max_items=1,
    )[0]
    render_html_block(
        f"""
        <div class="verdict-shell verdict-shell--{tone}">
            <div class="verdict-badge">{escape(badge)}</div>
            <div class="verdict-grid">
                <div>
                    <div class="verdict-kicker">AI Investor Decision Engine</div>
                    <div class="verdict-action">{escape(metrics["action"])}</div>
                    <p class="verdict-copy">{escape(summary)}</p>
                </div>
                <div class="verdict-scoreboard">
                    <div class="verdict-kicker">Live scorecard</div>
                    <div class="verdict-score">{metrics["score"]}<span>/100</span></div>
                    <div class="verdict-meta">
                        Confidence <strong>{metrics["confidence"]}%</strong><br/>
                        Risk <strong>{escape(metrics["risk_label"])}</strong><br/>
                        Verdict <strong>{escape(verdict)}</strong>
                    </div>
                    <div class="verdict-footnotes">
                        <span>{source_count} sources reviewed</span>
                        <span>{memory_hits} related memories</span>
                        <span>Deterministic scoring</span>
                    </div>
                </div>
            </div>
        </div>
        """
    )


def render_workflow_panel(workflow_steps: list[str], events: list[TraceEvent]) -> None:
    active_index = _workflow_active_index(events, len(workflow_steps))
    cards = []
    for index, label in enumerate(workflow_steps):
        if index < active_index:
            status = "Done"
            tone = "done"
        elif index == active_index and active_index < len(workflow_steps):
            status = "Live"
            tone = "live"
        else:
            status = "Queued"
            tone = "queued"

        if index < len(WORKFLOW_STEP_META):
            icon, fallback_label, detail = WORKFLOW_STEP_META[index]
            title = label or fallback_label
        else:
            icon, title, detail = "🤖", label or "Agent Step", "Research is in progress."

        cards.append(
            f"""
            <div class="workflow-step workflow-step--{tone}">
                <div class="workflow-step-top">
                    <div class="workflow-icon">{icon}</div>
                    <div class="workflow-status workflow-status--{tone}">{status}</div>
                </div>
                <div class="workflow-title">{escape(title.rstrip('.'))}</div>
                <p class="workflow-copy">{escape(detail)}</p>
            </div>
            """
        )
    render_html_block(f'<div class="workflow-list">{"".join(cards)}</div>')


def render_signal_bar(label: str, score: int, detail: str) -> None:
    st.markdown(f"**{label}**")
    st.progress(score / 100)
    st.caption(f"{score}/100 • {detail}")


def render_scenario_cards(scenarios: list[dict[str, Any]]) -> None:
    if not scenarios:
        st.info("No scenario analysis was generated for this run.")
        return

    columns = st.columns(min(3, len(scenarios)), gap="large")
    for column, scenario in zip(columns, scenarios[:3]):
        delta = int(scenario.get("delta", 0))
        with column:
            st.markdown(f"#### {scenario.get('name', 'Scenario')}")
            st.caption(str(scenario.get("summary", "")) or "Alternate case for the investor verdict.")
            st.metric("Scenario Score", f"{int(scenario.get('score', 0))}/100", delta=f"{delta:+d}")
            render_bullet_list(
                [
                    f"Verdict: {scenario.get('verdict', 'Moderate')}",
                    f"Demand: {scenario.get('market_demand', 'Medium')}",
                    f"Competition: {scenario.get('competition', 'Medium')}",
                    f"Risk: {scenario.get('risk', 'Medium')}",
                ],
                empty_message="No scenario details available.",
            )


def render_swot_grid(swot: dict[str, list[str]]) -> None:
    sections = [
        ("Strengths", "✅", swot.get("strengths", []) if isinstance(swot, dict) else []),
        ("Weaknesses", "⚠️", swot.get("weaknesses", []) if isinstance(swot, dict) else []),
        ("Opportunities", "🚀", swot.get("opportunities", []) if isinstance(swot, dict) else []),
        ("Threats", "🧱", swot.get("threats", []) if isinstance(swot, dict) else []),
    ]
    for start in range(0, len(sections), 2):
        columns = st.columns(2, gap="large")
        for column, (label, icon, items) in zip(columns, sections[start : start + 2]):
            with column:
                st.markdown(f"#### {icon} {label}")
                render_bullet_list(list(items), empty_message="No items surfaced for this quadrant.")


def render_recent_events(events: list[TraceEvent], *, limit: int = 5) -> None:
    recent_events = events[-limit:]
    if not recent_events:
        st.info("No execution events are available yet.")
        return

    for index, event in enumerate(recent_events):
        st.caption(event.stage.replace("_", " ").upper())
        st.markdown(f"**{_event_icon(event.stage)} {event.title}**")
        render_rich_text(event.details, bulletize=True)
        if index < len(recent_events) - 1:
            st.divider()


def build_mic_drop_insight(final_decision: dict[str, Any]) -> str:
    verdict = str(final_decision.get("final_verdict", "Moderate"))
    demand_score = _component_score(final_decision, "demand_score", "market_demand", positive=True)
    competition_score = _component_score(final_decision, "competition_score", "competition", positive=False)
    risk_score = _component_score(final_decision, "risk_score", "risk", positive=False)

    dominant_drag = max(
        [("competition", competition_score), ("risk", risk_score)],
        key=lambda item: item[1],
    )[0]

    if verdict == "Strong":
        if demand_score >= max(competition_score, risk_score):
            return "Demand is doing most of the work here, which is why this idea clears the build threshold."
        return "This idea still scores BUILD, but the moat will need to outrun pressure from the market."

    if dominant_drag == "competition":
        return "This idea falls short mainly because competitive pressure is stronger than the market pull."
    return "Execution risk is the main reason this verdict stays below BUILD."


def render_top_verdict(target: Any, result: ResearchRunResult) -> None:
    final_decision = dict(result.final_brief.final_decision)
    metrics = _dashboard_metrics(final_decision)
    run_quality = assess_run_quality(result)
    tone = _verdict_tone(str(final_decision.get("final_verdict", "Moderate")))
    summary = _text_to_points(
        final_decision.get("reasoning") or _verdict_supporting_copy(str(final_decision.get("final_verdict", "Moderate"))),
        max_items=1,
    )[0]
    insight = build_mic_drop_insight(final_decision)

    with target.container():
        if run_quality["status"] != "healthy":
            render_html_block('<div class="top-verdict-tag">Evidence Quality Alert</div>')
            verdict_col, stat_col = st.columns([1.2, 0.8], gap="large")
            with verdict_col:
                render_html_block(
                    """
                    <div class="top-verdict-note">Submission safety check</div>
                    <div class="top-verdict-action top-verdict-action--moderate">EVIDENCE LIMITED</div>
                    <p class="top-verdict-copy">
                        This run completed, but the evidence quality is not strong enough to present as a normal judge-facing verdict.
                    </p>
                    """
                )
            with stat_col:
                stat_grid = st.columns(3, gap="small")
                stat_grid[0].metric("Sources", str(run_quality["source_count"]))
                stat_grid[1].metric("Failed Steps", f"{run_quality['failed_steps']}/{run_quality['total_steps']}")
                stat_grid[2].metric("Confidence", f"{metrics['confidence']}%")
            st.warning("Review the evidence warnings below before using this output in a demo or submission.")
            render_bullet_list(run_quality["reasons"], empty_message="No evidence-quality issues were detected.")
            return

        render_html_block('<div class="top-verdict-tag">Final Investor Verdict</div>')
        verdict_col, stat_col = st.columns([1.2, 0.8], gap="large")
        with verdict_col:
            render_html_block(
                f"""
                <div class="top-verdict-note">First investor signal</div>
                <div class="top-verdict-action top-verdict-action--{tone}">{escape(metrics["action"])}</div>
                <p class="top-verdict-copy">{escape(summary)}</p>
                """
            )
        with stat_col:
            stat_grid = st.columns(3, gap="small")
            stat_grid[0].metric("Score", f"{metrics['score']}/100")
            stat_grid[1].metric("Confidence", f"{metrics['confidence']}%")
            stat_grid[2].metric("Risk Level", metrics["risk_label"])
        st.info(f"Mic Drop Insight: {insight}")


def render_results(result: ResearchRunResult) -> None:
    structured_output = build_structured_output(result)
    run_quality = assess_run_quality(result)
    st.divider()
    render_section_intro(
        "Results Dashboard",
        "Investment decision, evidence, and what-if analysis",
        "Verdict first, supporting signals second, and the deeper reasoning one click away.",
    )
    if run_quality["status"] != "healthy":
        st.warning(
            "This run is evidence-limited. Treat the dashboard as draft analysis until the warnings below are resolved."
        )
        render_bullet_list(
            run_quality["reasons"],
            empty_message="No evidence-quality issues were detected.",
        )

    dashboard_tab, reasoning_tab, data_room_tab = st.tabs(
        ["📊 Decision Dashboard", "🧠 Agent Reasoning", "🗂 Diligence Room"]
    )

    with dashboard_tab:
        render_decision_dashboard(result, structured_output)
    with reasoning_tab:
        render_reasoning_panel(result)
    with data_room_tab:
        render_data_room(result, structured_output)


def render_decision_dashboard(result: ResearchRunResult, structured_output: dict[str, object]) -> None:
    final_decision = dict(result.final_brief.final_decision)
    metrics = _dashboard_metrics(final_decision)
    source_count = sum(len(observation.sources) for observation in result.observations)
    workflow_steps = result.workflow_steps or WORKFLOW_STEPS
    market_observations = [observation for observation in result.observations if not _is_competitor_observation(observation)]
    competitor_observations = [observation for observation in result.observations if _is_competitor_observation(observation)]
    insight_points = result.final_brief.key_findings or _collect_data_points(result.observations, limit=4)
    render_section_intro(
        "Decision Dashboard",
        "Scoreboard and supporting signals",
        "The verdict now lives above the fold, so this section focuses on why the score landed where it did.",
    )
    render_badge_row(
        [
            f"{source_count} sources reviewed",
            f"{len(result.related_memories)} memory hits",
            "Deterministic scoring",
        ]
    )

    metric_columns = st.columns(4, gap="large")
    metric_columns[0].metric("Decision", metrics["action"])
    metric_columns[1].metric("Score", f"{metrics['score']}/100")
    metric_columns[2].metric("Confidence", f"{metrics['confidence']}%")
    metric_columns[3].metric("Risk Level", metrics["risk_label"])

    insight_col, workflow_col = st.columns([1.05, 0.95], gap="large")
    with insight_col:
        render_section_intro(
            "Judge Snapshot",
            "What matters in the first five seconds",
            "Keep the message short: core signals, confidence, and why the call landed here.",
        )
        render_badge_row(
            [
                "Multi-Agent Workflow",
                "Deterministic Scoring",
                "What-if Simulator",
            ]
        )
        st.markdown("**Key Insights**")
        render_bullet_list(insight_points[:4], empty_message="No key insights were generated.")
        st.markdown("**Decision Logic**")
        render_rich_text(
            final_decision.get("reasoning", "No decision reasoning available."),
            bulletize=True,
        )

    with workflow_col:
        render_section_intro(
            "Agent Workflow",
            "Visible multi-agent execution",
            "Judges can follow the research path from planning to final decision.",
        )
        render_workflow_panel(workflow_steps, result.trace)
        st.caption(f"Sources used: {source_count} • Memory hits: {len(result.related_memories)}")

    signal_col, evidence_col = st.columns([0.78, 1.22], gap="large")
    with signal_col:
        render_section_intro(
            "Signal Snapshot",
            "The score behind the verdict",
            "Big numbers first, then the three drivers behind the final call.",
        )
        signal_grid = st.columns(2, gap="large")
        signal_grid[0].metric("Market Demand", final_decision.get("market_demand", "Medium"))
        signal_grid[1].metric("Competition", final_decision.get("competition", "Medium"))
        signal_grid[0].metric("Risk Score", f"{metrics['risk_score']}/100")
        signal_grid[1].metric("Growth Potential", metrics["growth_label"])
        render_signal_bar("Overall Investor Score", metrics["score"], "Combined score across demand, competition, and risk.")
        render_signal_bar(
            "Demand Strength",
            _component_score(final_decision, "demand_score", "market_demand", positive=True),
            "Higher is better.",
        )
        render_signal_bar(
            "Competition Pressure",
            _component_score(final_decision, "competition_score", "competition", positive=False),
            "Lower is better.",
        )
        render_signal_bar(
            "Execution Risk",
            _component_score(final_decision, "risk_score", "risk", positive=False),
            "Lower is better.",
        )

    with evidence_col:
        render_section_intro(
            "Research Summary",
            "Market and competitor readout",
            "Long paragraphs are compressed into quick-scanning evidence blocks.",
        )
        market_col, competitor_col = st.columns(2, gap="large")
        with market_col:
            st.markdown("#### Market Research")
            render_rich_text(
                result.final_brief.market_analysis,
                empty_message="No market summary available.",
                bulletize=True,
            )
            st.markdown("**Fast facts**")
            render_bullet_list(
                _collect_data_points(market_observations),
                empty_message="No market evidence was captured.",
            )

        with competitor_col:
            st.markdown("#### Competitor Analysis")
            render_rich_text(
                result.final_brief.competitor_analysis,
                empty_message="No competitor summary available.",
                bulletize=True,
            )
            st.markdown("**Competitive pressure**")
            render_bullet_list(
                _collect_data_points(competitor_observations),
                empty_message="No competitor evidence was captured.",
            )

    simulator_col, scenario_col = st.columns([0.9, 1.1], gap="large")
    with simulator_col:
        render_section_intro(
            "What-If Simulator",
            "Stress-test the verdict live",
            "Move the market variables and watch the investor recommendation react.",
        )
        demand_adjustment = st.slider("Market Demand Adjustment", min_value=-25, max_value=25, value=0, step=5)
        competition_adjustment = st.slider("Competition Adjustment", min_value=-25, max_value=25, value=0, step=5)
        risk_adjustment = st.slider("Risk Adjustment", min_value=-25, max_value=25, value=0, step=5)

        simulated_decision = _simulate_decision(
            final_decision,
            demand_adjustment=demand_adjustment,
            competition_adjustment=competition_adjustment,
            risk_adjustment=risk_adjustment,
        )
        sim_metrics = _dashboard_metrics(simulated_decision)
        simulator_metric_cols = st.columns(3, gap="large")
        simulator_metric_cols[0].metric("Updated Decision", sim_metrics["action"])
        simulator_metric_cols[1].metric("Updated Score", f"{sim_metrics['score']}/100")
        simulator_metric_cols[2].metric("Updated Confidence", f"{sim_metrics['confidence']}%")
        render_rich_text(
            simulated_decision.get("reasoning", "Simulation results are unavailable."),
            bulletize=True,
        )

    with scenario_col:
        render_section_intro(
            "Investor Scenario Studio",
            "Three fast alternate outcomes",
            "This is the demo moment for showing how robust the verdict really is.",
        )
        render_scenario_cards(list(structured_output["scenario_analysis"]))


def render_reasoning_panel(result: ResearchRunResult) -> None:
    market_observations = [observation for observation in result.observations if not _is_competitor_observation(observation)]
    competitor_observations = [observation for observation in result.observations if _is_competitor_observation(observation)]
    workflow_steps = result.workflow_steps or WORKFLOW_STEPS

    summary_col, trace_col = st.columns([1.05, 0.95], gap="large")
    with summary_col:
        render_section_intro(
            "Agent Reasoning Panel",
            "How the agents thought",
            "Each expander below maps to one responsibility in the multi-agent workflow.",
        )

        with st.expander("📈 Market Agent Output", expanded=True):
            st.markdown("**Summary**")
            render_rich_text(
                result.final_brief.market_analysis,
                empty_message="No market summary available.",
                bulletize=True,
            )
            st.markdown("**Key data points**")
            render_bullet_list(
                _collect_data_points(market_observations),
                empty_message="No market evidence was collected.",
            )

        with st.expander("⚔️ Competitor Agent Output", expanded=False):
            st.markdown("**Summary**")
            render_rich_text(
                result.final_brief.competitor_analysis,
                empty_message="No competitor summary available.",
                bulletize=True,
            )
            st.markdown("**Key data points**")
            render_bullet_list(
                _collect_data_points(competitor_observations),
                empty_message="No competitor evidence was collected.",
            )

        with st.expander("🛡️ Risk Agent Output", expanded=False):
            st.markdown("**Risk summary**")
            render_rich_text(
                result.evaluation.reasoning_summary,
                empty_message="No risk summary available.",
                bulletize=True,
            )
            st.markdown("**Strengths**")
            render_bullet_list(result.evaluation.strengths, empty_message="No strengths were surfaced.")
            st.markdown("**Gaps / risks**")
            render_bullet_list(result.evaluation.gaps, empty_message="No obvious gaps were surfaced.")
            st.markdown("**Final decision logic**")
            render_rich_text(
                result.final_brief.final_decision.get("reasoning", "No decision reasoning available."),
                bulletize=True,
            )

    with trace_col:
        render_section_intro(
            "Execution Trace",
            "Live orchestration recap",
            "This is the clearest proof that the system is using multiple agents, not one long response.",
        )
        render_workflow_panel(workflow_steps, result.trace)
        st.markdown("### Recent events")
        render_recent_events(result.trace)


def render_data_room(result: ResearchRunResult, structured_output: dict[str, object]) -> None:
    left_column, right_column = st.columns([1.05, 0.95], gap="large")

    with left_column:
        render_section_intro(
            "Downloads",
            "Report handoff",
            "Carry the same decision into judging, founder review, or follow-up docs.",
        )
        download_columns = st.columns(2, gap="large")
        download_columns[0].download_button(
            "Download Markdown Report",
            data=result.final_markdown,
            file_name=f"venturemind_report_{result.run_id}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        try:
            pdf_bytes = generate_pdf_report(structured_output)
        except RuntimeError as exc:
            download_columns[1].warning(str(exc))
        else:
            download_columns[1].download_button(
                "Download PDF Report",
                data=pdf_bytes,
                file_name=f"venturemind_report_{result.run_id}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        st.markdown("### SWOT")
        render_swot_grid(result.final_brief.swot)

        st.markdown("### Recommended Actions")
        render_bullet_list(result.final_brief.recommended_actions, empty_message="No actions were recommended.")
        st.markdown("### Open Questions")
        render_bullet_list(result.final_brief.open_questions, empty_message="No open questions were surfaced.")

    with right_column:
        render_section_intro(
            "Structured Output",
            "Clean JSON for demos and docs",
            "Keep the raw payload available, but out of the way for screen recording.",
        )
        with st.expander("Open structured output", expanded=False):
            st.json(structured_output)

    evidence_tab, trace_tab, memory_tab = st.tabs(["Evidence", "Execution Trace", "Memory"])
    with evidence_tab:
        if not result.observations:
            st.info("No evidence was collected in this run.")
        for observation in result.observations:
            with st.expander(f"{observation.tool_name} | {observation.query}", expanded=False):
                st.caption(f"Status: {observation.status}")
                render_rich_text(
                    observation.summary,
                    empty_message="No evidence summary available.",
                    bulletize=True,
                )
                if observation.error:
                    st.error(observation.error)
                if observation.data_points:
                    st.markdown("**Key data points**")
                    render_bullet_list(observation.data_points, empty_message="No data points were collected.")
                if observation.sources:
                    st.markdown("**Sources**")
                    for source in observation.sources:
                        label = source.title or source.url
                        suffix = f" - {source.source}" if source.source else ""
                        if source.published_at:
                            suffix += f" ({source.published_at})"
                        st.markdown(f"- [{label}]({source.url}){suffix}")

    with trace_tab:
        for event in result.trace:
            with st.expander(
                f"{event.stage.upper()} | {event.title}",
                expanded=event.stage in {"planning", "decision", "report"},
            ):
                render_rich_text(
                    event.details,
                    empty_message="No event details are available.",
                    bulletize=True,
                )
                if event.metadata:
                    st.json(event.metadata)

    with memory_tab:
        if not result.related_memories:
            st.info("No related historical runs were found yet.")
        else:
            for memory in result.related_memories:
                with st.expander(f"{memory.user_question} | similarity {memory.score:.2f}"):
                    render_rich_text(
                        memory.summary,
                        empty_message="No memory summary is available.",
                        bulletize=True,
                    )
                    st.caption(f"Confidence: {memory.confidence}/100 | Created: {memory.created_at}")
        st.markdown("**Trace file**")
        st.markdown(f"`{result.trace_path}`")


def _dashboard_metrics(final_decision: dict[str, Any]) -> dict[str, Any]:
    score = int(final_decision.get("score", 0))
    confidence = int(final_decision.get("confidence", 0))
    demand_score = _component_score(final_decision, "demand_score", "market_demand", positive=True)
    competition_score = _component_score(final_decision, "competition_score", "competition", positive=False)
    risk_score = _component_score(final_decision, "risk_score", "risk", positive=False)
    growth_score = _clamp(int(round(demand_score * 0.6 + score * 0.4 - competition_score * 0.1)))
    verdict = str(final_decision.get("final_verdict", "Moderate"))
    return {
        "score": score,
        "confidence": confidence,
        "risk_score": risk_score,
        "growth_score": growth_score,
        "growth_label": _label_from_score(growth_score),
        "risk_label": str(final_decision.get("risk", _label_from_score(risk_score))),
        "action": _decision_action(verdict),
    }


def _simulate_decision(
    final_decision: dict[str, Any],
    *,
    demand_adjustment: int,
    competition_adjustment: int,
    risk_adjustment: int,
) -> dict[str, Any]:
    base_score = int(final_decision.get("score", 0))
    base_confidence = int(final_decision.get("confidence", 0))
    demand_score = _clamp(
        _component_score(final_decision, "demand_score", "market_demand", positive=True) + demand_adjustment
    )
    competition_score = _clamp(
        _component_score(final_decision, "competition_score", "competition", positive=False)
        + competition_adjustment
    )
    risk_score = _clamp(
        _component_score(final_decision, "risk_score", "risk", positive=False) + risk_adjustment
    )
    score = _clamp(
        int(
            round(
                demand_score * 0.5
                + (100 - competition_score) * 0.3
                + (100 - risk_score) * 0.2
            )
        )
    )
    confidence = _clamp(
        int(
            round(
                base_confidence
                + demand_adjustment * 0.25
                - abs(competition_adjustment) * 0.15
                - abs(risk_adjustment) * 0.2
            )
        )
    )
    return {
        "score": score,
        "market_demand": _label_from_score(demand_score),
        "competition": _label_from_score(competition_score),
        "risk": _label_from_score(risk_score),
        "final_verdict": _verdict_from_score(score),
        "confidence": confidence,
        "reasoning": (
            f"Compared with the live score of {base_score}, this simulation applies demand {demand_adjustment:+d}, "
            f"competition {competition_adjustment:+d}, and risk {risk_adjustment:+d} to show how sensitive the "
            "investment case is under changed market conditions."
        ),
        "demand_score": demand_score,
        "competition_score": competition_score,
        "risk_score": risk_score,
    }


def _component_score(
    final_decision: dict[str, Any],
    numeric_key: str,
    label_key: str,
    *,
    positive: bool,
) -> int:
    if numeric_key in final_decision:
        return _clamp(int(final_decision[numeric_key]))
    return _label_to_score(final_decision.get(label_key, "Medium"), positive=positive)


def _label_to_score(value: Any, *, positive: bool) -> int:
    normalized = str(value).strip().lower()
    if positive:
        mapping = {"high": 78, "medium": 55, "low": 30}
    else:
        mapping = {"high": 74, "medium": 52, "low": 28}
    return mapping.get(normalized, 52)


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


def _decision_action(verdict: str) -> str:
    if verdict == "Strong":
        return "BUILD"
    if verdict == "Moderate":
        return "CAUTION"
    return "REJECT"


def _verdict_tone(verdict: str) -> str:
    if verdict == "Strong":
        return "build"
    if verdict == "Moderate":
        return "caution"
    return "reject"


def _verdict_supporting_copy(verdict: str) -> str:
    if verdict == "Strong":
        return "Strong demand and manageable risk make this a build-worthy opportunity."
    if verdict == "Moderate":
        return "The opportunity is promising, but the team should validate key assumptions before fully committing."
    return "The downside is currently too high, so this idea needs rework before it earns investor confidence."


def _workflow_active_index(events: list[TraceEvent], step_count: int) -> int:
    if not events:
        return 0

    latest = next(
        (
            event
            for event in reversed(events)
            if event.stage in {"planning", "market_research", "competitor_analysis", "evaluation", "decision", "report", "storage"}
        ),
        None,
    )
    if latest is None:
        return 0
    if latest.stage == "storage":
        return step_count
    return WORKFLOW_STAGE_INDEX.get(latest.stage, 0)


def _event_icon(stage: str) -> str:
    icon_map = {
        "intake": "📝",
        "memory": "🧠",
        "planning": "🧭",
        "market_research": "📈",
        "competitor_analysis": "⚔️",
        "evaluation": "🛡️",
        "decision": "🏁",
        "report": "📄",
        "storage": "🗃️",
    }
    return icon_map.get(stage, "🤖")


def _clamp(value: int) -> int:
    return max(0, min(100, value))


def _is_competitor_observation(observation: ToolObservation) -> bool:
    combined = f"{observation.objective} {observation.query}".lower()
    return any(token in combined for token in {"competitor", "competition", "alternative"})


def _collect_data_points(observations: list[ToolObservation], limit: int = 6) -> list[str]:
    points: list[str] = []
    for observation in observations:
        for point in observation.data_points[:2]:
            points.append(point)
        if len(points) >= limit:
            break
    return points[:limit] or ["No granular data points were captured for this panel."]


def main() -> None:
    st.set_page_config(
        page_title="VentureMind AI",
        page_icon="🚀",
        layout="wide",
    )

    initialize_session_state()
    inject_styles()

    settings_error = None
    resolved_settings = None
    try:
        resolved_settings = Settings.from_env()
    except Exception as exc:  # pragma: no cover - UI path
        settings_error = exc

    selected_loops, selected_results = render_sidebar(resolved_settings, settings_error)
    render_header()
    render_problem_frame()
    st.divider()

    startup_idea, submitted = render_input_section(settings_error)
    top_verdict_placeholder = st.empty()
    st.divider()

    st.markdown(
        """
        <div class="section-eyebrow">Execution Section</div>
        <div class="section-title">Watch the agents evaluate the startup</div>
        <p class="section-copy">This panel turns the orchestration layer into something judges can immediately understand.</p>
        """,
        unsafe_allow_html=True,
    )

    execution_left, execution_right = st.columns([1.15, 0.85], gap="large")
    with execution_left:
        stepper_placeholder = st.empty()
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        render_html_target(stepper_placeholder, analysis_stepper_html([]))
    with execution_right:
        live_trace_placeholder = st.empty()
        live_trace_placeholder.info(
            "Run an analysis to see market analysis, competitor analysis, risk evaluation, and the final decision play out live."
        )

    if submitted:
        if not startup_idea.strip():
            st.warning("Enter a startup idea before running VentureMind AI.")
        elif resolved_settings is None:
            st.error("The environment is not configured yet.")
        else:
            top_verdict_placeholder.empty()
            st.session_state["latest_result"] = None
            runtime_settings = replace(
                resolved_settings,
                max_reasoning_loops=selected_loops,
                search_results=selected_results,
            )
            orchestrator = AgentathonOrchestrator(settings=runtime_settings)
            progress_state = {"value": 0.02}
            progress = progress_placeholder.progress(progress_state["value"])
            live_events: list[TraceEvent] = []

            for index, (icon, step) in enumerate(ANIMATION_STEPS, start=1):
                status_placeholder.info(f"{icon} {step}")
                progress_state["value"] = max(progress_state["value"], 0.03 + index * 0.03)
                progress.progress(progress_state["value"])
                time.sleep(0.6)

            def on_event(event: TraceEvent) -> None:
                live_events.append(event)
                progress_state["value"] = max(progress_state["value"], STAGE_PROGRESS.get(event.stage, 0.5))
                progress.progress(progress_state["value"])
                render_html_target(stepper_placeholder, analysis_stepper_html(live_events))
                status_placeholder.info(f"AI Agents are evaluating... {event.title}")
                render_html_target(live_trace_placeholder, render_live_trace(live_events))

            with st.spinner("AI Agents are evaluating..."):
                try:
                    result = orchestrator.run(startup_idea, event_callback=on_event)
                except Exception as exc:
                    progress_placeholder.empty()
                    status_placeholder.empty()
                    st.error(f"Validation failed: {exc}")
                    if "1010" in str(exc) or "Cloudflare" in str(exc):
                        st.info(
                            "This usually means Groq blocked the request at the edge. "
                            "Try a different network, disable VPN or proxy, confirm the key works in Groq Console, "
                            "and retry after restarting Streamlit."
                        )
                else:
                    progress.progress(1.0)
                    run_quality = assess_run_quality(result)
                    st.session_state["latest_result"] = result
                    if run_quality["status"] == "healthy":
                        status_placeholder.success("Analysis complete. The dashboard below is ready for review.")
                        st.success("Analysis complete. Review the decision dashboard below.")
                    else:
                        status_placeholder.warning(
                            "Analysis completed with evidence gaps. Review the warnings before relying on the verdict."
                        )
                        st.warning(
                            "Analysis completed in a degraded state. Review the evidence warnings before using this verdict in a demo."
                        )

    latest_result = st.session_state.get("latest_result")
    if latest_result:
        render_top_verdict(top_verdict_placeholder, latest_result)
        render_results(latest_result)
    elif not submitted:
        st.info(
            "Paste a startup idea and hit Analyze Startup. The dashboard will respond with an investor verdict, "
            "structured business analysis, live workflow visibility, and a dynamic what-if simulator."
        )


if __name__ == "__main__":
    main()
