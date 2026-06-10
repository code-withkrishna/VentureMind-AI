from __future__ import annotations

import time
from dataclasses import replace
from html import escape
from typing import Any

import streamlit as st

from core.config import Settings
from core.models import ResearchRunResult, TraceEvent
from core.orchestrator import AgentathonOrchestrator, WORKFLOW_STEPS
from ui.rendering import (
    AGENT_META,
    action_label,
    agent_pipeline_html,
    html,
    render_live_panel,
    render_scenario_cards,
    render_swot,
    render_verdict_card,
    score_arc_svg,
    section_label,
    signal_bar,
    verdict_accent,
    verdict_bg,
)
from utils.report_generator import generate_pdf_report
from utils.scenario_engine import build_investor_scenarios

# ── Constants ─────────────────────────────────────────────────────────────────

EXAMPLE_IDEAS = [
    "AI startup that helps college students choose careers using mentor calls and placement data.",
    "Fintech startup that automates invoice collections for SMBs in India.",
    "Healthcare startup that reduces clinic admin workload with voice-to-workflow AI.",
    "E-commerce tool that helps D2C brands predict stockouts and demand shifts.",
    "B2B SaaS that lets law firms automate contract review using specialised LLMs.",
]

DEPLOYMENT_URL = ""  # Set to your deployed URL (e.g. "https://yourapp.streamlit.app")
NOVUS_SNIPPET  = ""  # Optional: paste analytics script tag here

STAGE_PROGRESS = {
    "intake": 0.05, "memory": 0.12, "planning": 0.28,
    "market_research": 0.48, "competitor_analysis": 0.64,
    "evaluation": 0.78, "decision": 0.90, "report": 0.96, "storage": 1.0,
}

# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600&display=swap');

:root {
  --ink:        #080a0d;
  --ink-2:      #0e1216;
  --ink-3:      #161b22;
  --ink-4:      #1c2330;
  --border:     rgba(255,255,255,.06);
  --border-m:   rgba(255,255,255,.1);
  --border-s:   rgba(255,255,255,.04);
  --text:       #dde4ec;
  --text-dim:   #a8b4c0;
  --muted:      #6b7885;
  --faint:      #374049;
  --gold:       #c9a84c;
  --gold-l:     #e2b95c;
  --gold-d:     #a8892e;
  --green:      #22c55e;
  --amber:      #f59e0b;
  --red:        #ef4444;
  --blue:       #60a5fa;
  --purple:     #a78bfa;
  --serif:      'DM Serif Display', Georgia, serif;
  --sans:       'DM Sans', system-ui, -apple-system, sans-serif;
  --r:          14px;
  --r-lg:       22px;
  --r-xl:       28px;
}

/* ── Base reset ── */
html, body, [class*="css"], .stApp {
  font-family: var(--sans) !important;
  background: var(--ink) !important;
  color: var(--text) !important;
  -webkit-font-smoothing: antialiased !important;
  text-rendering: optimizeLegibility !important;
}

/* ── Strip Streamlit chrome ── */
#MainMenu, footer, header,
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"] { display: none !important; }

/* ── Layout ── */
div[data-testid="stAppViewContainer"] { background: var(--ink) !important; }
.block-container {
  padding-top: 1.5rem !important;
  padding-bottom: 5rem !important;
  max-width: 1120px !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: var(--ink-2) !important;
  border-right: 1px solid var(--border) !important;
  min-width: 262px !important;
  max-width: 262px !important;
}
section[data-testid="stSidebar"] .block-container {
  padding: 1.4rem 1rem !important;
}

/* ── Typography ── */
h1, h2, h3 {
  font-family: var(--serif) !important;
  color: var(--text) !important;
  letter-spacing: -.025em !important;
  line-height: 1.12 !important;
}
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 2rem 0 !important;
}
p { color: var(--text-dim) !important; line-height: 1.68 !important; }

/* ── Form shell ── */
div[data-testid="stForm"] {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}

/* ── Textarea ── */
textarea {
  font-family: var(--sans) !important;
  font-size: .97rem !important;
  background: var(--ink-3) !important;
  color: var(--text) !important;
  border: 1px solid var(--border-m) !important;
  border-radius: var(--r-lg) !important;
  line-height: 1.68 !important;
  caret-color: var(--gold) !important;
  transition: border-color .2s, box-shadow .2s !important;
  padding: 1rem 1.15rem !important;
  resize: none !important;
}
textarea:focus {
  border-color: rgba(201,168,76,.45) !important;
  box-shadow: 0 0 0 4px rgba(201,168,76,.07) !important;
  outline: none !important;
}
textarea::placeholder { color: var(--faint) !important; }

/* ── Primary button ── */
div[data-testid="stFormSubmitButton"] button,
button[kind="primary"] {
  background: linear-gradient(135deg, var(--gold) 0%, var(--gold-l) 100%) !important;
  color: #060809 !important;
  font-family: var(--sans) !important;
  font-weight: 600 !important;
  font-size: .9rem !important;
  letter-spacing: .045em !important;
  border: none !important;
  border-radius: var(--r-lg) !important;
  padding: .8rem 1.5rem !important;
  transition: all .18s !important;
  width: 100% !important;
  box-shadow: 0 2px 12px rgba(201,168,76,.25) !important;
}
div[data-testid="stFormSubmitButton"] button:hover,
button[kind="primary"]:hover {
  box-shadow: 0 4px 20px rgba(201,168,76,.4) !important;
  transform: translateY(-1px) !important;
}
div[data-testid="stFormSubmitButton"] button:active,
button[kind="primary"]:active {
  transform: translateY(0) !important;
}

/* ── Secondary buttons ── */
button[kind="secondary"] {
  background: transparent !important;
  color: var(--muted) !important;
  font-family: var(--sans) !important;
  border: 1px solid var(--border-m) !important;
  border-radius: var(--r) !important;
  font-size: .82rem !important;
  transition: all .15s !important;
}
button[kind="secondary"]:hover {
  border-color: rgba(201,168,76,.35) !important;
  color: var(--gold-l) !important;
  background: rgba(201,168,76,.04) !important;
}

/* ── Metrics ── */
div[data-testid="metric-container"] {
  background: var(--ink-3) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r) !important;
  padding: 1rem 1.15rem !important;
}
div[data-testid="metric-container"] label {
  color: var(--muted) !important;
  font-size: .72rem !important;
  text-transform: uppercase !important;
  letter-spacing: .1em !important;
  font-weight: 600 !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
  font-family: var(--serif) !important;
  font-size: 1.45rem !important;
  color: var(--text) !important;
}

/* ── Tabs ── */
div[data-baseweb="tab-list"] {
  gap: 3px !important;
  background: var(--ink-3) !important;
  border-radius: var(--r-lg) !important;
  padding: 4px !important;
  border: 1px solid var(--border) !important;
}
button[data-baseweb="tab"] {
  border-radius: 10px !important;
  font-family: var(--sans) !important;
  font-size: .84rem !important;
  color: var(--muted) !important;
  background: transparent !important;
  padding: .52rem 1rem !important;
  transition: all .15s !important;
  font-weight: 400 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  background: var(--ink-4) !important;
  color: var(--text) !important;
  font-weight: 500 !important;
  box-shadow: 0 1px 3px rgba(0,0,0,.3) !important;
}

/* ── Expanders ── */
div[data-testid="stExpander"] {
  background: var(--ink-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r) !important;
  overflow: hidden !important;
}
div[data-testid="stExpander"] summary {
  font-family: var(--sans) !important;
  font-size: .88rem !important;
  color: var(--text) !important;
  padding: .75rem 1rem !important;
}

/* ── Progress bar ── */
div[data-testid="stProgressBar"] > div {
  background: rgba(255,255,255,.055) !important;
  border-radius: 99px !important;
  overflow: hidden !important;
}
div[data-testid="stProgressBar"] > div > div {
  background: linear-gradient(90deg, var(--gold-d), var(--gold), var(--gold-l)) !important;
  border-radius: 99px !important;
  transition: width .35s ease !important;
  box-shadow: 0 0 10px rgba(201,168,76,.4) !important;
}

/* ── Sliders ── */
div[data-testid="stSlider"] > div > div > div { background: var(--gold) !important; }
div[data-testid="stSlider"] > div > div { background: var(--ink-3) !important; }
div[data-testid="stSlider"] label { color: var(--muted) !important; font-size: .8rem !important; }

/* ── Download button ── */
div[data-testid="stDownloadButton"] button {
  background: var(--ink-3) !important;
  color: var(--text-dim) !important;
  border: 1px solid var(--border-m) !important;
  border-radius: var(--r) !important;
  font-family: var(--sans) !important;
  font-size: .84rem !important;
  transition: all .15s !important;
}
div[data-testid="stDownloadButton"] button:hover {
  border-color: rgba(201,168,76,.35) !important;
  color: var(--gold-l) !important;
  background: rgba(201,168,76,.04) !important;
}

/* ── Alerts ── */
div[data-testid="stAlert"] {
  border-radius: var(--r) !important;
  border-left: 2px solid !important;
  font-size: .84rem !important;
}
.stSuccess { background: rgba(34,197,94,.07) !important; border-color: var(--green) !important; }
.stWarning { background: rgba(245,158,11,.07) !important; border-color: var(--amber) !important; }
.stError   { background: rgba(239,68,68,.07) !important; border-color: var(--red)   !important; }

/* ── Caption ── */
div[data-testid="stCaptionContainer"] p, small, .stCaption {
  color: var(--muted) !important;
  font-size: .78rem !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--ink); }
::-webkit-scrollbar-thumb { background: var(--ink-4); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--faint); }

/* ── Selection ── */
::selection { background: rgba(201,168,76,.22); color: var(--text); }

/* ── Animations ── */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: .3; transform: scale(.85); }
}
@keyframes verdict-reveal {
  from { opacity: 0; transform: scale(.93) translateY(8px); }
  to   { opacity: 1; transform: scale(1)  translateY(0); }
}
@keyframes score-count {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}
</style>
"""

# ── Page config ───────────────────────────────────────────────────────────────

def setup_page() -> None:
    st.set_page_config(
        page_title="VentureMind AI — AI Investment Committee",
        page_icon="◆",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(CSS, unsafe_allow_html=True)
    if NOVUS_SNIPPET:
        st.html(NOVUS_SNIPPET)
    # Open Graph meta for social sharing
    st.markdown(
        '''<meta property="og:title" content="VentureMind AI — AI Investment Committee"/>
<meta property="og:description" content="Six AI agents debate your startup idea. BUILD, CAUTION, or REJECT verdict in 90 seconds."/>
<meta name="twitter:card" content="summary_large_image"/>''',
        unsafe_allow_html=True,
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar(resolved: Settings | None, err: Exception | None) -> tuple[int, int]:
    with st.sidebar:
        html("""
        <div style="margin-bottom:1.4rem;padding-bottom:1.1rem;border-bottom:1px solid rgba(255,255,255,.06);">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">
            <span style="font-size:.9rem;color:#c9a84c;opacity:.8;">◆</span>
            <span style="font-family:'DM Serif Display',Georgia,serif;font-size:1.05rem;
                         color:#dde4ec;letter-spacing:-.01em;font-weight:400;">VentureMind</span>
          </div>
          <div style="font-size:.7rem;color:#556070;letter-spacing:.05em;padding-left:1.35rem;">
            AI Investment Committee
          </div>
        </div>
        <div style="font-size:.6rem;color:#556070;text-transform:uppercase;letter-spacing:.13em;
                    font-weight:600;margin-bottom:.65rem;">Try an example</div>
        """)

        for i, idea in enumerate(EXAMPLE_IDEAS):
            label = idea[:54] + "…" if len(idea) > 54 else idea
            if st.button(label, key=f"ex_{i}", use_container_width=True):
                st.session_state["idea_input"] = idea

        html('<hr style="border:none;border-top:1px solid rgba(255,255,255,.07);margin:1.2rem 0;">')

        with st.expander("Agent Pipeline", expanded=False):
            for num, name, desc, _ in AGENT_META:
                html(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.05);">
                  <div style="font-size:.7rem;color:#404a56;">{num}</div>
                  <div>
                    <div style="font-size:.84rem;font-weight:500;color:#e8ecf0;">{name}</div>
                    <div style="font-size:.76rem;color:#7a8694;">{desc}</div>
                  </div>
                </div>""")

        with st.expander("Advanced", expanded=False):
            loops   = st.slider("Reflection loops",  1, 3, resolved.max_reasoning_loops if resolved else 2)
            results = st.slider("Results per query", 3, 6, resolved.search_results      if resolved else 5)

        if err:
            st.error("Configure api.env to run live analysis.")
        else:
            html('<div style="display:flex;align-items:center;gap:6px;font-size:.75rem;color:#22c55e;margin-top:.6rem;"><span style="width:5px;height:5px;border-radius:50%;background:#22c55e;animation:pulse-dot 3s ease-in-out infinite;flex-shrink:0;"></span>Environment ready</div>')

    return loops, results


# ── Hero ──────────────────────────────────────────────────────────────────────

def render_hero() -> None:
    html("""
<div style="padding:3.2rem 0 2rem;animation:fadeUp .55s cubic-bezier(.22,.68,0,1.1) both;">

  <!-- Status pill -->
  <div style="display:inline-flex;align-items:center;gap:7px;
              background:rgba(201,168,76,.08);
              border:1px solid rgba(201,168,76,.18);
              border-radius:99px;padding:4px 13px;margin-bottom:1.6rem;">
    <span style="width:5px;height:5px;border-radius:50%;background:#c9a84c;
                 animation:pulse-dot 2.2s ease-in-out infinite;flex-shrink:0;"></span>
    <span style="font-size:.65rem;color:#c9a84c;letter-spacing:.12em;font-weight:600;text-transform:uppercase;">AI Investment Committee</span>
  </div>

  <!-- Headline -->
  <h1 style="font-family:'DM Serif Display',Georgia,serif;
             font-size:clamp(2.6rem,5.5vw,4.4rem);
             line-height:1.06;color:#dde4ec;
             margin:0 0 .9rem;max-width:720px;
             letter-spacing:-.03em;font-weight:400;">
    Should you build<br>
    <em style="color:#c9a84c;font-style:italic;">this startup?</em>
  </h1>

  <!-- Subline -->
  <p style="font-size:1.05rem;color:#6b7885;line-height:1.7;
            max-width:520px;margin:0 0 2rem;font-weight:300;">
    Paste your idea. Six AI agents debate market demand, competition, and risk.
    Get a <strong style="color:#dde4ec;font-weight:500;">BUILD&nbsp;·&nbsp;CAUTION&nbsp;·&nbsp;REJECT</strong>
    verdict with evidence in 90 seconds.
  </p>

  <!-- Feature pills -->
  <div style="display:flex;flex-wrap:wrap;gap:8px;">
    <div style="padding:5px 13px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);border-radius:99px;font-size:.78rem;color:#6b7885;letter-spacing:.01em;">6-agent pipeline</div>
    <div style="padding:5px 13px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);border-radius:99px;font-size:.78rem;color:#6b7885;letter-spacing:.01em;">Deterministic scoring</div>
    <div style="padding:5px 13px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);border-radius:99px;font-size:.78rem;color:#6b7885;letter-spacing:.01em;">5-scenario simulator</div>
    <div style="padding:5px 13px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);border-radius:99px;font-size:.78rem;color:#6b7885;letter-spacing:.01em;">PDF + Markdown export</div>
  </div>
</div>""")


# ── Input ─────────────────────────────────────────────────────────────────────

def render_input(err: Exception | None) -> tuple[str, bool]:
    left, right = st.columns([1.3, 0.7], gap="large")

    with left:
        with st.form("main_form", clear_on_submit=False):
            idea = st.text_area(
                "Startup idea",
                key="idea_input",
                height=140,
                max_chars=2000,
                placeholder="e.g.  An AI copilot that helps independent clinics turn doctor conversations into completed admin workflows — billing, referrals, notes — without manual entry.",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button(
                "Analyze with 6 Agents  →",
                type="primary",
                use_container_width=True,
                disabled=err is not None,
            )

    with right:
        html("""
<div style="padding:1.4rem 1.5rem;
            background:rgba(255,255,255,.025);
            border:1px solid rgba(255,255,255,.07);
            border-radius:18px;height:100%;
            position:relative;overflow:hidden;">
  <!-- subtle top accent -->
  <div style="position:absolute;top:0;left:1.5rem;right:1.5rem;height:1px;
              background:linear-gradient(90deg,transparent,rgba(201,168,76,.25),transparent);"></div>

  <div style="font-size:.62rem;color:#c9a84c;letter-spacing:.13em;text-transform:uppercase;
              font-weight:600;margin-bottom:1.1rem;">How it works</div>

  <div style="display:flex;flex-direction:column;gap:1rem;">
    <div style="display:flex;align-items:flex-start;gap:11px;">
      <div style="width:22px;height:22px;border-radius:7px;flex-shrink:0;
                  background:rgba(201,168,76,.1);border:1px solid rgba(201,168,76,.2);
                  display:flex;align-items:center;justify-content:center;
                  font-size:.68rem;color:#c9a84c;font-weight:700;">1</div>
      <div>
        <div style="font-size:.85rem;color:#dde4ec;font-weight:500;margin-bottom:2px;">Describe your idea</div>
        <div style="font-size:.76rem;color:#556070;line-height:1.45;">One sentence is enough</div>
      </div>
    </div>
    <div style="display:flex;align-items:flex-start;gap:11px;">
      <div style="width:22px;height:22px;border-radius:7px;flex-shrink:0;
                  background:rgba(201,168,76,.1);border:1px solid rgba(201,168,76,.2);
                  display:flex;align-items:center;justify-content:center;
                  font-size:.68rem;color:#c9a84c;font-weight:700;">2</div>
      <div>
        <div style="font-size:.85rem;color:#dde4ec;font-weight:500;margin-bottom:2px;">Six agents debate it</div>
        <div style="font-size:.76rem;color:#556070;line-height:1.45;">Market · Competitors · Risk · Decision</div>
      </div>
    </div>
    <div style="display:flex;align-items:flex-start;gap:11px;">
      <div style="width:22px;height:22px;border-radius:7px;flex-shrink:0;
                  background:rgba(201,168,76,.1);border:1px solid rgba(201,168,76,.2);
                  display:flex;align-items:center;justify-content:center;
                  font-size:.68rem;color:#c9a84c;font-weight:700;">3</div>
      <div>
        <div style="font-size:.85rem;color:#dde4ec;font-weight:500;margin-bottom:2px;">Get the verdict</div>
        <div style="font-size:.76rem;color:#556070;line-height:1.45;">BUILD · CAUTION · REJECT + score</div>
      </div>
    </div>
  </div>
</div>""")

    return idea, submitted


# ── Idle state ────────────────────────────────────────────────────────────────

def render_idle() -> None:
    url_hint = (
        f'<div style="margin-top:.8rem;"><a href="{DEPLOYMENT_URL}" target="_blank" '
        f'style="font-size:.82rem;color:#c9a84c;text-decoration:none;">'
        f'→ Open live app: {DEPLOYMENT_URL}</a></div>'
    ) if DEPLOYMENT_URL else ""
    html(f"""
<div style="padding:2.8rem;text-align:center;
            background:rgba(255,255,255,.012);
            border:1px dashed rgba(255,255,255,.055);
            border-radius:20px;margin-top:.5rem;
            position:relative;overflow:hidden;">
  <!-- ambient glow -->
  <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
              width:300px;height:200px;
              background:radial-gradient(ellipse,rgba(201,168,76,.05) 0%,transparent 70%);
              pointer-events:none;"></div>

  <div style="font-size:1.6rem;margin-bottom:.9rem;opacity:.5;position:relative;">◆</div>
  <div style="font-family:'DM Serif Display',Georgia,serif;font-size:1.15rem;
              color:#dde4ec;margin-bottom:.5rem;font-weight:400;letter-spacing:-.01em;
              position:relative;">Ready when you are</div>
  <p style="font-size:.83rem;color:#374049;max-width:380px;margin:0 auto;
            line-height:1.65;position:relative;">
    Paste a startup idea above and click Analyze. Six agents will debate it and return
    an investor-grade verdict in under 90 seconds.
  </p>
  {url_hint}
</div>""")


# ── Dashboard tab ─────────────────────────────────────────────────────────────

def _label_to_score(v: str, *, positive: bool) -> int:
    n = str(v).strip().lower()
    if positive:  return {"high": 78, "medium": 55, "low": 30}.get(n, 52)
    else:         return {"high": 74, "medium": 52, "low": 28}.get(n, 52)


def _clamp(v: int) -> int:
    return max(0, min(100, v))


def render_dashboard(result: ResearchRunResult) -> None:
    fd = result.final_brief.final_decision

    # resolve component scores
    demand_score = int(fd.get("demand_score") or _label_to_score(fd.get("market_demand", "Medium"), positive=True))
    comp_score   = int(fd.get("competition_score") or _label_to_score(fd.get("competition", "Medium"), positive=False))
    risk_score   = int(fd.get("risk_score") or _label_to_score(fd.get("risk", "Medium"), positive=False))
    source_count = sum(len(o.sources) for o in result.observations)

    left, right = st.columns([1, 1], gap="large")

    with left:
        section_label("Signal Analysis")
        signal_bar("Market Demand",         demand_score, positive=True)
        signal_bar("Competition Pressure",  comp_score,   positive=False)
        signal_bar("Execution Risk",        risk_score,   positive=False)

        findings = result.final_brief.key_findings[:4] or ["No key findings yet."]
        items_html = "".join(
            f'<li style="font-size:.86rem;color:#7a8694;line-height:1.6;margin-bottom:4px;">{html_escape(str(f))}</li>'
            for f in findings
        )
        html(f"""
<div style="margin-top:1.2rem;padding:1rem 1.1rem;background:rgba(255,255,255,.02);
            border:1px solid rgba(255,255,255,.06);border-radius:16px;">
  <div style="font-size:.72rem;color:#c9a84c;letter-spacing:.1em;text-transform:uppercase;margin-bottom:.6rem;">Key Findings</div>
  <ul style="margin:0;padding-left:1.1rem;">{items_html}</ul>
</div>""")

    with right:
        section_label("Agent Workflow")
        html(agent_pipeline_html(result.trace))
        st.caption(f"{source_count} sources · {len(result.related_memories)} memory hits · deterministic scoring")

    # ── What-if simulator ───────────────────────────────────────────────────────
    st.markdown("---")
    sim_col, scen_col = st.columns([0.85, 1.15], gap="large")

    with sim_col:
        section_label("What-If Simulator")
        html("""
<div style="font-family:'DM Serif Display',serif;font-size:1.15rem;color:#e8ecf0;margin-bottom:.3rem;">Stress-test the verdict live</div>
<p style="font-size:.84rem;color:#7a8694;margin-bottom:1rem;">Move market variables and watch the investment signal react.</p>""")

        d_adj = st.slider("Market Demand",  -25, 25, 0, 5, key="sim_d")
        c_adj = st.slider("Competition",    -25, 25, 0, 5, key="sim_c")
        r_adj = st.slider("Risk",           -25, 25, 0, 5, key="sim_r")

        sd = _clamp(demand_score + d_adj)
        sc = _clamp(comp_score   + c_adj)
        sr = _clamp(risk_score   + r_adj)
        sim_score   = _clamp(int(round(sd * .5 + (100 - sc) * .3 + (100 - sr) * .2)))

        if sim_score >= 72:   sv, sa = "Strong",   "#3ecf8e"
        elif sim_score >= 48: sv, sa = "Moderate", "#f59e0b"
        else:                 sv, sa = "Weak",     "#ef4444"
        sim_action = {"Strong":"BUILD","Moderate":"CAUTION","Weak":"REJECT"}[sv]

        html(f"""
<div style="padding:1.1rem 1.2rem;
            background:rgba(255,255,255,.02);
            border:1px solid rgba(255,255,255,.07);
            border-radius:14px;margin-top:.85rem;
            position:relative;overflow:hidden;">
  <!-- colour flash strip -->
  <div style="position:absolute;top:0;left:0;right:0;height:2px;
              background:linear-gradient(90deg,transparent,{sa}55,transparent);"></div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.65rem;">
    <span style="font-size:.72rem;color:#556070;text-transform:uppercase;letter-spacing:.08em;font-weight:600;">Simulated signal</span>
    <span style="font-size:1.55rem;font-family:'DM Serif Display',Georgia,serif;
                 color:{sa};line-height:1;letter-spacing:-.02em;">{sim_action}</span>
  </div>
  <div style="height:3px;background:rgba(255,255,255,.055);border-radius:99px;overflow:hidden;">
    <div style="height:100%;width:{sim_score}%;background:{sa};border-radius:99px;
                box-shadow:0 0 8px {sa}60;transition:width .3s ease;"></div>
  </div>
  <div style="font-size:.72rem;color:#556070;margin-top:.45rem;text-align:right;
              font-variant-numeric:tabular-nums;">{sim_score} / 100</div>
</div>""")

    with scen_col:
        section_label("Investor Scenario Studio — 5 Futures")
        html("""
<div style="font-family:'DM Serif Display',serif;font-size:1.15rem;color:#e8ecf0;margin-bottom:.3rem;">Bull · Base · Bear · Regulatory · Breakout</div>
<p style="font-size:.84rem;color:#7a8694;margin-bottom:1rem;">How the verdict shifts under each market condition.</p>""")
        scenarios = build_investor_scenarios(fd)
        render_scenario_cards(scenarios)


# ── Analysis tab ──────────────────────────────────────────────────────────────

def render_analysis(result: ResearchRunResult) -> None:
    market_obs = [o for o in result.observations if "competitor" not in f"{o.objective} {o.query}".lower()]
    comp_obs   = [o for o in result.observations if "competitor"     in f"{o.objective} {o.query}".lower()]

    m_col, c_col = st.columns(2, gap="large")

    def _section(col: Any, title: str, obs_list: list, summary: str) -> None:
        with col:
            section_label(title)
            html(f'<p style="font-size:.9rem;color:#7a8694;line-height:1.6;margin-bottom:1rem;">{escape(summary[:300])}</p>')
            pts: list[str] = []
            for o in obs_list:
                pts.extend(o.data_points[:2])
            for pt in pts[:5]:
                html(f'<div style="font-size:.82rem;color:#e8ecf0;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.04);">· {escape(str(pt))}</div>')

    _section(m_col, "Market Analysis",    market_obs, result.final_brief.market_analysis)
    _section(c_col, "Competitor Analysis", comp_obs,  result.final_brief.competitor_analysis)

    st.markdown("---")
    section_label("SWOT Analysis")
    sw = result.final_brief.swot
    if isinstance(sw, dict):
        render_swot(sw)


# ── Evidence tab ──────────────────────────────────────────────────────────────

def render_evidence(result: ResearchRunResult) -> None:
    section_label("Agent Execution Trace")
    stage_colors = {
        "planning":"#c9a84c","market_research":"#60a5fa","competitor_analysis":"#a78bfa",
        "evaluation":"#f59e0b","decision":"#3ecf8e","report":"#38bdf8","storage":"#7a8694",
    }
    for ev in result.trace:
        c = stage_colors.get(ev.stage, "#7a8694")
        with st.expander(f"[{ev.stage.upper()}]  {ev.title}", expanded=ev.stage in {"decision","report"}):
            html(f'<p style="font-size:.86rem;color:#7a8694;line-height:1.6;">{escape(ev.details)}</p>')
            if ev.metadata:
                st.json(ev.metadata)

    if result.observations:
        st.markdown("---")
        section_label("Sources")
        seen: set[str] = set()
        for obs in result.observations:
            for src in obs.sources[:3]:
                key = src.url or src.title
                if key in seen: continue
                seen.add(key)
                html(f"""
<div style="padding:6px 0;border-bottom:1px solid rgba(255,255,255,.04);">
  <a href="{escape(src.url)}" style="font-size:.84rem;color:#60a5fa;text-decoration:none;" target="_blank">{escape(src.title or src.url)}</a>
  <span style="font-size:.76rem;color:#404a56;margin-left:8px;">{escape(src.source)}</span>
</div>""")


# ── Data room tab ─────────────────────────────────────────────────────────────

def render_dataroom(result: ResearchRunResult) -> None:
    left, right = st.columns([1, 1], gap="large")
    structured = {
        "idea": result.final_brief.startup_idea,
        "market_analysis": result.final_brief.market_analysis,
        "competitor_analysis": result.final_brief.competitor_analysis,
        "swot": result.final_brief.swot,
        "final_decision": result.final_brief.final_decision,
        "scenario_analysis": build_investor_scenarios(result.final_brief.final_decision),
    }

    with left:
        section_label("Download Reports")
        dl1, dl2 = st.columns(2, gap="small")
        dl1.download_button("Markdown Report", data=result.final_markdown,
                            file_name=f"venturemind_{result.run_id}.md", mime="text/markdown",
                            use_container_width=True)
        try:
            pdf = generate_pdf_report(structured)
            dl2.download_button("PDF Report", data=pdf,
                                file_name=f"venturemind_{result.run_id}.pdf", mime="application/pdf",
                                use_container_width=True)
        except RuntimeError as exc:
            dl2.warning(str(exc))

        st.markdown("---")
        section_label("Recommended Actions")
        for act in result.final_brief.recommended_actions:
            html(f'<div style="font-size:.86rem;color:#7a8694;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.04);">→ {escape(str(act))}</div>')

    with right:
        section_label("Structured Output")
        with st.expander("JSON payload", expanded=False):
            st.json(structured)
        if result.related_memories:
            st.markdown("---")
            section_label("Memory Hits")
            for mem in result.related_memories:
                html(f"""
<div style="padding:.7rem .9rem;background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:12px;margin-bottom:.5rem;">
  <div style="font-size:.84rem;color:#e8ecf0;font-weight:500;">{escape(mem.user_question[:80])}</div>
  <div style="font-size:.76rem;color:#7a8694;margin-top:3px;">Similarity {mem.score:.2f} · Confidence {mem.confidence}/100</div>
</div>""")


# ── Results ───────────────────────────────────────────────────────────────────

def render_results(result: ResearchRunResult) -> None:
    verdict_slot = st.empty()
    render_verdict_card(result, verdict_slot)

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🔬 Analysis", "📋 Evidence", "🗂 Data Room"])
    with tab1: render_dashboard(result)
    with tab2: render_analysis(result)
    with tab3: render_evidence(result)
    with tab4: render_dataroom(result)


# ── QA ────────────────────────────────────────────────────────────────────────

def qa_run(result: ResearchRunResult) -> dict[str, Any]:
    total   = len(result.observations)
    failed  = sum(1 for o in result.observations if o.status != "completed")
    sources = sum(len(o.sources) for o in result.observations)
    try:    conf = int(result.evaluation.confidence)
    except (TypeError, ValueError, AttributeError): conf = 0
    status = "healthy"
    reasons: list[str] = []
    if total == 0 or sources == 0 or failed == total:
        status = "blocked"
        reasons.append("No evidence collected — verdict is fallback logic only.")
    elif failed:
        status = "degraded"
        reasons.append(f"{failed}/{total} research steps failed.")
    if sources < 3:
        if status == "healthy": status = "degraded"
        reasons.append("Fewer than 3 sources — confidence is low.")
    return {"status": status, "reasons": reasons, "source_count": sources, "confidence": conf}


# ── Main ──────────────────────────────────────────────────────────────────────

def html_escape(s: str) -> str:
    """Escape HTML entities in user-facing strings."""
    from html import escape as _e
    return _e(s)


def main() -> None:
    setup_page()
    st.session_state.setdefault("idea_input", "")
    st.session_state.setdefault("latest_result", None)

    err: Exception | None = None
    resolved: Settings | None = None
    try:
        resolved = Settings.from_env()
    except Exception as exc:
        err = exc

    loops, results = render_sidebar(resolved, err)
    render_hero()
    idea, submitted = render_input(err)
    st.markdown("---")

    exec_label    = st.empty()
    pipeline_slot = st.empty()
    progress_slot = st.empty()
    status_slot   = st.empty()
    trace_slot    = st.empty()

    if not submitted and not st.session_state.get("latest_result"):
        html('<div style="font-size:.72rem;color:#404a56;letter-spacing:.1em;text-transform:uppercase;margin-bottom:.6rem;">Agent Pipeline</div>', container=exec_label)
        html(agent_pipeline_html([]), container=pipeline_slot)

    if submitted:
        if not idea.strip():
            st.warning("Describe a startup idea to analyze.")
        elif resolved is None:
            st.error("Configure api.env before running analysis.")
        else:
            # ── Per-session rate limiting ──
            if "analysis_count" not in st.session_state:
                st.session_state["analysis_count"] = 0
                st.session_state["first_analysis_time"] = time.time()

            # Reset counter every hour
            if time.time() - st.session_state["first_analysis_time"] > 3600:
                st.session_state["analysis_count"] = 0
                st.session_state["first_analysis_time"] = time.time()

            if st.session_state["analysis_count"] >= 10:
                st.error("Rate limit reached. Please try again later (max 10 analyses per hour).")
                st.stop()

            st.session_state["analysis_count"] += 1

            st.session_state["latest_result"] = None
            html("""<div style="font-size:.72rem;color:#c9a84c;letter-spacing:.1em;text-transform:uppercase;margin-bottom:.6rem;">
                <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#c9a84c;vertical-align:middle;margin-right:8px;animation:pulse-dot 1.4s ease-in-out infinite;"></span>
                Live Execution</div>""", container=exec_label)

            runtime = replace(resolved, max_reasoning_loops=loops, search_results=results)
            orchestrator = AgentathonOrchestrator(settings=runtime)
            live_events: list[TraceEvent] = []
            progress_val = {"v": 0.02}
            progress_slot.progress(0.02)
            html(agent_pipeline_html([]), container=pipeline_slot)

            def on_event(ev: TraceEvent) -> None:
                live_events.append(ev)
                progress_val["v"] = max(progress_val["v"], STAGE_PROGRESS.get(ev.stage, 0.5))
                render_live_panel(pipeline_slot, progress_slot, status_slot, trace_slot,
                                  live_events, progress_val["v"])

            with st.spinner(""):
                try:
                    result = orchestrator.run(idea, event_callback=on_event)
                except Exception as exc:
                    progress_slot.empty()
                    status_slot.empty()
                    st.error(f"Analysis failed: {exc}")
                    if "1010" in str(exc) or "Cloudflare" in str(exc):
                        st.info("Groq blocked the request. Confirm your API key in Groq Console and retry.")
                else:
                    progress_slot.progress(1.0)
                    qa = qa_run(result)
                    st.session_state["latest_result"] = result
                    trace_slot.empty()
                    status_slot.empty()
                    if qa["status"] == "healthy":
                        st.success("Analysis complete.")
                    else:
                        st.warning("Analysis complete — evidence quality is limited. " + " ".join(qa["reasons"]))

    latest = st.session_state.get("latest_result")
    if latest:
        st.markdown("---")
        render_results(latest)
    elif not submitted:
        render_idle()


if __name__ == "__main__":
    main()
