"use client"

import React, { useState, useCallback, useRef } from "react"
import {
  Header, IdeaInput, AnalysisProgress,
  ResultTabs, WhatIfSimulator, HowItWorks,
} from "@/components/venturemind/interactive"
import { Badge } from "@/components/ui/primitives"
import { analyzeIdea } from "@/lib/api"
import { generateMockResult } from "@/lib/utils"
import type { AnalysisResult, AgentStage, TraceEvent } from "@/types"
import { STAGE_ORDER, AGENT_DEFINITIONS } from "@/types"

// ── Stage display labels ──────────────────────────────────────────────────────

const STAGE_TITLES: Record<AgentStage, string> = {
  planning:            "Planner agent — research plan decomposed",
  market_research:     "Market agent — demand signals being gathered",
  competitor_analysis: "Competitor agent — landscape being mapped",
  evaluation:          "Evaluator agent — quality gate running",
  decision:            "Decision agent — scoring with 50/30/20 formula",
  report:              "Report agent — investment memo being synthesised",
  complete:            "Analysis complete",
}

const STAGE_DETAILS: Record<AgentStage, string> = {
  planning:            "Breaking your idea into targeted research vectors: TAM, adoption signals, buyer personas.",
  market_research:     "Searching live web sources for demand evidence and market sizing data.",
  competitor_analysis: "Mapping direct and indirect competitors; assessing moat potential.",
  evaluation:          "EvaluatorAgent reviewing evidence quality. Will trigger reflection loop if confidence is low.",
  decision:            "Computing final score: demand × 0.5 + competition_penalty × 0.3 + risk_penalty × 0.2.",
  report:              "Synthesising SWOT, key findings, and executive summary into investor memo.",
  complete:            "All 6 agents finished. Result ready.",
}

// ── Analysis engine ───────────────────────────────────────────────────────────

function useAnalysisEngine() {
  const [status,       setStatus]       = useState<"idle" | "analyzing" | "done" | "error">("idle")
  const [currentStage, setCurrentStage] = useState<AgentStage | null>(null)
  const [progress,     setProgress]     = useState(0)
  const [events,       setEvents]       = useState<TraceEvent[]>([])
  const [result,       setResult]       = useState<AnalysisResult | null>(null)
  const [error,        setError]        = useState<string | null>(null)
  const [isDemo,       setIsDemo]       = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const startAnalysis = useCallback(async (idea: string) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setStatus("analyzing")
    setCurrentStage(null)
    setProgress(0)
    setEvents([])
    setResult(null)
    setError(null)
    setIsDemo(false)

    // ── Kick off the real API call in the background ──────────────────────
    const apiCall: Promise<{ result: AnalysisResult } | { error: unknown }> =
      analyzeIdea(idea, controller.signal)
        .then(r => ({ result: r }))
        .catch(e => ({ error: e }))

    // ── Animate agent stages while waiting ────────────────────────────────
    const STAGE_DELAY = 1_200

    for (let i = 0; i < STAGE_ORDER.length; i++) {
      if (controller.signal.aborted) return
      const stage = STAGE_ORDER[i]
      setCurrentStage(stage)
      setProgress(Math.round(((i + 0.5) / STAGE_ORDER.length) * 100))

      await new Promise(r => setTimeout(r, STAGE_DELAY))
      if (controller.signal.aborted) return

      setEvents(prev => [
        ...prev,
        {
          id:        `anim_${i}_${Date.now()}`,
          stage,
          title:     STAGE_TITLES[stage],
          details:   STAGE_DETAILS[stage],
          timestamp: Date.now(),
        },
      ])
      setProgress(Math.round(((i + 1) / STAGE_ORDER.length) * 100))
    }

    if (controller.signal.aborted) return

    // ── Wait for real API result (or use mock) ────────────────────────────
    const outcome = await Promise.race([
      apiCall,
      new Promise<{ timeout: true }>(r => setTimeout(() => r({ timeout: true }), 120_000)),
    ])

    if (controller.signal.aborted) return

    if ("timeout" in outcome) {
      // API took too long — fall back to demo mode
      const mock = generateMockResult(idea)
      setResult({ ...mock, trace: events })
      setIsDemo(true)
      setStatus("done")
      return
    }

    if ("error" in outcome) {
      const err = outcome.error
      // If ANALYZE_API_URL isn't configured, fall back to demo mode gracefully
      const msg = err instanceof Error ? err.message : String(err)
      if (
        msg.includes("unavailable") ||
        msg.includes("503") ||
        msg.includes("ANALYZE_API_URL") ||
        msg.includes("not configured") ||
        msg.includes("fetch")
      ) {
        const mock = generateMockResult(idea)
        setResult({ ...mock, trace: events })
        setIsDemo(true)
        setStatus("done")
      } else {
        setError(msg || "Analysis failed. Please try again.")
        setStatus("error")
      }
      return
    }

    // Real result — merge in the animated trace events for better UX
    const real = (outcome as { result: AnalysisResult }).result
    const mergedTrace = real.trace?.length ? real.trace : events
    setResult({ ...real, trace: mergedTrace })
    setIsDemo(false)
    setStatus("done")
    setCurrentStage(null)
    setProgress(100)
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setStatus("idle")
    setCurrentStage(null)
    setProgress(0)
    setEvents([])
    setResult(null)
    setError(null)
    setIsDemo(false)
  }, [])

  return { status, currentStage, progress, events, result, error, isDemo, startAnalysis, reset }
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function HomePage() {
  const {
    status, currentStage, progress, events,
    result, error, isDemo, startAnalysis, reset,
  } = useAnalysisEngine()

  return (
    <>
      <Header />

      <main className="mx-auto max-w-6xl px-4 sm:px-6 py-8 sm:py-12" id="main-content">

        {/* ── IDLE ── */}
        {status === "idle" && (
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6 lg:gap-8 items-start">

            {/* Left */}
            <div className="space-y-6">
              <div className="space-y-4 animate-fade-up">
                <div className="inline-flex items-center gap-2">
                  <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-[var(--gold)] animate-pulse-soft" />
                  <span className="text-2xs font-bold tracking-widest uppercase text-[var(--gold)]">AI Investment Committee</span>
                </div>

                <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-normal leading-[1.06] text-[var(--text-primary)] tracking-tight">
                  Should you build<br />
                  <em className="text-[var(--gold)] not-italic">this startup?</em>
                </h1>

                <p className="text-base sm:text-lg text-[var(--text-secondary)] leading-relaxed max-w-lg font-light">
                  Paste your idea. Six AI agents debate market demand, competition, and risk.
                  Get a{" "}
                  <strong className="text-[var(--text-primary)] font-semibold">BUILD · CAUTION · REJECT</strong>{" "}
                  verdict with evidence in 90 seconds.
                </p>

                <div className="flex flex-wrap gap-2">
                  {["6-agent pipeline", "Deterministic scoring", "5-scenario studio", "PDF export"].map(tag => (
                    <Badge key={tag} variant="default">{tag}</Badge>
                  ))}
                </div>
              </div>

              <div className="animate-fade-up animate-delay-200">
                <IdeaInput onSubmit={startAnalysis} isLoading={false} />
              </div>
            </div>

            {/* Right sidebar */}
            <aside className="space-y-4 lg:sticky lg:top-24 animate-fade-up animate-delay-300" aria-label="How VentureMind works">
              <HowItWorks />
              <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-2)] p-4 space-y-3" aria-label="Platform stats">
                <p className="text-2xs font-bold tracking-widest uppercase text-[var(--text-tertiary)]">Platform</p>
                {[
                  { label: "Scoring formula",  value: "50 / 30 / 20" },
                  { label: "Agents per run",   value: "6 specialist" },
                  { label: "Avg. runtime",     value: "< 90 seconds" },
                  { label: "Scenarios",        value: "5 investor cases" },
                ].map(({ label, value }) => (
                  <div key={label} className="flex items-center justify-between">
                    <span className="text-xs text-[var(--text-tertiary)]">{label}</span>
                    <span className="text-xs font-semibold text-[var(--text-primary)]">{value}</span>
                  </div>
                ))}
              </div>
            </aside>
          </div>
        )}

        {/* ── ANALYZING ── */}
        {status === "analyzing" && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="text-center space-y-2 animate-fade-up">
              <h2 className="font-display text-2xl text-[var(--text-primary)]">Committee in session…</h2>
              <p className="text-sm text-[var(--text-secondary)]">Six agents are researching and debating your idea in real time</p>
            </div>
            <AnalysisProgress currentStage={currentStage} events={events} progress={progress} />
          </div>
        )}

        {/* ── ERROR ── */}
        {status === "error" && error && (
          <div className="max-w-lg mx-auto text-center space-y-4 animate-fade-up">
            <div className="rounded-2xl border border-[rgba(239,68,68,0.2)] bg-[rgba(239,68,68,0.06)] p-8">
              <p className="text-2xl mb-2" aria-hidden="true">⚠</p>
              <h2 className="font-display text-xl text-[var(--text-primary)] mb-2">Analysis failed</h2>
              <p className="text-sm text-[var(--text-secondary)] mb-4">{error}</p>
              <button
                onClick={reset}
                className="text-sm font-medium text-[var(--gold)] hover:underline"
              >
                Try again →
              </button>
            </div>
          </div>
        )}

        {/* ── DONE ── */}
        {status === "done" && result && (
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 lg:gap-8 items-start">

            {/* Main results */}
            <div>
              {/* Demo mode notice */}
              {isDemo && (
                <div className="mb-4 rounded-xl border border-[var(--gold-border)] bg-[var(--gold-dim)] px-4 py-3 animate-fade-up">
                  <p className="text-xs text-[var(--gold-light)]">
                    <strong>Demo mode</strong> — showing illustrative analysis. Connect{" "}
                    <code className="text-xs bg-[rgba(255,255,255,0.1)] px-1 py-0.5 rounded">ANALYZE_API_URL</code>{" "}
                    for real AI pipeline results.
                  </p>
                </div>
              )}

              {/* Idea pill */}
              <div className="mb-4 flex items-center gap-2 flex-wrap animate-fade-up">
                <span className="text-xs text-[var(--text-tertiary)]">Analyzing:</span>
                <span className="inline-flex items-center rounded-full border border-[var(--border-subtle)] bg-[var(--surface-3)] px-3 py-1 text-xs text-[var(--text-secondary)] max-w-sm truncate">
                  {result.idea}
                </span>
              </div>

              <ResultTabs result={result} onReset={reset} />
            </div>

            {/* Right sidebar */}
            <aside className="space-y-4 lg:sticky lg:top-24 animate-fade-up animate-delay-200" aria-label="Analysis tools">
              <WhatIfSimulator
                baseScore={result.final_brief.final_decision.score}
              />

              {/* Agent completion */}
              <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-2)] p-4">
                <p className="text-2xs font-bold tracking-widest uppercase text-[var(--text-tertiary)] mb-3">Pipeline complete</p>
                <div className="space-y-2">
                  {AGENT_DEFINITIONS.map(agent => (
                    <div key={agent.id} className="flex items-center gap-2.5">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e] flex-shrink-0" aria-hidden="true" />
                      <span className="text-xs text-[var(--text-secondary)]">{agent.name}</span>
                      <span className="ml-auto text-2xs text-[#22c55e] font-medium">Done</span>
                    </div>
                  ))}
                </div>
              </div>
            </aside>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--border-subtle)] mt-16 py-8" role="contentinfo">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span aria-hidden="true" className="text-[var(--gold)] opacity-60">◆</span>
            <span className="text-xs text-[var(--text-tertiary)]">VentureMind AI — AI Investment Committee</span>
          </div>
          <div className="flex items-center gap-4">
            {["Deterministic scoring", "6-agent pipeline", "5 investor scenarios"].map(tag => (
              <span key={tag} className="text-2xs text-[var(--text-tertiary)]">{tag}</span>
            ))}
          </div>
        </div>
      </footer>
    </>
  )
}
