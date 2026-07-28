"use client"

import { motion } from "motion/react"
import { CheckCircle, FileText } from "lucide-react"
import { cn } from "@/lib/utils"

interface SuccessCardProps {
  system: string
  timestamp: Date
  rowCount?: number
  files?: string[]
  systemIcon?: React.ComponentType<{ className?: string }>
}

export function SuccessCard({ system, timestamp, rowCount, files, systemIcon: SystemIcon }: SuccessCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 dark:border-emerald-900/50 dark:bg-emerald-950/20"
    >
      <div className="flex items-start gap-3">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400">
          {SystemIcon ? <SystemIcon className="size-4" /> : <CheckCircle className="size-4" />}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
              {system} exported successfully
            </p>
            <CheckCircle className="size-3.5 text-emerald-500" />
          </div>
          <p className="mt-0.5 text-xs text-emerald-600 dark:text-emerald-400">
            {timestamp.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}
            {rowCount !== undefined && (
              <> &middot; {rowCount} row{rowCount !== 1 ? "s" : ""}</>
            )}
          </p>
          {files && files.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {files.map((f) => (
                <span
                  key={f}
                  className="inline-flex items-center gap-1 rounded-md bg-emerald-100/70 px-2 py-0.5 text-[10px] font-medium text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400"
                >
                  <FileText className="size-3" />
                  {f}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
