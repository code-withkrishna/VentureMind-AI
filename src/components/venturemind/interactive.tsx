"use client"

import React, { useState, useRef, useCallback } from "react"
import { ArrowRight, Sparkles, RefreshCw, Download, RotateCcw, Zap } from "lucide-react"
import { cn, getVerdictConfig, verdictToAction, scoreToVerdict } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Textarea, Badge, Progress,
  Tabs, TabsList, TabsTrigger, TabsContent,
  Card, CardContent, CardHeader, CardTitle, CardDescription,
  Separator,
} from "@/components/ui/primitives"
import {
  ScoreArc, AgentGrid, VerdictCard, LiveTracePanel,
  SignalBar, ScenarioCardItem, SwotGrid,
} from "@/components/venturemind/display"
import type { AnalysisResult, AgentStage, TraceEvent } from "@/types"
import { EXAMPLE_IDEAS } from "@/types"

// ── Header ────────────────────────────────────────────────────────────────────

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-[var(--border-subtle)] bg-[var(--surface-0)]/80 backdrop-blur-xl" role="banner">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
        {/* Logo */}
        <div className="flex items-center gap-2.5" aria-label="VentureMind AI home">
          <span aria-hidden="true" className="text-[var(--gold)] text-lg leading-none">◆</span>
          <span className="font-display text-base font-normal text-[var(--text-primary)] tracking-tight">
            VentureMind
          </span>
          <span className="hidden sm:inline-block text-2xs font-semibold tracking-widest uppercase text-[var(--text-tertiary)] ml-0.5">
            AI
          </span>
        </div>

        {/* Right */}
        <div className="flex items-center gap-2">
          <Badge variant="gold">
            <span aria-hidden="true" className="h-1 w-1 rounded-full bg-[var(--gold)] animate-pulse-soft" />
            6-agent pipeline
          </Badge>
          <Badge variant="default" className="hidden sm:inline-flex">v2.0</Badge>
        </div>
      </div>
    </header>
  )
}

// ── IdeaInput ─────────────────────────────────────────────────────────────────

interface IdeaInputProps {
  onSubmit: (idea: string) => void
  isLoading: boolean
}

export function IdeaInput({ onSubmit, isLoading }: IdeaInputProps) {
  const [value, setValue]     = useState("")
  const [focused, setFocused] = useState(false)
  const textareaRef           = useRef<HTMLTextAreaElement>(null)
  const charLimit             = 500

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = value.trim()
    if (trimmed.length < 10 || isLoading) return
    onSubmit(trimmed)
  }, [value, isLoading, onSubmit])

  const handleExample = useCallback((idea: string) => {
    setValue(idea)
    textareaRef.current?.focus()
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      handleSubmit(e as unknown as React.FormEvent)
    }
  }, [handleSubmit])

  const charPct    = (value.length / charLimit) * 100
  const isReady    = value.trim().length >= 10 && !isLoading
  const charColor  = charPct > 90 ? "#ef4444" : charPct > 70 ? "#f59e0b" : "var(--text-tertiary)"

  return (
    <section aria-label="Idea input" className="space-y-4">
      <form onSubmit={handleSubmit} noValidate>
        {/* Textarea shell */}
        <div
          className={cn(
            "relative rounded-2xl border transition-all duration-200",
            focused
              ? "border-[var(--gold-border)] bg-[var(--surface-2)] shadow-gold-sm"
              : "border-[var(--border-subtle)] bg-[var(--surface-2)]"
          )}
        >
          <Textarea
            ref={textareaRef}
            id="idea-input"
            value={value}
            onChange={e => setValue(e.target.value.slice(0, charLimit))}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your startup idea… e.g. 'Healthcare startup that reduces clinic admin workload with voice-to-workflow AI'"
            rows={4}
            maxLength={charLimit}
            aria-label="Startup idea"
            aria-describedby="idea-hint idea-charcount"
            disabled={isLoading}
            className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 min-h-[100px] text-sm sm:text-base leading-relaxed p-4 pb-12 resize-none"
          />

          {/* Bottom bar */}
          <div className="absolute bottom-0 inset-x-0 flex items-center justify-between px-4 pb-3 pointer-events-none">
            <p id="idea-hint" className="text-2xs text-[var(--text-tertiary)]">
              ⌘ + Enter to analyze
            </p>
            <p
              id="idea-charcount"
              className="text-2xs tabular-nums transition-colors"
              style={{ color: charColor }}
              aria-live="polite"
            >
              {value.length} / {charLimit}
            </p>
          </div>
        </div>

        {/* Submit button */}
        <Button
          type="submit"
          size="xl"
          disabled={!isReady}
          className="w-full mt-3 font-semibold tracking-wide"
          aria-busy={isLoading}
        >
          {isLoading ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" aria-hidden="true" />
              Analyzing…
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              Analyze with 6 AI Agents
              <ArrowRight className="h-4 w-4 ml-auto" aria-hidden="true" />
            </>
          )}
        </Button>
      </form>

      {/* Examples */}
      <div className="space-y-2">
        <p className="text-2xs font-semibold tracking-widest uppercase text-[var(--text-tertiary)]">
          Try an example
        </p>
        <div className="flex flex-col gap-1.5">
          {EXAMPLE_IDEAS.slice(0, 3).map((idea, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleExample(idea)}
              disabled={isLoading}
              className={cn(
                "group w-full text-left rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-2)]",
                "px-4 py-2.5 text-xs text-[var(--text-secondary)] leading-relaxed",
                "hover:border-[var(--border-medium)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-3)]",
                "transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--gold)]",
                "disabled:opacity-40 disabled:cursor-not-allowed",
              )}
              aria-label={`Use example: ${idea}`}
            >
              <span aria-hidden="true" className="text-[var(--gold)] opacity-60 group-hover:opacity-100 transition-opacity mr-2">
                →
              </span>
              {idea}
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}

// ── AnalysisProgress ──────────────────────────────────────────────────────────

interface AnalysisProgressProps {
  currentStage: AgentStage | null
  events: TraceEvent[]
  progress: number
}

export function AnalysisProgress({ currentStage, events, progress }: AnalysisProgressProps) {
  return (
    <div className="space-y-4 animate-fade-up" role="status" aria-label="Analysis in progress">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            aria-hidden="true"
            className="h-2 w-2 rounded-full bg-[var(--gold)] animate-pulse-soft"
          />
          <span className="text-sm font-semibold text-[var(--text-primary)]">
            Analysis in progress
          </span>
        </div>
        <span className="text-xs text-[var(--text-tertiary)] tabular-nums" aria-live="polite">
          {progress}%
        </span>
      </div>

      <Progress value={progress} aria-label={`Analysis progress: ${progress}%`} />

      <AgentGrid activeStage={currentStage} />

      <LiveTracePanel events={events} currentStage={currentStage} />
    </div>
  )
}

// ── ResultTabs ────────────────────────────────────────────────────────────────

interface ResultTabsProps {
  result: AnalysisResult
  onReset: () => void
}

export function ResultTabs({ result, onReset }: ResultTabsProps) {
  const fd       = result.final_brief.final_decision
  const config   = getVerdictConfig(fd.final_verdict)

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Verdict hero */}
      <VerdictCard result={result} />

      {/* Quick stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "Score",       value: `${fd.score}`,        sub: "out of 100" },
          { label: "Confidence",  value: `${fd.confidence}%`,  sub: "certainty" },
          { label: "Risk level",  value: fd.risk,              sub: "assessment" },
          { label: "Time",        value: `${(result.processing_time_ms / 1000).toFixed(0)}s`, sub: "processing" },
        ].map((stat, i) => (
          <Card key={i} className="p-4">
            <p className="text-2xs font-semibold tracking-widest uppercase text-[var(--text-tertiary)] mb-1">{stat.label}</p>
            <p
              className="font-display text-2xl leading-none mb-0.5"
              style={{ color: i === 0 ? config.color : "var(--text-primary)" }}
            >
              {stat.value}
            </p>
            <p className="text-2xs text-[var(--text-tertiary)]">{stat.sub}</p>
          </Card>
        ))}
      </div>

      {/* Tabs */}
      <Tabs defaultValue="dashboard">
        <TabsList className="w-full sm:w-auto" aria-label="Analysis sections">
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="scenarios">Scenarios</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
          <TabsTrigger value="swot">SWOT</TabsTrigger>
        </TabsList>

        {/* ── Dashboard ── */}
        <TabsContent value="dashboard" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Signal breakdown</CardTitle>
              <CardDescription>Three-factor scoring formula: demand × 0.5 + competition_penalty × 0.3 + risk_penalty × 0.2</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <SignalBar label="Market demand"    value={fd.demand_score}      positive />
              <SignalBar label="Competition moat" value={fd.competition_score} positive={false} />
              <SignalBar label="Execution risk"   value={fd.risk_score}        positive={false} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Key findings</CardTitle>
              <CardDescription>Evidence surfaced by the Market and Competitor agents</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3" aria-label="Key findings">
                {result.final_brief.key_findings.map((f, i) => (
                  <li key={i} className="flex gap-3 text-sm text-[var(--text-secondary)] leading-relaxed">
                    <span aria-hidden="true" className="flex-shrink-0 font-mono text-2xs text-[var(--text-tertiary)] mt-1">
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    {f}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Executive summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                {result.final_brief.executive_summary}
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Scenarios ── */}
        <TabsContent value="scenarios" className="space-y-3">
          <Card>
            <CardHeader>
              <CardTitle>Investor scenario studio</CardTitle>
              <CardDescription>Five alternative futures — stress-test your idea before committing runway</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {result.scenarios.map((sc, i) => (
                <ScenarioCardItem
                  key={sc.id}
                  scenario={sc}
                  isActive={sc.id === "base"}
                  className={cn(`stagger-${i + 1}`, "animate-fade-up")}
                />
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Analysis ── */}
        <TabsContent value="analysis" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Market analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                {result.final_brief.market_analysis}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Competitor analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                {result.final_brief.competitor_analysis}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Agent trace log</CardTitle>
              <CardDescription>Every step the committee took</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {result.trace.map((ev, i) => (
                <div key={ev.id} className="flex gap-3">
                  <span className="text-2xs font-mono text-[var(--text-tertiary)] flex-shrink-0 mt-1">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <div>
                    <p className="text-xs font-semibold text-[var(--text-primary)] mb-0.5">{ev.title}</p>
                    <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{ev.details}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── SWOT ── */}
        <TabsContent value="swot">
          <Card>
            <CardHeader>
              <CardTitle>SWOT analysis</CardTitle>
              <CardDescription>Synthesised from market, competitor, and risk signals</CardDescription>
            </CardHeader>
            <CardContent>
              <SwotGrid swot={result.final_brief.swot} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-2">
        <Button variant="outline" size="lg" className="flex-1" onClick={onReset}>
          <RotateCcw className="h-4 w-4" aria-hidden="true" />
          Analyze another idea
        </Button>
        <Button variant="gold" size="lg" className="flex-1" aria-label="Download report" onClick={() => {
          const fd = result.final_brief.final_decision;
          const sw = result.final_brief.swot;
          const blob = new Blob(
            [
              `VentureMind AI — Analysis Report\n${'='.repeat(40)}\n\n` +
              `Idea: ${result.idea}\n` +
              `Verdict: ${result.final_brief.final_decision.final_verdict}\n` +
              `Score: ${result.final_brief.final_decision.score}/100\n` +
              `Action: ${result.final_brief.final_decision.action}\n` +
              `Confidence: ${result.final_brief.final_decision.confidence}%\n\n` +
              `Reasoning:\n${result.final_brief.final_decision.reasoning}\n\n` +
              `Key Findings:\n${result.final_brief.key_findings.map((f, i) => `  ${i + 1}. ${f}`).join('\n')}\n\n` +
              `SWOT Analysis:\n` +
              `  Strengths: ${result.final_brief.swot.strengths.join(', ')}\n` +
              `  Weaknesses: ${result.final_brief.swot.weaknesses.join(', ')}\n` +
              `  Opportunities: ${result.final_brief.swot.opportunities.join(', ')}\n` +
              `  Threats: ${result.final_brief.swot.threats.join(', ')}\n\n` +
              (result.final_brief.executive_summary ? `Executive Summary:\n${result.final_brief.executive_summary}\n\n` : '') +
              (result.final_brief.market_analysis ? `Market Analysis:\n${result.final_brief.market_analysis}\n\n` : '') +
              (result.final_brief.competitor_analysis ? `Competitor Analysis:\n${result.final_brief.competitor_analysis}\n` : '')
            ],
            { type: 'text/plain' }
          );
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `venturemind-report-${Date.now()}.txt`;
          a.click();
          URL.revokeObjectURL(url);
        }}>
          <Download className="h-4 w-4" aria-hidden="true" />
          Download report
        </Button>
      </div>
    </div>
  )
}

// ── WhatIfSimulator ───────────────────────────────────────────────────────────

interface WhatIfSimulatorProps {
  baseScore: number
}

export function WhatIfSimulator({ baseScore }: WhatIfSimulatorProps) {
  const [demand,      setDemand]      = useState(0)
  const [competition, setCompetition] = useState(0)
  const [risk,        setRisk]        = useState(0)

  const simScore   = Math.max(0, Math.min(100, baseScore + demand - competition - risk))
  const simVerdict = scoreToVerdict(simScore)
  const simConfig  = getVerdictConfig(simVerdict)
  const simAction  = verdictToAction(simVerdict)

  const sliders: {
    label: string; value: number;
    setter: (v: number) => void; positive: boolean
  }[] = [
    { label: "Demand boost",        value: demand,      setter: setDemand,      positive: true },
    { label: "Competition pressure", value: competition, setter: setCompetition, positive: false },
    { label: "Risk increase",        value: risk,        setter: setRisk,        positive: false },
  ]

  return (
    <Card aria-label="What-If Simulator">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-[var(--gold)]" aria-hidden="true" />
          <CardTitle>What-If Simulator</CardTitle>
        </div>
        <CardDescription>
          Drag the sliders to stress-test your verdict in real time
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Sliders */}
        {sliders.map(({ label, value, setter, positive }) => (
          <div key={label} className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label
                className="text-xs text-[var(--text-secondary)]"
                htmlFor={`slider-${label}`}
              >
                {label}
              </label>
              <span className="text-xs font-semibold tabular-nums" style={{
                color: positive
                  ? (value > 0 ? "#22c55e" : "var(--text-tertiary)")
                  : (value > 0 ? "#ef4444" : "var(--text-tertiary)")
              }}>
                {value > 0 ? "+" : ""}{value}
              </span>
            </div>
            <input
              id={`slider-${label}`}
              type="range"
              min={-25}
              max={25}
              step={1}
              value={value}
              onChange={e => setter(Number(e.target.value))}
              className="w-full h-1 rounded-full appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, var(--gold) ${((value + 25) / 50) * 100}%, var(--surface-4) ${((value + 25) / 50) * 100}%)`,
                accentColor: "var(--gold)",
              }}
              aria-label={`${label}: ${value}`}
            />
          </div>
        ))}

        <Separator />

        {/* Result */}
        <div
          className="relative overflow-hidden rounded-xl p-4 transition-all duration-300"
          style={{
            background: simConfig.bgColor,
            border: `1px solid ${simConfig.borderColor}`,
          }}
          role="status"
          aria-live="polite"
          aria-label={`Simulated verdict: ${simAction}, score ${simScore}`}
        >
          {/* Stripe */}
          <div
            className="absolute inset-x-0 top-0 h-px"
            style={{ background: `linear-gradient(90deg, transparent, ${simConfig.color}55, transparent)` }}
          />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xs font-bold tracking-widest uppercase mb-1" style={{ color: simConfig.color }}>
                Simulated signal
              </p>
              <p className="font-display text-3xl leading-none" style={{ color: simConfig.color }}>
                {simAction}
              </p>
            </div>
            <ScoreArc score={simScore} verdict={simVerdict} size={72} animated={false} />
          </div>
        </div>

        {/* Reset */}
        {(demand !== 0 || competition !== 0 || risk !== 0) && (
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-[var(--text-tertiary)]"
            onClick={() => { setDemand(0); setCompetition(0); setRisk(0) }}
          >
            <RotateCcw className="h-3 w-3" aria-hidden="true" />
            Reset sliders
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

// ── HowItWorks ────────────────────────────────────────────────────────────────

export function HowItWorks() {
  const steps = [
    { num: "1", title: "Describe your idea",   desc: "One sentence is enough"                   },
    { num: "2", title: "Six agents debate it",  desc: "Market · Competitors · Risk · Decision"  },
    { num: "3", title: "Get the verdict",       desc: "BUILD · CAUTION · REJECT + evidence"     },
  ]
  return (
    <Card aria-label="How VentureMind works">
      <CardHeader>
        <CardTitle className="text-sm">How it works</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {steps.map(({ num, title, desc }) => (
          <div key={num} className="flex gap-3">
            <div
              className="h-6 w-6 rounded-lg flex-shrink-0 flex items-center justify-center text-2xs font-bold"
              style={{
                background: "var(--gold-dim)",
                border: "1px solid var(--gold-border)",
                color: "var(--gold-light)",
              }}
              aria-hidden="true"
            >
              {num}
            </div>
            <div>
              <p className="text-sm font-semibold text-[var(--text-primary)] leading-none mb-1">{title}</p>
              <p className="text-xs text-[var(--text-tertiary)]">{desc}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
