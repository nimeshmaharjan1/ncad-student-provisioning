"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "motion/react"
import { Button } from "@/components/ui/button"
import { FileUpload } from "@/components/file-upload"
import { ProcessingProgress } from "@/components/processing-progress"
import { WorkflowChips } from "@/components/workflow-chips"
import { ExportError } from "@/components/export-error"
import { SuccessCard } from "@/components/success-card"
import { downloadAthensExport, ExportError as ExportErrorClass } from "@/lib/api"
import { usePipeline } from "@/lib/pipeline-context"
import { useToast } from "@/lib/toast-context"
import { addExportHistoryEntry } from "@/lib/local-storage"
import { Upload, Check, BookOpen } from "lucide-react"

export function AthensStep() {
  const { step1Done, cleanedQuercusFile, setStepStatus } = usePipeline()
  const { addToast } = useToast()
  const [baselineFile, setBaselineFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorDetail, setErrorDetail] = useState<ExportErrorClass | null>(null)
  const [done, setDone] = useState(false)
  const [doneTs, setDoneTs] = useState<Date | null>(null)

  const handleRun = async () => {
    if (!baselineFile || !cleanedQuercusFile) return
    setLoading(true)
    setError(null)
    setErrorDetail(null)
    setDone(false)
    setDoneTs(null)
    try {
      const { blob, filename } = await downloadAthensExport(baselineFile, cleanedQuercusFile)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
      setDone(true)
      setDoneTs(new Date())
      setStepStatus("athens", "done")
      addExportHistoryEntry({
        ts: new Date().toISOString(),
        system: "OpenAthens",
        status: "success",
        rowCount: null,
        fileCount: filename.endsWith(".zip") ? 2 : 1,
      })
      addToast({
        type: "success",
        title: "OpenAthens export successful",
        description: filename,
      })
    } catch (e) {
      const message = e instanceof Error ? e.message : "Athens export failed"
      if (e instanceof ExportErrorClass) {
        setError(message)
        setErrorDetail(e)
      } else {
        setError(message)
      }
      setStepStatus("athens", "error")
      addExportHistoryEntry({
        ts: new Date().toISOString(),
        system: "OpenAthens",
        status: "error",
        rowCount: null,
        fileCount: 0,
        detail: message,
      })
      addToast({
        type: "error",
        title: "OpenAthens export failed",
        description: message,
      })
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
            <ProcessingProgress stages={["Comparing files...", "Generating download..."]} />
          </motion.div>
        )}
      </AnimatePresence>
      {error && (
        <ExportError
          message={error}
          detail={errorDetail?.exportError ?? null}
        />
      )}
      {done && doneTs && (
        <SuccessCard
          system="OpenAthens"
          timestamp={doneTs}
          systemIcon={BookOpen}
        />
      )}
      {!step1Done && !loading && (
        <p className="text-xs text-muted-foreground">
          Complete Step 1 (Quercus) first.
        </p>
      )}
      <WorkflowChips
        systemId="openathens"
        chips={[
          { number: 4, icon: Upload, title: "Bulk upload to OpenAthens", detail: "Accounts → Bulk Upload in admin.openathens.net", type: "manual" },
          { number: 5, icon: Check, title: "Confirm accounts appear", detail: "Verify new accounts in the user list", type: "manual" },
        ]}
      />
    </div>
  )
}
