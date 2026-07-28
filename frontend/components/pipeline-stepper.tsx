"use client"

import type { StepStatus } from "@/lib/pipeline-context"
import { cn } from "@/lib/utils"
import { Check, Loader, X, Circle } from "lucide-react"

interface Step {
  key: string
  label: string
  subtitle?: string
}

const steps: Step[] = [
  { key: "quercus", label: "Quercus", subtitle: "Source data" },
  { key: "ldap", label: "LDAP", subtitle: "Triangle" },
  { key: "canvas", label: "Canvas", subtitle: "SIS Import" },
  { key: "google", label: "Google", subtitle: "Workspace" },
  { key: "athens", label: "Athens", subtitle: "OpenAthens" },
  { key: "library", label: "Library", subtitle: "Standalone" },
]

function StepIcon({ status }: { status: StepStatus | undefined }) {
  if (status === "done") return <Check className="size-3.5" />
  if (status === "error") return <X className="size-3.5" />
  return <Circle className="size-3" />
}

function StepDot({ status }: { status: StepStatus | undefined }) {
  return (
    <div
      className={cn(
        "flex size-7 items-center justify-center rounded-full border-2 text-[11px] font-bold transition-colors",
        status === "done" && "border-emerald-500 bg-emerald-50 text-emerald-600 dark:border-emerald-400 dark:bg-emerald-950/30 dark:text-emerald-400",
        status === "error" && "border-red-500 bg-red-50 text-red-600 dark:border-red-400 dark:bg-red-950/30 dark:text-red-400",
        !status && "border-muted-foreground/30 bg-card text-muted-foreground/50",
      )}
    >
      <StepIcon status={status} />
    </div>
  )
}

interface PipelineStepperProps {
  stepStatuses: Record<string, StepStatus>
  activeSystem?: string
}

export function PipelineStepper({ stepStatuses, activeSystem }: PipelineStepperProps) {
  return (
    <div className="rounded-xl border bg-card shadow-xs">
      <div className="flex items-center justify-between gap-1 overflow-x-auto px-3 py-3 sm:px-5 sm:py-4">
        {steps.map((step, i) => {
          const status = step.key === "quercus"
            ? (stepStatuses[step.key] || (Object.keys(stepStatuses).length > 0 ? undefined : undefined))
            : stepStatuses[step.key]
          const isActive = step.key === activeSystem

          return (
            <div key={step.key} className="flex items-center gap-1 sm:gap-2">
              <div className="flex flex-col items-center gap-1 min-w-0">
                <StepDot status={status} />
                <div className="text-center">
                  <p
                    className={cn(
                      "text-[10px] font-semibold uppercase tracking-wider sm:text-[11px]",
                      isActive && "text-foreground",
                      !isActive && "text-muted-foreground/70",
                      status === "done" && "text-emerald-600 dark:text-emerald-400",
                      status === "error" && "text-red-600 dark:text-red-400",
                    )}
                  >
                    {step.label}
                  </p>
                  {step.subtitle && (
                    <p className="hidden text-[9px] text-muted-foreground/50 sm:block">
                      {step.subtitle}
                    </p>
                  )}
                </div>
              </div>
              {i < steps.length - 1 && (
                <div className="mx-1 h-px w-3 bg-border sm:mx-2 sm:w-6" />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
