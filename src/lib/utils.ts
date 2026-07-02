import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Verdict, ActionLabel, AgentStage, ScenarioCard, AnalysisResult } from "@/types";
import { VERDICT_CONFIG, STAGE_ORDER } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ── Verdict utilities ─────────────────────────────────────────────────────────

export function getVerdictConfig(verdict: Verdict) {
  return VERDICT_CONFIG[verdict] ?? VERDICT_CONFIG.Moderate;
}

export function verdictToAction(verdict: Verdict): ActionLabel {
  return VERDICT_CONFIG[verdict]?.label ?? "CAUTION";
}

export function scoreToVerdict(score: number): Verdict {
  if (score >= 65) return "Strong";
  if (score >= 40) return "Moderate";
  return "Weak";
}

// ── Score arc calculations ────────────────────────────────────────────────────

export function scoreArcProps(score: number, radius: number) {
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (score / 100) * circumference;
  return { circumference, dashOffset };
}

// ── Stage utilities ───────────────────────────────────────────────────────────

export function stageToProgress(stage: AgentStage | null): number {
  if (!stage) return 0;
  const idx = STAGE_ORDER.indexOf(stage);
  if (idx === -1) return 0;
  return Math.round(((idx + 1) / STAGE_ORDER.length) * 100);
}

export function isStageComplete(stage: AgentStage, activeStage: AgentStage | null): boolean {
  if (!activeStage) return false;
  const activeIdx = STAGE_ORDER.indexOf(activeStage);
  const stageIdx  = STAGE_ORDER.indexOf(stage);
  return stageIdx < activeIdx;
}

export function isStageLive(stage: AgentStage, activeStage: AgentStage | null): boolean {
  return stage === activeStage;
}

// ── Formatting utilities ──────────────────────────────────────────────────────

export function formatProcessingTime(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function formatRelativeTime(timestamp: number): string {
  const diff = Date.now() - timestamp;
  if (diff < 60_000) return "just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return new Date(timestamp).toLocaleDateString();
}

export function clampText(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen).trimEnd() + "…";
}

// ── Mock result (demo mode fallback) ─────────────────────────────────────────

export function generateMockResult(idea: string): AnalysisResult {
  // Deterministic-ish score seeded from idea length so repeated calls are stable
  const seed   = idea.length % 30;
  const score  = 52 + seed;                        // 52–81 range
  const verdict: Verdict     = scoreToVerdict(score);
  const action: ActionLabel  = verdictToAction(verdict);
  const confidence           = Math.min(88, 62 + seed);

  return {
    id:                 `demo_${Date.now()}`,
    idea,
    timestamp:          Date.now(),
    processing_time_ms: 4_200,
    trace:              [],                         // page.tsx injects animated trace
    scenarios:          buildScenarios(score),
    final_brief: {
      final_decision: {
        final_verdict:    verdict,
        action,
        score,
        confidence,
        risk:             score >= 65 ? "Low"    : score >= 45 ? "Medium" : "High",
        market_demand:    score >= 65 ? "High"   : score >= 45 ? "Medium" : "Low",
        competition:      score >= 65 ? "Medium" : "High",
        reasoning:
          `Demo mode — real pipeline not connected. ` +
          `Illustrative score ${score}/100 based on typical validation heuristics. ` +
          `Connect NEXT_PUBLIC_API_URL for live AI-powered analysis.`,
        demand_score:      Math.min(100, score + 8),
        competition_score: Math.max(0,   score - 10),
        risk_score:        Math.max(0,   score - 5),
      },
      executive_summary:
        `This is a demo analysis for "${idea.slice(0, 60)}${idea.length > 60 ? "…" : ""}". ` +
        `Connect the VentureMind backend (NEXT_PUBLIC_API_URL) to receive a real verdict ` +
        `powered by live market data and the 6-agent AI pipeline.`,
      market_analysis:
        "Demo mode: Market agent would analyse search-volume trends, funding signals, and " +
        "buyer-persona evidence from live web sources. Score reflects a moderate demand signal.",
      competitor_analysis:
        "Demo mode: Competitor agent would map direct and indirect rivals, assess differentiation " +
        "potential, and flag positioning pressure from incumbents.",
      key_findings: [
        "Demo mode is active — connect NEXT_PUBLIC_API_URL to run the live 6-agent pipeline.",
        "The scoring formula is: demand × 0.5 + competition_penalty × 0.3 + risk_penalty × 0.2.",
        "Live analysis searches real-time web sources via Serper and reasons with Groq LLaMA 3.3.",
        "Results include a PDF-exportable investor memo and 5-scenario stress-test.",
      ],
      swot: {
        strengths:     ["Clear problem framing", "Identifiable target user segment"],
        weaknesses:    ["Market demand not yet validated with live data", "Demo mode — real evidence unavailable"],
        opportunities: ["Validate with 10 user interviews before committing to build", "Narrow wedge positioning can reduce competition pressure"],
        threats:       ["Incumbents may already serve this need", "Limited evidence depth in demo mode"],
      },
    },
  };
}

// ── Scenario utilities ────────────────────────────────────────────────────────

export function buildScenarios(baseScore: number): ScenarioCard[] {
  return [
    {
      id: "bull",
      name: "Bull Case",
      icon: "▲",
      summary: "Faster adoption, fragmented competition, low friction entry",
      score: Math.min(100, baseScore + 14),
      delta: +14,
      verdict: scoreToVerdict(Math.min(100, baseScore + 14)),
      implication: "Raise a pre-seed and move fast — the window is open.",
    },
    {
      id: "base",
      name: "Base Case",
      icon: "◆",
      summary: "Current evidence conditions — most likely scenario",
      score: baseScore,
      delta: 0,
      verdict: scoreToVerdict(baseScore),
      implication: "Execute with discipline. Focus on the top demand signal.",
    },
    {
      id: "bear",
      name: "Bear Case",
      icon: "▼",
      summary: "Slow traction, incumbent pushback, harder execution",
      score: Math.max(0, baseScore - 18),
      delta: -18,
      verdict: scoreToVerdict(Math.max(0, baseScore - 18)),
      implication: "Validate one segment deeply before scaling spend.",
    },
    {
      id: "regulatory",
      name: "Regulatory Headwind",
      icon: "⚖",
      summary: "Sector-specific compliance burden increases cost & time",
      score: Math.max(0, baseScore - 11),
      delta: -11,
      verdict: scoreToVerdict(Math.max(0, baseScore - 11)),
      implication: "Budget 6 months and legal counsel before GTM.",
    },
    {
      id: "breakout",
      name: "Breakout Timing",
      icon: "⚡",
      summary: "Platform shift or macro event accelerates demand sharply",
      score: Math.min(100, baseScore + 7),
      delta: +7,
      verdict: scoreToVerdict(Math.min(100, baseScore + 7)),
      implication: "Position as the category-defining solution and move to Series A storytelling now.",
    },
  ];
}