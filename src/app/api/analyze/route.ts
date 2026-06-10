import { NextResponse } from "next/server";
import { buildScenarios, scoreToVerdict, verdictToAction } from "@/lib/utils";
import type { ActionLabel, AgentStage, AnalysisResult, TraceEvent, Verdict } from "@/types";

export const runtime = "nodejs";
export const maxDuration = 120; // Vercel: allow up to 2 min for AI pipeline

/* ── Rate limiting ─────────────────────────────────────────────────────────── */

const ipRequestMap = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT = 10;
const RATE_WINDOW_MS = 60 * 60 * 1000;

function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const entry = ipRequestMap.get(ip);
  if (!entry || now > entry.resetTime) {
    ipRequestMap.set(ip, { count: 1, resetTime: now + RATE_WINDOW_MS });
    return true;
  }
  if (entry.count >= RATE_LIMIT) return false;
  entry.count++;
  return true;
}

/* ── Type helpers ──────────────────────────────────────────────────────────── */

type JsonRecord = Record<string, unknown>;

const STAGE_MAP: Record<string, AgentStage> = {
  intake: "planning", memory: "planning", planning: "planning",
  market_research: "market_research", competitor_analysis: "competitor_analysis",
  evaluation: "evaluation", decision: "decision", report: "report",
  storage: "complete", complete: "complete",
};

function asRecord(value: unknown): JsonRecord {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as JsonRecord) : {};
}
function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}
function asNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}
function clamp(value: number, min = 0, max = 100): number {
  return Math.max(min, Math.min(max, Math.round(value)));
}
function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map(item => String(item)).filter(Boolean) : [];
}
function normalizeVerdict(value: unknown, score: number): Verdict {
  const raw = asString(value).toLowerCase();
  if (raw === "build" || raw === "strong") return "Strong";
  if (raw === "caution" || raw === "moderate") return "Moderate";
  if (raw === "reject" || raw === "weak") return "Weak";
  return scoreToVerdict(score);
}
function normalizeAction(value: unknown, verdict: Verdict): ActionLabel {
  const raw = asString(value).toUpperCase();
  if (raw === "BUILD" || raw === "CAUTION" || raw === "REJECT") return raw;
  return verdictToAction(verdict);
}
function normalizeLabel(value: unknown, fallback: "Low" | "Medium" | "High") {
  const raw = asString(value, fallback);
  if (raw === "Low" || raw === "Medium" || raw === "High") return raw;
  return fallback;
}
function normalizeTrace(value: unknown): TraceEvent[] {
  if (!Array.isArray(value)) return [];
  return value.map((item, index) => {
    const record = asRecord(item);
    const rawStage = asString(record.stage, "complete").toLowerCase();
    const stage = STAGE_MAP[rawStage] ?? "complete";
    const rawTimestamp = record.timestamp;
    const parsedTimestamp =
      typeof rawTimestamp === "string"
        ? Date.parse(rawTimestamp)
        : asNumber(rawTimestamp, Date.now());
    return {
      id: asString(record.id, `trace_${index}`),
      stage,
      title: asString(record.title, stage.replace(/_/g, " ")),
      details: asString(record.details),
      timestamp: Number.isFinite(parsedTimestamp) ? parsedTimestamp : Date.now(),
    };
  });
}

function normalizeResult(data: unknown, idea: string): AnalysisResult {
  const record = asRecord(data);
  const brief = asRecord(record.final_brief);
  const decision = asRecord(brief.final_decision ?? record.final_decision);
  const score = clamp(asNumber(decision.score, 0));
  const verdict = normalizeVerdict(decision.final_verdict, score);
  const action = normalizeAction(decision.action, verdict);
  const swot = asRecord(brief.swot);
  const trace = normalizeTrace(record.trace);

  return {
    id: asString(record.id, asString(record.run_id, `run_${Date.now()}`)),
    idea: asString(record.idea, asString(record.user_question, idea)),
    timestamp: asNumber(record.timestamp, Date.now()),
    processing_time_ms: asNumber(record.processing_time_ms, 0),
    final_brief: {
      final_decision: {
        final_verdict: verdict,
        action,
        score,
        confidence: clamp(asNumber(decision.confidence, 0)),
        risk: normalizeLabel(decision.risk, "Medium"),
        market_demand: normalizeLabel(decision.market_demand, "Medium"),
        competition: normalizeLabel(decision.competition, "Medium"),
        reasoning: asString(decision.reasoning, "Analysis completed."),
        demand_score: clamp(asNumber(decision.demand_score, score)),
        competition_score: clamp(asNumber(decision.competition_score, 100 - score)),
        risk_score: clamp(asNumber(decision.risk_score, 100 - score)),
      },
      swot: {
        strengths: asStringArray(swot.strengths),
        weaknesses: asStringArray(swot.weaknesses),
        opportunities: asStringArray(swot.opportunities),
        threats: asStringArray(swot.threats),
      },
      key_findings: asStringArray(brief.key_findings ?? []),
      market_analysis: asString(brief.market_analysis),
      competitor_analysis: asString(brief.competitor_analysis),
      executive_summary: asString(brief.executive_summary),
    },
    scenarios: buildScenarios(score),
    trace,
  };
}

/* ── POST /api/analyze ─────────────────────────────────────────────────────── */

export async function POST(request: Request) {
  const forwarded = request.headers.get("x-forwarded-for");
  const ip = forwarded?.split(",")[0]?.trim() || "unknown";

  if (!checkRateLimit(ip)) {
    return NextResponse.json(
      { error: "Rate limit exceeded — max 10 analyses per hour." },
      { status: 429 }
    );
  }

  const endpoint = process.env.ANALYZE_API_URL;

  // ── No backend configured: return 503 with a clear message ───────────────
  if (!endpoint) {
    return NextResponse.json(
      {
        error:
          "Analysis service not configured. " +
          "Set ANALYZE_API_URL to your api_server.py endpoint (e.g. https://your-backend.railway.app/analyze). " +
          "The UI will fall back to demo mode automatically.",
      },
      { status: 503 }
    );
  }

  const body = await request.json().catch(() => ({}));
  const idea = asString(asRecord(body).idea || asRecord(body).question);

  if (idea.length < 10) {
    return NextResponse.json({ error: "Startup idea must be at least 10 characters." }, { status: 400 });
  }
  if (idea.length > 2000) {
    return NextResponse.json({ error: "Startup idea must be 2000 characters or fewer." }, { status: 400 });
  }

  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (process.env.ANALYZE_API_KEY) {
    headers.Authorization = `Bearer ${process.env.ANALYZE_API_KEY}`;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 115_000); // 115s — under Vercel's 120s limit

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify({ idea, question: idea }),
      signal: controller.signal,
    });
    clearTimeout(timeout);

    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      const message = asString(asRecord(payload).error, `Analyzer returned HTTP ${response.status}.`);
      return NextResponse.json({ error: message }, { status: response.status });
    }

    return NextResponse.json(normalizeResult(payload, idea));
  } catch (error) {
    clearTimeout(timeout);
    if (error instanceof Error && error.name === "AbortError") {
      return NextResponse.json({ error: "Analysis timed out after 115 seconds." }, { status: 504 });
    }
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Analyzer request failed." },
      { status: 502 }
    );
  }
}
