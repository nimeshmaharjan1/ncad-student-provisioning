"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "motion/react"
import { Button } from "@/components/ui/button"
import { FileUpload } from "@/components/file-upload"
import { downloadAthensExport } from "@/lib/api"
import { usePipeline } from "@/lib/pipeline-context"

function ProcessingProgress() {
  const [stage, setStage] = useState(0)
  const stages = ["Comparing files...", "Generating download..."]

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
          transition={{ duration: 3.6, ease: "easeInOut" }}
        />
      </div>
    </div>
  )
}

export function AthensStep() {
  const { step1Done, cleanedQuercusFile } = usePipeline()
  const [baselineFile, setBaselineFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  const handleRun = async () => {
    if (!baselineFile || !cleanedQuercusFile) return
    setLoading(true)
    setError(null)
    try {
      const { blob, filename } = await downloadAthensExport(baselineFile, cleanedQuercusFile)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
      setDone(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Athens export failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <FileUpload
        label="Upload OpenAthens Baseline CSV"
        accept=".csv,.xlsx"
        disabled={!step1Done}
        onFilesSelected={(f) => setBaselineFile(f[0] ?? null)}
      />
      <Button
        onClick={handleRun}
        disabled={!baselineFile || !cleanedQuercusFile || loading}
      >
        {loading ? "Exporting..." : "Run OpenAthens Export"}
      </Button>
      <AnimatePresence>
        {loading && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <ProcessingProgress />
          </motion.div>
        )}
      </AnimatePresence>
      {error && <p className="text-sm text-destructive">{error}</p>}
      {done && !loading && (
        <p className="text-sm text-green-600 dark:text-green-400">
          OpenAthens export downloaded.
        </p>
      )}
      {!step1Done && (
        <p className="text-xs text-muted-foreground">
          Complete Step 1 (Quercus) first.
        </p>
      )}
    </div>
  )
}
