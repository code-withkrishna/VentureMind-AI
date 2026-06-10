"use client"

// ── Textarea ──────────────────────────────────────────────────────────────────
import * as React from "react"
import * as TabsPrimitive from "@radix-ui/react-tabs"
import * as ProgressPrimitive from "@radix-ui/react-progress"
import * as SeparatorPrimitive from "@radix-ui/react-separator"
import * as LabelPrimitive from "@radix-ui/react-label"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

// ─────────────────────────────────────────────────────────────────────────────
// LABEL
// ─────────────────────────────────────────────────────────────────────────────
const labelVariants = cva(
  "text-xs font-medium leading-none text-[var(--text-secondary)] tracking-widest uppercase peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
)
const Label = React.forwardRef<
  React.ElementRef<typeof LabelPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof LabelPrimitive.Root> & VariantProps<typeof labelVariants>
>(({ className, ...props }, ref) => (
  <LabelPrimitive.Root ref={ref} className={cn(labelVariants(), className)} {...props} />
))
Label.displayName = LabelPrimitive.Root.displayName

// ─────────────────────────────────────────────────────────────────────────────
// TEXTAREA
// ─────────────────────────────────────────────────────────────────────────────
export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>
const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "flex min-h-[80px] w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-2)]",
        "px-4 py-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--gold-border)]",
        "focus-visible:border-[var(--gold-border)] focus-visible:bg-[var(--surface-3)]",
        "disabled:cursor-not-allowed disabled:opacity-50 resize-none",
        "transition-all duration-150 leading-relaxed",
        "caret-[var(--gold)]",
        className
      )}
      {...props}
    />
  )
)
Textarea.displayName = "Textarea"

// ─────────────────────────────────────────────────────────────────────────────
// BADGE
// ─────────────────────────────────────────────────────────────────────────────
const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-2xs font-semibold tracking-wider uppercase transition-colors focus:outline-none focus:ring-2 focus:ring-ring",
  {
    variants: {
      variant: {
        default:    "border-[var(--border-subtle)] bg-[var(--surface-3)] text-[var(--text-secondary)]",
        gold:       "border-[var(--gold-border)] bg-[var(--gold-dim)] text-[var(--gold-light)]",
        build:      "border-[rgba(34,197,94,0.25)] bg-[rgba(34,197,94,0.08)] text-[#22c55e]",
        caution:    "border-[rgba(245,158,11,0.25)] bg-[rgba(245,158,11,0.08)] text-[#f59e0b]",
        reject:     "border-[rgba(239,68,68,0.25)] bg-[rgba(239,68,68,0.08)] text-[#ef4444]",
        blue:       "border-[rgba(96,165,250,0.25)] bg-[rgba(96,165,250,0.08)] text-[#60a5fa]",
        purple:     "border-[rgba(167,139,250,0.25)] bg-[rgba(167,139,250,0.08)] text-[#a78bfa]",
        live:       "border-[var(--gold-border)] bg-[var(--gold-dim)] text-[var(--gold-light)] animate-pulse-soft",
      },
    },
    defaultVariants: { variant: "default" },
  }
)
export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}
function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

// ─────────────────────────────────────────────────────────────────────────────
// PROGRESS
// ─────────────────────────────────────────────────────────────────────────────
const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>
>(({ className, value, ...props }, ref) => (
  <ProgressPrimitive.Root
    ref={ref}
    className={cn("relative h-[3px] w-full overflow-hidden rounded-full bg-[var(--surface-4)]", className)}
    {...props}
  >
    <ProgressPrimitive.Indicator
      className="h-full w-full flex-1 rounded-full transition-all duration-500 ease-out"
      style={{
        transform: `translateX(-${100 - (value ?? 0)}%)`,
        background: "linear-gradient(90deg, #a56614, #c9861a, #e4a81e)",
        boxShadow: "0 0 10px rgba(201,134,26,0.5)",
      }}
    />
  </ProgressPrimitive.Root>
))
Progress.displayName = ProgressPrimitive.Root.displayName

// ─────────────────────────────────────────────────────────────────────────────
// SEPARATOR
// ─────────────────────────────────────────────────────────────────────────────
const Separator = React.forwardRef<
  React.ElementRef<typeof SeparatorPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SeparatorPrimitive.Root>
>(({ className, orientation = "horizontal", decorative = true, ...props }, ref) => (
  <SeparatorPrimitive.Root
    ref={ref}
    decorative={decorative}
    orientation={orientation}
    className={cn(
      "shrink-0 bg-[var(--border-subtle)]",
      orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]",
      className
    )}
    {...props}
  />
))
Separator.displayName = SeparatorPrimitive.Root.displayName

// ─────────────────────────────────────────────────────────────────────────────
// TABS
// ─────────────────────────────────────────────────────────────────────────────
const Tabs = TabsPrimitive.Root
const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      "inline-flex h-10 items-center justify-start gap-1 rounded-xl p-1",
      "bg-[var(--surface-2)] border border-[var(--border-subtle)]",
      className
    )}
    {...props}
  />
))
TabsList.displayName = TabsPrimitive.List.displayName

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-lg px-4 py-1.5",
      "text-sm text-[var(--text-tertiary)] font-medium transition-all duration-150",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
      "disabled:pointer-events-none disabled:opacity-50",
      "data-[state=active]:bg-[var(--surface-4)] data-[state=active]:text-[var(--text-primary)]",
      "data-[state=active]:shadow-sm",
      "hover:text-[var(--text-secondary)]",
      className
    )}
    {...props}
  />
))
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn(
      "mt-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
      "animate-fade-in",
      className
    )}
    {...props}
  />
))
TabsContent.displayName = TabsPrimitive.Content.displayName

// ─────────────────────────────────────────────────────────────────────────────
// CARD
// ─────────────────────────────────────────────────────────────────────────────
const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-2)]",
        "shadow-card transition-all duration-150",
        className
      )}
      {...props}
    />
  )
)
Card.displayName = "Card"

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col gap-2 p-6", className)} {...props} />
  )
)
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn("text-base font-semibold leading-none tracking-tight text-[var(--text-primary)]", className)}
      {...props}
    />
  )
)
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p ref={ref} className={cn("text-sm text-[var(--text-tertiary)] leading-relaxed", className)} {...props} />
  )
)
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
  )
)
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex items-center p-6 pt-0", className)} {...props} />
  )
)
CardFooter.displayName = "CardFooter"

export {
  Label,
  Textarea,
  Badge, badgeVariants,
  Progress,
  Separator,
  Tabs, TabsList, TabsTrigger, TabsContent,
  Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
}
