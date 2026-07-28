"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "motion/react"
import { loadExportHistory, clearAllLocalData, type ExportHistoryEntry } from "@/lib/local-storage"
import { CheckCircle, XCircle, Clock, Trash2, ChevronDown, ChevronUp, ShieldAlert } from "lucide-react"
import { cn } from "@/lib/utils"

function formatTime(ts: string): string {
  try {
    const d = new Date(ts)
    return d.toLocaleString(undefined, {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    })
  } catch {
    return ts
  }
}

function HistoryRow({ entry }: { entry: ExportHistoryEntry }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card px-3 py-2.5 text-sm transition-colors hover:bg-muted/50">
      {entry.status === "success" ? (
        <CheckCircle className="size-4 shrink-0 text-emerald-500" />
      ) : (
        <XCircle className="size-4 shrink-0 text-red-500" />
      )}
      <span className="min-w-0 flex-1">
        <span className="font-medium">{entry.system}</span>
        {entry.rowCount !== null && (
          <span className="ml-2 text-xs text-muted-foreground">
            {entry.rowCount} row{entry.rowCount !== 1 ? "s" : ""}
          </span>
        )}
        {entry.detail && (
          <span className="ml-2 text-xs text-muted-foreground">
            {entry.detail}
          </span>
        )}
      </span>
      <span className="flex items-center gap-1 text-xs text-muted-foreground shrink-0">
        <Clock className="size-3" />
        {formatTime(entry.ts)}
      </span>
    </div>
  )
}

export function ExportHistory() {
  const [history, setHistory] = useState<ExportHistoryEntry[]>([])
  const [open, setOpen] = useState(false)

  useEffect(() => {
    setHistory(loadExportHistory())
  }, [])

  const handleClear = () => {
    clearAllLocalData()
    setHistory([])
  }

  if (history.length === 0) return null

  return (
    <div className="rounded-xl border bg-card shadow-xs">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm transition-colors hover:bg-muted/50"
      >
        <span className="font-semibold">Export History ({history.length})</span>
        {open ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="border-t px-4 pb-3 pt-3">
              <div className="mb-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 dark:border-amber-900/50 dark:bg-amber-950/20">
                <ShieldAlert className="mt-0.5 size-4 shrink-0 text-amber-600 dark:text-amber-400" />
                <p className="text-[11px] text-amber-800 dark:text-amber-300">
                  <strong>Privacy:</strong> Only anonymized metadata (timestamps,
                  system names, row counts) is stored locally on this device.
                  No student or staff personal data is saved.{" "}
                  <strong>No names, emails, IDs, or file contents.</strong>
                </p>
              </div>
              <div className="space-y-1.5">
                {history.map((entry, i) => (
                  <HistoryRow key={`${entry.ts}-${i}`} entry={entry} />
                ))}
              </div>
              <button
                type="button"
                onClick={handleClear}
                className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground hover:text-destructive transition-colors"
              >
                <Trash2 className="size-3" />
                Clear all stored data
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
