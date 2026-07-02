// ── Core domain types ──────────────────────────────────────────────────────────

export type Verdict = "Strong" | "Moderate" | "Weak";
export type ActionLabel = "BUILD" | "CAUTION" | "REJECT";
export type AgentStage =
  | "planning"
  | "market_research"
  | "competitor_analysis"
  | "evaluation"
  | "decision"
  | "report"
  | "complete";

export type AgentStatus = "idle" | "active" | "done" | "error";

export interface Agent {
  id: string;
  num: string;
  name: string;
  description: string;
  stage: AgentStage;
  icon: string;
  status: AgentStatus;
}

export interface TraceEvent {
  id: string;
  stage: AgentStage;
  title: string;
  details: string;
  timestamp: number;
}

export interface ScenarioCard {
  id: string;
  name: string;
  icon: string;
  summary: string;
  score: number;
  delta: number;
  verdict: Verdict;
  implication: string;
}

export interface FinalDecision {
  final_verdict: Verdict;
  action: ActionLabel;
  score: number;
  confidence: number;
  risk: "Low" | "Medium" | "High";
  market_demand: "Low" | "Medium" | "High";
  competition: "Low" | "Medium" | "High";
  reasoning: string;
  demand_score: number;
  competition_score: number;
  risk_score: number;
}

export interface FinalBrief {
  final_decision: FinalDecision;
  swot: {
    strengths: string[];
    weaknesses: string[];
    opportunities: string[];
    threats: string[];
  };
  key_findings: string[];
  market_analysis: string;
  competitor_analysis: string;
  executive_summary: string;
}

export interface AnalysisResult {
  id: string;
  idea: string;
  timestamp: number;
  final_brief: FinalBrief;
  scenarios: ScenarioCard[];
  trace: TraceEvent[];
  processing_time_ms: number;
}

export interface AnalysisState {
  status: "idle" | "analyzing" | "done" | "error";
  progress: number;
  currentStage: AgentStage | null;
  events: TraceEvent[];
  result: AnalysisResult | null;
  error: string | null;
}

// ── UI utility types ──────────────────────────────────────────────────────────

export interface VerdictConfig {
  label: ActionLabel;
  color: string;
  bgColor: string;
  borderColor: string;
  gradientFrom: string;
  gradientTo: string;
  glowColor: string;
}

export const VERDICT_CONFIG: Record<Verdict, VerdictConfig> = {
  Strong: {
    label: "BUILD",
    color: "#22c55e",
    bgColor: "rgba(34,197,94,0.06)",
    borderColor: "rgba(34,197,94,0.2)",
    gradientFrom: "#0a1f12",
    gradientTo: "#041508",
    glowColor: "rgba(34,197,94,0.15)",
  },
  Moderate: {
    label: "CAUTION",
    color: "#f59e0b",
    bgColor: "rgba(245,158,11,0.06)",
    borderColor: "rgba(245,158,11,0.2)",
    gradientFrom: "#1a1200",
    gradientTo: "#0d0900",
    glowColor: "rgba(245,158,11,0.15)",
  },
  Weak: {
    label: "REJECT",
    color: "#ef4444",
    bgColor: "rgba(239,68,68,0.06)",
    borderColor: "rgba(239,68,68,0.2)",
    gradientFrom: "#1a0606",
    gradientTo: "#0d0303",
    glowColor: "rgba(239,68,68,0.15)",
  },
};

export const AGENT_DEFINITIONS: Agent[] = [
  { id: "01", num: "01", name: "Planner",    description: "Builds research plan",      stage: "planning",             icon: "◈", status: "idle" },
  { id: "02", num: "02", name: "Market",     description: "Demand & timing signals",   stage: "market_research",      icon: "◎", status: "idle" },
  { id: "03", num: "03", name: "Competitor", description: "Maps rivals & pressure",    stage: "competitor_analysis",  icon: "◉", status: "idle" },
  { id: "04", num: "04", name: "Evaluator",  description: "Quality gate & reflection", stage: "evaluation",           icon: "◐", status: "idle" },
  { id: "05", num: "05", name: "Decision",   description: "Deterministic scoring",     stage: "decision",             icon: "◆", status: "idle" },
  { id: "06", num: "06", name: "Report",     description: "Packages the verdict",      stage: "report",               icon: "◇", status: "idle" },
];

export const EXAMPLE_IDEAS = [
  "Healthcare startup that reduces clinic admin workload with voice-to-workflow AI",
  "B2B SaaS platform that auto-generates legal contracts from plain-English descriptions",
  "Subscription marketplace for independent game studios targeting mid-core gamers",
  "AI-powered personal finance coach for Gen Z first-time earners",
  "No-code workflow builder for operations teams in e-commerce brands",
];

export const STAGE_ORDER: AgentStage[] = [
  "planning",
  "market_research",
  "competitor_analysis",
  "evaluation",
  "decision",
  "report",
];
