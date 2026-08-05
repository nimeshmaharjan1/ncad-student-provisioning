"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowLeft, Users } from "lucide-react"
import { StaffCanvasStep } from "@/components/staff-canvas-step"
import { cn } from "@/lib/utils"

type ToolId = "canvas" | "library"

const tools: { id: ToolId; label: string; available: boolean }[] = [
  { id: "canvas", label: "Canvas", available: true },
  { id: "library", label: "Library", available: false },
]

export default function StaffPage() {
  const [active, setActive] = useState<ToolId>("canvas")

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      {/* Back link */}
      <div className="mb-6">
        <Link
          href="/"
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" />
          Home
        </Link>
      </div>

      <div className="rounded-xl border bg-card shadow-xs">
        <div className="flex items-center justify-between border-b px-5 py-3.5">
          <div className="flex items-center gap-3">
            <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Users className="size-4" />
            </div>
            <div>
              <h1 className="text-sm font-semibold">Staff Provisioning</h1>
              <p className="text-xs text-muted-foreground">
                Tools for staff accounts. Nothing is stored — rows are produced
                on the fly.
              </p>
            </div>
          </div>
        </div>

        {/* Tool tabs */}
        <div className="flex items-center gap-1 border-b px-5">
          {tools.map((tool) => {
            const isActive = active === tool.id
            return (
              <button
                key={tool.id}
                disabled={!tool.available}
                onClick={() => setActive(tool.id)}
                className={cn(
                  "-mb-px flex items-center gap-2 border-b-2 px-3 py-2.5 text-sm transition-colors",
                  isActive
                    ? "border-primary font-medium text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground",
                  !tool.available && "cursor-not-allowed opacity-50 hover:text-muted-foreground",
                )}
              >
                {tool.label}
                {!tool.available && (
                  <span className="rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                    soon
                  </span>
                )}
              </button>
            )
          })}
        </div>

        <div className="px-5 py-4">
          {active === "canvas" && <StaffCanvasStep />}
          {active === "library" && (
            <p className="text-sm text-muted-foreground">
              The Library staff tool will appear here.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
