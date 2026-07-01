"use client"

import Link from "next/link"
import { cn } from "@/lib/utils"

export interface ChipConfig {
  number: number
  icon: React.ComponentType<{ className?: string }>
  title: string
  detail: string
  type: "manual" | "critical"
}

export function WorkflowChips({
  systemId,
  chips,
}: {
  systemId: string
  chips: ChipConfig[]
}) {
  if (chips.length === 0) return null

  return (
    <div className="mt-5 space-y-3 border-t pt-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          What to do after the download
        </p>
        <Link
          href={`/guide#system-${systemId}`}
          className="text-xs font-medium text-primary hover:underline"
        >
          View full guide &rarr;
        </Link>
      </div>

      <div className="space-y-2">
        {chips.map((chip) => (
          <StepTile key={chip.number} chip={chip} systemId={systemId} />
        ))}
      </div>
    </div>
  )
}

function StepTile({
  chip,
  systemId,
}: {
  chip: ChipConfig
  systemId: string
}) {
  const isCritical = chip.type === "critical"
  const Icon = chip.icon

  return (
    <Link
      href={`/guide#system-${systemId}`}
      className={cn(
        "flex items-start gap-3 rounded-lg border p-3 transition-all hover:shadow-sm",
        isCritical
          ? "border-rose-200 bg-rose-50/50 hover:border-rose-300 hover:bg-rose-50 dark:border-rose-800 dark:bg-rose-950/20 dark:hover:border-rose-700 dark:hover:bg-rose-950/30"
          : "border-amber-200 bg-amber-50/50 hover:border-amber-300 hover:bg-amber-50 dark:border-amber-800 dark:bg-amber-950/20 dark:hover:border-amber-700 dark:hover:bg-amber-950/30",
      )}
    >
      <div
        className={cn(
          "flex size-10 shrink-0 items-center justify-center rounded-lg text-base font-bold",
          isCritical
            ? "bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-300"
            : "bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300",
        )}
      >
        {chip.number}
      </div>

      <div className="min-w-0 flex-1 pt-0.5">
        <div className="flex items-center gap-1.5">
          <Icon
            className={cn(
              "size-4 shrink-0",
              isCritical
                ? "text-rose-600 dark:text-rose-400"
                : "text-amber-600 dark:text-amber-400",
            )}
          />
          <p className="text-sm font-semibold">{chip.title}</p>
        </div>
        <p className="mt-0.5 text-xs text-muted-foreground">{chip.detail}</p>
      </div>
    </Link>
  )
}
