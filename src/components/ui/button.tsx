import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-40 active:scale-[0.98]",
  {
    variants: {
      variant: {
        default:
          "bg-gradient-to-br from-gold-500 to-gold-400 text-[hsl(220deg_20%_6%)] font-semibold shadow-gold-sm hover:shadow-gold-md hover:-translate-y-px",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:
          "border border-[var(--border-subtle)] bg-transparent text-[var(--text-secondary)] hover:border-[var(--border-medium)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-3)]",
        secondary:
          "bg-[var(--surface-3)] text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:border-[var(--border-medium)] hover:text-[var(--text-primary)]",
        ghost:
          "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-3)]",
        link:
          "text-[var(--gold)] underline-offset-4 hover:underline p-0 h-auto font-normal",
        gold:
          "border border-[var(--gold-border)] bg-[var(--gold-dim)] text-[var(--gold-light)] hover:bg-[rgba(201,134,26,0.2)] hover:border-[rgba(201,134,26,0.4)]",
      },
      size: {
        default: "h-10 px-5 py-2",
        sm:      "h-8 px-4 text-xs rounded-lg",
        lg:      "h-12 px-8 text-base rounded-xl",
        xl:      "h-14 px-10 text-base rounded-2xl",
        icon:    "h-10 w-10",
        "icon-sm": "h-8 w-8 rounded-lg",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
