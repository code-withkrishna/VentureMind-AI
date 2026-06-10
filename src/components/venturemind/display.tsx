"use client"

import React, { useEffect, useMemo, useRef } from "react"
import { cn, scoreArcProps, getVerdictConfig, clampText } from "@/lib/utils"
import { Badge } from "@/components/ui/primitives"
import type { AnalysisResult, Agent, AgentStage, TraceEvent, Verdict } from "@/types"
import { AGENT_DEFINITIONS, STAGE_ORDER } from "@/types"

// ── ScoreArc ──────────────────────────────────────────────────────────────────

interface ScoreArcProps {
  score: number
  verdict: Verdict
  size?: number
  strokeWidth?: number
  animated?: boolean
  className?: string
}

export function ScoreArc({
  score, verdict, size = 128, strokeWidth = 8, animated = true, className,
}: ScoreArcProps) {
  const radius = (size - strokeWidth) / 2
  const cx = size / 2
  const cy = size / 2
  const config = getVerdictConfig(verdict)
  const { circumference, dashOffset } = scoreArcProps(score, radius)
  const filterId = useMemo(() => `glow-${score}-${Math.random().toString(36).slice(2, 7)}`, [score])

  const circleRef = useRef<SVGCircleElement>(null)

  useEffect(() => {
    if (!animated || !circleRef.current) return
    circleRef.current.style.strokeDashoffset = `${circumference}`
    const raf = requestAnimationFrame(() => {
      if (circleRef.current) {
        circleRef.current.style.transition = "stroke-dashoffset 1.4s cubic-bezier(0.22,0.68,0,1.1) 0.3s"
        circleRef.current.style.strokeDashoffset = `${dashOffset}`
      }
    })
    return () => cancelAnimationFrame(raf)
  }, [score, dashOffset, circumference, animated])

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className={cn("overflow-visible", className)}
      aria-label={`Score: ${score} out of 100`}
      role="img"
    >
      <defs>
        <filter id={filterId}>
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>
      {/* Track */}
      <circle
        cx={cx} cy={cy} r={radius}
        fill="none"
        stroke="rgba(255,255,255,0.06)"
        strokeWidth={strokeWidth}
      />
      {/* Fill */}
      <circle
        ref={circleRef}
        cx={cx} cy={cy} r={radius}
        fill="none"
        stroke={config.color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={animated ? circumference : dashOffset}
        filter={`url(#${filterId})`}
        transform={`rotate(-90 ${cx} ${cy})`}
        style={!animated ? { strokeDashoffset: dashOffset } : undefined}
      />
      {/* Score text */}
      <text
        x={cx} y={cy - 8}
        textAnchor="middle"
        fontFamily="'Instrument Serif', Georgia, serif"
        fontSize={size < 100 ? "20" : "28"}
        fontWeight="400"
        fill={config.color}
      >
        {score}
      </text>
      <text
        x={cx} y={cy + 12}
        textAnchor="middle"
        fontFamily="system-ui, sans-serif"
        fontSize="10"
        fill="rgba(255,255,255,0.28)"
      >
        /100
      </text>
    </svg>
  )
}

// ── AgentGrid ─────────────────────────────────────────────────────────────────

interface AgentGridProps {
  activeStage: AgentStage | null
  completedStages?: Set<AgentStage>
  className?: string
}

export function AgentGrid({ activeStage, completedStages, className }: AgentGridProps) {
  return (
    <div
      className={cn("grid grid-cols-3 sm:grid-cols-6 gap-2", className)}
      role="list"
      aria-label="Agent pipeline status"
    >
      {AGENT_DEFINITIONS.map((agent, i) => {
        const isLive = agent.stage === activeStage
        const isDone = completedStages
          ? completedStages.has(agent.stage)
          : activeStage
            ? STAGE_ORDER.indexOf(agent.stage) < STAGE_ORDER.indexOf(activeStage)
            : false

        return (
          <AgentCard
            key={agent.id}
            agent={agent}
            isLive={isLive}
            isDone={isDone}
            style={{ animationDelay: `${i * 60}ms` }}
          />
        )
      })}
    </div>
  )
}

interface AgentCardProps {
  agent: Agent
  isLive: boolean
  isDone: boolean
  style?: React.CSSProperties
}

function AgentCard({ agent, isLive, isDone, style }: AgentCardProps) {
  return (
    <div
      role="listitem"
      aria-label={`${agent.name}: ${isDone ? "complete" : isLive ? "running" : "queued"}`}
      style={style}
      className={cn(
        "relative overflow-hidden rounded-xl border p-3 transition-all duration-300 animate-fade-up",
        isDone && "border-[rgba(34,197,94,0.2)] bg-[rgba(34,197,94,0.05)]",
        isLive && "border-[rgba(201,134,26,0.35)] bg-[rgba(201,134,26,0.07)] shadow-gold-sm",
        !isDone && !isLive && "border-[var(--border-subtle)] bg-[var(--surface-2)]",
      )}
    >
      {/* Top accent stripe */}
      <div
        className={cn(
          "absolute inset-x-0 top-0 h-px transition-all duration-300",
          isDone && "bg-[rgba(34,197,94,0.4)]",
          isLive && "bg-gradient-to-r from-transparent via-[rgba(201,134,26,0.6)] to-transparent",
          !isDone && !isLive && "bg-transparent",
        )}
      />

      {/* Header row */}
      <div className="flex items-center justify-between mb-2">
        <span className={cn(
          "text-2xs font-bold tracking-widest",
          isDone && "text-[#22c55e]",
          isLive && "text-[var(--gold)]",
          !isDone && !isLive && "text-[var(--text-tertiary)]",
        )}>
          {agent.num}
        </span>

        {/* Status dot */}
        <span
          aria-hidden="true"
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            isDone && "bg-[#22c55e]",
            isLive && "bg-[var(--gold)] animate-pulse-soft",
            !isDone && !isLive && "bg-[var(--surface-4)]",
          )}
        />
      </div>

      <p className={cn(
        "text-xs font-semibold leading-none mb-1 transition-colors",
        isDone && "text-[#22c55e]",
        isLive && "text-[var(--text-primary)]",
        !isDone && !isLive && "text-[var(--text-tertiary)]",
      )}>
        {agent.name}
      </p>
      <p className="text-2xs text-[var(--text-tertiary)] leading-tight hidden sm:block">
        {agent.description}
      </p>
    </div>
  )
}

// ── VerdictCard ───────────────────────────────────────────────────────────────

interface VerdictCardProps {
  result: AnalysisResult
  className?: string
}

export function VerdictCard({ result, className }: VerdictCardProps) {
  const fd      = result.final_brief.final_decision
  const config  = getVerdictConfig(fd.final_verdict)
  const sources = result.trace.length * 3

  const pills = [
    { label: "Demand",      value: fd.market_demand },
    { label: "Competition", value: fd.competition },
    { label: "Risk",        value: fd.risk },
    { label: "Sources",     value: `${sources}` },
    { label: "Agents",      value: "6 active" },
  ]

  return (
    <div
      className={cn("relative overflow-hidden rounded-2xl border p-6 sm:p-8 animate-scale-in", className)}
      style={{
        background: `linear-gradient(160deg, ${config.gradientFrom} 0%, ${config.gradientTo} 100%)`,
        borderColor: config.borderColor,
      }}
      role="region"
      aria-label={`Analysis result: ${fd.action}`}
    >
      {/* Ambient glow blobs */}
      <div
        aria-hidden="true"
        className="absolute -top-20 -right-20 h-64 w-64 rounded-full opacity-20 blur-3xl pointer-events-none"
        style={{ background: config.glowColor }}
      />
      <div
        aria-hidden="true"
        className="absolute -bottom-16 -left-12 h-48 w-48 rounded-full opacity-10 blur-3xl pointer-events-none"
        style={{ background: config.glowColor }}
      />

      <div className="relative flex flex-col sm:flex-row items-start gap-6 sm:gap-8">
        {/* Left — action + reasoning */}
        <div className="flex-1 min-w-0">
          {/* Live badge */}
          <div className="inline-flex items-center gap-2 mb-4">
            <span
              aria-hidden="true"
              className="h-1.5 w-1.5 rounded-full animate-pulse-soft"
              style={{ background: config.color }}
            />
            <span
              className="text-2xs font-bold tracking-[0.15em] uppercase"
              style={{ color: config.color }}
            >
              Final Investor Signal
            </span>
          </div>

          {/* Verdict word */}
          <h2
            className="font-display text-5xl sm:text-6xl lg:text-7xl font-normal leading-none mb-4 animate-fade-up"
            style={{ color: config.color, letterSpacing: "-0.025em" }}
          >
            {fd.action}
          </h2>

          {/* Reasoning */}
          <p className="text-sm sm:text-base text-[var(--text-secondary)] leading-relaxed max-w-lg font-light">
            {fd.reasoning}
          </p>
        </div>

        {/* Right — score arc */}
        <div
          className="flex-shrink-0 rounded-2xl p-4 sm:p-5 text-center"
          style={{
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          <ScoreArc score={fd.score} verdict={fd.final_verdict} size={120} animated />
          <p className="text-2xs text-[var(--text-tertiary)] mt-2">{fd.confidence}% confidence</p>
        </div>
      </div>

      {/* Bottom pills */}
      <div
        className="relative mt-6 pt-5 flex flex-wrap gap-2"
        style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
      >
        {pills.map(pill => (
          <div
            key={pill.label}
            className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs"
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.08)",
            }}
          >
            <span className="text-[var(--text-tertiary)]">{pill.label}</span>
            <span className="text-[var(--text-primary)] font-medium">{pill.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── LiveTracePanel ────────────────────────────────────────────────────────────

interface LiveTracePanelProps {
  events: TraceEvent[]
  currentStage: AgentStage | null
  className?: string
}

const STAGE_COLORS: Record<string, string> = {
  planning:             "var(--gold)",
  market_research:      "#60a5fa",
  competitor_analysis:  "#a78bfa",
  evaluation:           "#f59e0b",
  decision:             "#22c55e",
  report:               "#38bdf8",
}

const STAGE_ICONS: Record<string, string> = {
  planning: "◈", market_research: "◎", competitor_analysis: "◉",
  evaluation: "◐", decision: "◆", report: "◇",
}

export function LiveTracePanel({ events, currentStage, className }: LiveTracePanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [events.length])

  if (!events.length) return null

  return (
    <div
      className={cn(
        "rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-2)] overflow-hidden",
        className
      )}
      role="log"
      aria-label="Agent execution trace"
      aria-live="polite"
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--border-subtle)]">
        <span
          aria-hidden="true"
          className="h-1.5 w-1.5 rounded-full animate-pulse-soft"
          style={{ background: "var(--gold)" }}
        />
        <span className="text-2xs font-bold tracking-widest uppercase text-[var(--text-tertiary)]">
          Live trace
        </span>
        {currentStage && (
          <Badge variant="live" className="ml-auto">
            {currentStage.replaceAll("_", " ")}
          </Badge>
        )}
      </div>

      {/* Events */}
      <div ref={scrollRef} className="max-h-48 overflow-y-auto p-3 space-y-1">
        {events.map((ev, i) => (
          <div
            key={ev.id}
            className={cn(
              "flex gap-3 p-2.5 rounded-lg transition-all duration-200",
              i === events.length - 1 && "bg-[var(--surface-3)]"
            )}
          >
            <span
              aria-hidden="true"
              className="text-sm flex-shrink-0 mt-0.5"
              style={{ color: STAGE_COLORS[ev.stage] ?? "var(--text-tertiary)" }}
            >
              {STAGE_ICONS[ev.stage] ?? "·"}
            </span>
            <div className="min-w-0">
              <p className="text-xs font-medium text-[var(--text-primary)] mb-0.5">{ev.title}</p>
              <p className="text-2xs text-[var(--text-tertiary)] leading-relaxed">
                {clampText(ev.details, 100)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── SignalBar ─────────────────────────────────────────────────────────────────

interface SignalBarProps {
  label: string
  value: number
  positive?: boolean
  className?: string
}

export function SignalBar({ label, value, positive = true, className }: SignalBarProps) {
  const color = positive
    ? value >= 70 ? "#22c55e" : value >= 40 ? "#f59e0b" : "#ef4444"
    : value >= 70 ? "#ef4444" : value >= 40 ? "#f59e0b" : "#22c55e"

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-[var(--text-secondary)]">{label}</span>
        <span
          className="text-xs font-semibold tabular-nums"
          style={{ color }}
        >
          {value}
        </span>
      </div>
      <div className="h-[3px] w-full rounded-full bg-[var(--surface-4)] overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${value}%`,
            background: color,
            boxShadow: `0 0 8px ${color}60`,
          }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={label}
        />
      </div>
    </div>
  )
}

// ── ScenarioCard ─────────────────────────────────────────────────────────────

interface ScenarioCardItemProps {
  scenario: {
    id: string
    name: string
    icon: string
    summary: string
    score: number
    delta: number
    verdict: Verdict
    implication: string
  }
  isActive?: boolean
  className?: string
}

export function ScenarioCardItem({ scenario, isActive, className }: ScenarioCardItemProps) {
  const config    = getVerdictConfig(scenario.verdict)
  const deltaSign = scenario.delta > 0 ? "+" : ""
  const deltaColor = scenario.delta > 0 ? "#22c55e" : scenario.delta < 0 ? "#ef4444" : "var(--text-tertiary)"

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border p-4 transition-all duration-200 cursor-default",
        isActive
          ? "border-[var(--border-medium)] bg-[var(--surface-3)]"
          : "border-[var(--border-subtle)] bg-[var(--surface-2)] hover:border-[var(--border-medium)] hover:bg-[var(--surface-3)]",
        className
      )}
    >
      {/* Top accent */}
      {isActive && (
        <div
          className="absolute inset-x-0 top-0 h-px"
          style={{ background: `linear-gradient(90deg, transparent, ${config.color}55, transparent)` }}
        />
      )}

      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span aria-hidden="true" className="text-base opacity-75">{scenario.icon}</span>
            <span className="text-sm font-semibold text-[var(--text-primary)] truncate">{scenario.name}</span>
          </div>
          <p className="text-xs text-[var(--text-tertiary)] mb-2 leading-relaxed">
            {clampText(scenario.summary, 70)}
          </p>
          <p className="text-xs italic leading-relaxed" style={{ color: "var(--gold-light)" }}>
            {clampText(scenario.implication, 80)}
          </p>
        </div>

        <div className="flex-shrink-0 text-right">
          <p
            className="font-display text-2xl leading-none"
            style={{ color: config.color }}
          >
            {scenario.score}
          </p>
          <p
            className="text-xs font-bold mt-0.5"
            style={{ color: deltaColor }}
          >
            {deltaSign}{scenario.delta}
          </p>
        </div>
      </div>
    </div>
  )
}

// ── SwotGrid ──────────────────────────────────────────────────────────────────

interface SwotGridProps {
  swot: {
    strengths: string[]
    weaknesses: string[]
    opportunities: string[]
    threats: string[]
  }
  className?: string
}

const SWOT_META = [
  { key: "strengths",     label: "Strengths",     color: "#22c55e", bg: "rgba(34,197,94,0.06)",  border: "rgba(34,197,94,0.15)" },
  { key: "weaknesses",    label: "Weaknesses",    color: "#ef4444", bg: "rgba(239,68,68,0.06)",  border: "rgba(239,68,68,0.15)" },
  { key: "opportunities", label: "Opportunities", color: "#60a5fa", bg: "rgba(96,165,250,0.06)", border: "rgba(96,165,250,0.15)" },
  { key: "threats",       label: "Threats",       color: "#f59e0b", bg: "rgba(245,158,11,0.06)", border: "rgba(245,158,11,0.15)" },
] as const

export function SwotGrid({ swot, className }: SwotGridProps) {
  return (
    <div
      className={cn("grid grid-cols-1 sm:grid-cols-2 gap-3", className)}
      aria-label="SWOT Analysis"
    >
      {SWOT_META.map(({ key, label, color, bg, border }) => {
        const items: string[] = swot[key] ?? []
        return (
          <div
            key={key}
            className="rounded-xl p-4"
            style={{ background: bg, border: `1px solid ${border}` }}
            aria-label={`${label}: ${items.length} items`}
          >
            <p
              className="text-2xs font-bold tracking-widest uppercase mb-3"
              style={{ color }}
            >
              {label}
            </p>
            <ul className="space-y-1.5" aria-label={label}>
              {items.length ? items.map((item, i) => (
                <li key={i} className="flex gap-2 text-xs text-[var(--text-secondary)] leading-relaxed">
                  <span aria-hidden="true" className="flex-shrink-0 mt-0.5" style={{ color }}>·</span>
                  {item}
                </li>
              )) : (
                <li className="text-xs text-[var(--text-tertiary)]">None surfaced.</li>
              )}
            </ul>
          </div>
        )
      })}
    </div>
  )
}
