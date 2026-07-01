"use client"

import { useState, useEffect } from "react"
import { motion } from "motion/react"

interface ProcessingProgressProps {
  stages: string[]
  duration?: number
}

/**
 * Animated progress bar with stage labels. Shown during API calls to
 * give the user visibility into what's happening.
 */
export function ProcessingProgress({ stages, duration = 3.6 }: ProcessingProgressProps) {
  const [stage, setStage] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setStage((p) => Math.min(p + 1, stages.length - 1)), 1800)
    return () => clearInterval(t)
  }, [stages.length])

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span className="relative flex size-4">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-primary/40" />
          <span className="relative inline-flex size-4 rounded-full bg-primary" />
        </span>
        {stages[stage]}
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <motion.div
          className="h-full rounded-full bg-primary"
          initial={{ width: "0%" }}
          animate={{ width: "100%" }}
          transition={{ duration, ease: "easeInOut" }}
        />
      </div>
    </div>
  )
}
