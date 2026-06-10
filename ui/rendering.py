"""
VentureMind AI — UI rendering primitives.
All heavy HTML/SVG generation lives here; app.py stays thin.
"""
from __future__ import annotations
from html import escape
from typing import Any
import streamlit as st

from core.models import ResearchRunResult, ToolObservation, TraceEvent
from utils.scenario_engine import build_investor_scenarios

# ── Colour helpers ─────────────────────────────────────────────────────────────

def verdict_accent(verdict: str) -> str:
    return {"Strong": "#22c55e", "Moderate": "#f59e0b", "Weak": "#ef4444"}.get(verdict, "#f59e0b")

def verdict_bg(verdict: str) -> str:
    return {
        "Strong":   "linear-gradient(160deg,#020d06 0%,#041a0c 60%,#020d06 100%)",
        "Moderate": "linear-gradient(160deg,#0d0800 0%,#1c1200 60%,#0d0800 100%)",
        "Weak":     "linear-gradient(160deg,#0d0202 0%,#1c0404 60%,#0d0202 100%)",
    }.get(verdict, "linear-gradient(160deg,#0d0800 0%,#1c1200 60%,#0d0800 100%)")

def verdict_glow(verdict: str) -> str:
    return {"Strong": "#22c55e", "Moderate": "#f59e0b", "Weak": "#ef4444"}.get(verdict, "#f59e0b")

def action_label(verdict: str) -> str:
    return {"Strong": "BUILD", "Moderate": "CAUTION", "Weak": "REJECT"}.get(verdict, "CAUTION")

# ── html() helper ─────────────────────────────────────────────────────────────

def html(markup: str, *, container: Any = None) -> None:
    target = container or st
    renderer = getattr(target, "html", None)
    if callable(renderer):
        renderer(markup)
    else:
        target.markdown(markup, unsafe_allow_html=True)

# ── Agent pipeline grid ───────────────────────────────────────────────────────

AGENT_META = [
    ("01", "Planner",    "Builds research plan",       "planning"),
    ("02", "Market",     "Demand & timing signals",    "market_research"),
    ("03", "Competitor", "Maps rivals & pressure",     "competitor_analysis"),
    ("04", "Evaluator",  "Quality gate & reflection",  "evaluation"),
    ("05", "Decision",   "Deterministic scoring",      "decision"),
    ("06", "Report",     "Packages the verdict",       "report"),
]

_STAGE_ORDER = ["planning", "market_research", "competitor_analysis",
                "evaluation", "decision", "report"]

_AGENT_ICONS = {
    "planning": "◈", "market_research": "◎", "competitor_analysis": "◉",
    "evaluation": "◐", "decision": "◆", "report": "◇",
}

def agent_pipeline_html(events: list[TraceEvent]) -> str:
    active = {e.stage for e in events}
    active_idx = 0
    for i, s in enumerate(_STAGE_ORDER):
        if s in active:
            active_idx = i

    cards = []
    for i, (num, name, desc, stage) in enumerate(AGENT_META):
        done = stage in active and stage != _STAGE_ORDER[active_idx]
        live = stage == _STAGE_ORDER[active_idx] and stage in active
        if i < active_idx and not done:
            done = True

        icon = _AGENT_ICONS.get(stage, "·")

        if done:
            dot, label = "#22c55e", "Done"
            card_bg     = "rgba(34,197,94,.06)"
            card_border = "rgba(34,197,94,.2)"
            num_color   = "#22c55e"
            pulse = ""
        elif live:
            dot, label = "#c9a84c", "Live"
            card_bg     = "rgba(201,168,76,.07)"
            card_border = "rgba(201,168,76,.28)"
            num_color   = "#c9a84c"
            pulse = "animation:pulse-dot 1.4s ease-in-out infinite;"
        else:
            dot, label = "#2e3740", "Queue"
            card_bg     = "rgba(255,255,255,.018)"
            card_border = "rgba(255,255,255,.055)"
            num_color   = "#404a56"
            pulse = ""

        status_dot = f'<div style="width:5px;height:5px;border-radius:50%;background:{dot};{pulse}flex-shrink:0;"></div>'

        cards.append(f"""
<div style="padding:.8rem .85rem;background:{card_bg};border:1px solid {card_border};
            border-radius:12px;transition:all .25s;position:relative;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:2px;background:{card_border};"></div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem;">
    <span style="font-size:.62rem;color:{num_color};font-weight:600;letter-spacing:.08em;">{escape(num)}</span>
    <div style="display:flex;align-items:center;gap:4px;">
      {status_dot}
      <span style="font-size:.62rem;color:{dot};letter-spacing:.05em;text-transform:uppercase;">{label}</span>
    </div>
  </div>
  <div style="font-size:.8rem;font-weight:600;color:#e8ecf0;margin-bottom:2px;letter-spacing:-.01em;">{escape(name)}</div>
  <div style="font-size:.7rem;color:#556070;line-height:1.4;">{escape(desc)}</div>
</div>""")

    return (
        '<div style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:6px;">'
        + "".join(cards) + "</div>"
    )


# ── Score arc SVG ─────────────────────────────────────────────────────────────

def score_arc_svg(score: int, accent: str, *, size: int = 140) -> str:
    r = size // 2 - 12
    circ = 2 * 3.14159 * r
    dash = (score / 100) * circ
    cx = cy = size // 2
    # track segments for a more refined look
    return f"""
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="overflow:visible;">
  <defs>
    <filter id="arc-glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none"
          stroke="rgba(255,255,255,.055)" stroke-width="7"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none"
          stroke="{accent}" stroke-width="7"
          stroke-dasharray="{dash:.1f} {circ - dash:.1f}"
          stroke-linecap="round"
          filter="url(#arc-glow)"
          transform="rotate(-90 {cx} {cy})"/>
  <text x="{cx}" y="{cy - 7}" text-anchor="middle"
        font-family="DM Serif Display,Georgia,serif"
        font-size="26" font-weight="400" fill="{accent}">{score}</text>
  <text x="{cx}" y="{cy + 13}" text-anchor="middle"
        font-family="DM Sans,system-ui,sans-serif"
        font-size="10" fill="rgba(232,236,240,.38)">/100</text>
</svg>"""


# ── Verdict card ──────────────────────────────────────────────────────────────

def render_verdict_card(result: ResearchRunResult, slot: Any) -> None:
    fd        = result.final_brief.final_decision
    verdict   = str(fd.get("final_verdict", "Moderate"))
    score     = int(fd.get("score", 0))
    conf      = int(fd.get("confidence", 0))
    risk      = str(fd.get("risk", "Medium"))
    demand    = str(fd.get("market_demand", "Medium"))
    comp      = str(fd.get("competition", "Medium"))
    action    = str(fd.get("action", action_label(verdict)))
    reasoning = str(fd.get("reasoning", ""))[:280]
    sources   = sum(len(o.sources) for o in result.observations)

    accent = verdict_accent(verdict)
    bg     = verdict_bg(verdict)
    arc    = score_arc_svg(score, accent)

    # pill colors
    pill_bg     = "rgba(255,255,255,.04)"
    pill_border = "rgba(255,255,255,.09)"

    html(f"""
<div style="animation:verdict-reveal .55s cubic-bezier(.22,.68,0,1.25) both;
            background:{bg};
            border:1px solid {accent}28;
            border-radius:24px;
            padding:2rem 2.2rem;
            margin-bottom:1.5rem;
            position:relative;overflow:hidden;">
  <!-- ambient glow blobs -->
  <div style="position:absolute;top:-80px;right:-80px;width:260px;height:260px;
              background:radial-gradient(circle,{accent}14 0%,transparent 65%);
              pointer-events:none;"></div>
  <div style="position:absolute;bottom:-60px;left:-40px;width:180px;height:180px;
              background:radial-gradient(circle,{accent}09 0%,transparent 65%);
              pointer-events:none;"></div>

  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1.5rem;position:relative;">

    <!-- Left: action + reasoning -->
    <div style="flex:1;min-width:240px;">
      <div style="display:inline-flex;align-items:center;gap:7px;
                  background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.09);
                  border-radius:99px;padding:3px 12px;margin-bottom:1rem;">
        <span style="width:5px;height:5px;border-radius:50%;background:{accent};
                     animation:pulse-dot 2.5s ease-in-out infinite;flex-shrink:0;"></span>
        <span style="font-size:.65rem;color:{accent};letter-spacing:.12em;font-weight:600;text-transform:uppercase;">Final Investor Signal</span>
      </div>
      <div style="font-family:'DM Serif Display',Georgia,serif;
                  font-size:clamp(3rem,6.5vw,4.8rem);
                  color:{accent};line-height:.92;
                  margin-bottom:.9rem;
                  letter-spacing:-.02em;
                  animation:score-count .45s ease both .08s;">{escape(action)}</div>
      <p style="font-size:.93rem;color:rgba(232,236,240,.75);line-height:1.68;
                max-width:500px;margin:0;font-weight:300;">{escape(reasoning)}</p>
    </div>

    <!-- Right: score arc + confidence -->
    <div style="text-align:center;padding:1.25rem 1.6rem;
                background:rgba(255,255,255,.03);
                border:1px solid rgba(255,255,255,.07);
                border-radius:18px;min-width:160px;
                backdrop-filter:blur(4px);">
      {arc}
      <div style="font-size:.72rem;color:rgba(232,236,240,.42);margin-top:.4rem;letter-spacing:.02em;">
        {conf}% confidence
      </div>
      <div style="font-size:.72rem;color:rgba(232,236,240,.3);margin-top:2px;">
        {escape(risk)} risk
      </div>
    </div>
  </div>

  <!-- Bottom pill row -->
  <div style="display:flex;flex-wrap:wrap;gap:7px;margin-top:1.4rem;padding-top:1.1rem;
              border-top:1px solid rgba(255,255,255,.055);position:relative;">
    <div style="padding:4px 13px;border-radius:99px;background:{pill_bg};border:1px solid {pill_border};
                font-size:.76rem;color:rgba(232,236,240,.6);">
      Demand <strong style="color:#e8ecf0;font-weight:500;">{escape(demand)}</strong>
    </div>
    <div style="padding:4px 13px;border-radius:99px;background:{pill_bg};border:1px solid {pill_border};
                font-size:.76rem;color:rgba(232,236,240,.6);">
      Competition <strong style="color:#e8ecf0;font-weight:500;">{escape(comp)}</strong>
    </div>
    <div style="padding:4px 13px;border-radius:99px;background:{pill_bg};border:1px solid {pill_border};
                font-size:.76rem;color:rgba(232,236,240,.6);">
      <strong style="color:#e8ecf0;font-weight:500;">{sources}</strong> sources
    </div>
    <div style="padding:4px 13px;border-radius:99px;background:{pill_bg};border:1px solid {pill_border};
                font-size:.76rem;color:rgba(232,236,240,.6);">
      6-agent pipeline
    </div>
  </div>
</div>""", container=slot)


# ── Signal bar ────────────────────────────────────────────────────────────────

def signal_bar(label: str, value: int, *, positive: bool, container: Any = None) -> None:
    if positive:
        color = "#22c55e" if value >= 70 else "#f59e0b" if value >= 40 else "#ef4444"
    else:
        color = "#ef4444" if value >= 70 else "#f59e0b" if value >= 40 else "#22c55e"

    # subtle track glow matching bar color
    html(f"""
<div style="margin-bottom:1rem;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
    <span style="font-size:.8rem;color:#7a8694;letter-spacing:.01em;">{escape(label)}</span>
    <span style="font-size:.8rem;font-weight:600;color:{color};font-variant-numeric:tabular-nums;">{value}</span>
  </div>
  <div style="height:3px;background:rgba(255,255,255,.055);border-radius:99px;overflow:hidden;">
    <div style="height:100%;width:{value}%;background:{color};border-radius:99px;
                box-shadow:0 0 8px {color}60;transition:width .4s ease;"></div>
  </div>
</div>""", container=container)


# ── Scenario cards ────────────────────────────────────────────────────────────

def render_scenario_cards(scenarios: list[dict[str, Any]], container: Any = None) -> None:
    for sc in scenarios:
        delta  = int(sc.get("delta", 0))
        score  = int(sc.get("score", 0))
        v      = str(sc.get("verdict", "Moderate"))
        accent = verdict_accent(v)
        pfx    = "+" if delta > 0 else ""
        dc     = "#22c55e" if delta > 0 else "#ef4444" if delta < 0 else "#556070"
        icon   = escape(str(sc.get("icon", "◆")))
        impl   = escape(str(sc.get("implication", "")))
        name   = escape(str(sc.get("name", "")))
        summary = escape(str(sc.get("summary", ""))[:80])

        html(f"""
<div style="padding:.85rem 1rem;
            background:rgba(255,255,255,.018);
            border:1px solid rgba(255,255,255,.07);
            border-radius:12px;margin-bottom:.5rem;
            transition:border-color .2s, background .2s;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;">
    <div style="flex:1;min-width:0;">
      <div style="display:flex;align-items:center;gap:7px;margin-bottom:4px;">
        <span style="font-size:.9rem;opacity:.85;">{icon}</span>
        <span style="font-size:.85rem;font-weight:600;color:#dde4ec;letter-spacing:-.01em;">{name}</span>
      </div>
      <div style="font-size:.75rem;color:#556070;margin-bottom:3px;line-height:1.4;">{summary}</div>
      <div style="font-size:.72rem;color:rgba(201,168,76,.75);font-style:italic;line-height:1.4;">{impl[:90]}</div>
    </div>
    <div style="text-align:right;flex-shrink:0;">
      <div style="font-family:'DM Serif Display',Georgia,serif;font-size:1.55rem;color:{accent};line-height:1;">{score}</div>
      <div style="font-size:.68rem;color:{dc};font-weight:600;margin-top:2px;">{pfx}{delta}</div>
    </div>
  </div>
</div>""", container=container)


# ── Live execution panel ──────────────────────────────────────────────────────

def render_live_panel(
    pipeline_slot: Any,
    progress_slot: Any,
    status_slot: Any,
    trace_slot: Any,
    events: list[TraceEvent],
    progress_val: float,
) -> None:
    html(agent_pipeline_html(events), container=pipeline_slot)
    progress_slot.progress(progress_val)

    if not events:
        return

    latest = events[-1]
    html(f"""
<div style="margin-top:.5rem;display:flex;align-items:center;gap:8px;">
  <div style="width:5px;height:5px;border-radius:50%;background:#c9a84c;
              animation:pulse-dot 1.4s ease-in-out infinite;flex-shrink:0;"></div>
  <span style="font-size:.82rem;color:#c9a84c;font-weight:500;letter-spacing:.01em;">{escape(latest.title)}</span>
</div>""", container=status_slot)

    stage_icons = {
        "planning": "◈", "market_research": "◎", "competitor_analysis": "◉",
        "evaluation": "◐", "decision": "◆", "report": "◇", "storage": "○", "memory": "◌",
    }
    stage_colors = {
        "planning": "#c9a84c", "market_research": "#60a5fa",
        "competitor_analysis": "#a78bfa", "evaluation": "#f59e0b",
        "decision": "#22c55e", "report": "#38bdf8", "storage": "#556070",
    }
    trace_rows = "".join(
        f"""<div style="display:flex;gap:10px;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.038);">
          <div style="font-size:.82rem;color:{stage_colors.get(e.stage,'#556070')};flex-shrink:0;width:16px;margin-top:1px;">{stage_icons.get(e.stage,"·")}</div>
          <div style="min-width:0;">
            <div style="font-size:.79rem;color:#dde4ec;font-weight:500;margin-bottom:1px;">{escape(e.title)}</div>
            <div style="font-size:.72rem;color:#556070;line-height:1.4;">{escape(e.details[:110])}{"…" if len(e.details)>110 else ""}</div>
          </div>
        </div>"""
        for e in events[-4:]
    )
    html(f"""
<div style="background:rgba(255,255,255,.018);border:1px solid rgba(255,255,255,.065);
            border-radius:12px;padding:.8rem 1rem;margin-top:.75rem;">
  <div style="font-size:.62rem;color:#404a56;letter-spacing:.1em;text-transform:uppercase;
              margin-bottom:.5rem;font-weight:600;">Live trace</div>
  {trace_rows}
</div>""", container=trace_slot)


# ── SWOT grid ─────────────────────────────────────────────────────────────────

def render_swot(swot: dict[str, list[str]]) -> None:
    cols = st.columns(4, gap="small")
    swot_meta = [
        ("Strengths",     swot.get("strengths",    []), "#22c55e", "rgba(34,197,94,.08)",  "rgba(34,197,94,.18)"),
        ("Weaknesses",    swot.get("weaknesses",   []), "#ef4444", "rgba(239,68,68,.07)",  "rgba(239,68,68,.18)"),
        ("Opportunities", swot.get("opportunities",[]), "#60a5fa", "rgba(96,165,250,.07)", "rgba(96,165,250,.18)"),
        ("Threats",       swot.get("threats",      []), "#f59e0b", "rgba(245,158,11,.07)", "rgba(245,158,11,.18)"),
    ]
    for col, (label, items, color, bg, top_c) in zip(cols, swot_meta):
        with col:
            items_html = "".join(
                f'<li style="font-size:.77rem;color:#7a8694;line-height:1.55;margin-bottom:4px;">{escape(str(it))}</li>'
                for it in (items or ["None surfaced."])
            )
            html(f"""
<div style="padding:.9rem 1rem;background:{bg};
            border:1px solid {top_c};
            border-radius:12px;height:100%;">
  <div style="font-size:.65rem;color:{color};letter-spacing:.1em;
              text-transform:uppercase;font-weight:600;margin-bottom:.55rem;">{escape(label)}</div>
  <ul style="margin:0;padding-left:1rem;">{items_html}</ul>
</div>""")


# ── Section label helper ──────────────────────────────────────────────────────

def section_label(text: str, container: Any = None) -> None:
    html(
        f'<div style="font-size:.65rem;color:#c9a84c;letter-spacing:.12em;'
        f'text-transform:uppercase;margin-bottom:.55rem;font-weight:600;">{escape(text)}</div>',
        container=container,
    )
