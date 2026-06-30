"use client"

import { useState, useEffect, useRef } from "react"
import { motion, AnimatePresence } from "motion/react"
import { Button } from "@/components/ui/button"
import { FileUpload } from "@/components/file-upload"
import { DataTable } from "@/components/data-table"
import { AuditSummary } from "@/components/audit-summary"
import { uploadQuercus, type AuditInfo } from "@/lib/api"
import { usePipeline } from "@/lib/pipeline-context"
import { cn } from "@/lib/utils"

/*
 * Processing progress bar shown during the Quercus upload + clean step.
 * Animates through two stages (uploading, generating) to give the user
 * visibility into what is happening while they wait.
 */
function ProcessingProgress() {
  const [stage, setStage] = useState(0)
  const stages = ["Uploading files...", "Cleaning data...", "Generating download..."]

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
          transition={{ duration: 5.4, ease: "easeInOut" }}
        />
      </div>
    </div>
  )
}

export function QuercusStep() {
  const { step1Done, setQuercusData } = usePipeline()
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<{
    sampleRows: Record<string, unknown>[]
    auditInfo: AuditInfo
  } | null>(null)

  const handleProcess = async () => {
    if (files.length === 0) return
    setLoading(true)
    setError(null)
    try {
      const data = await uploadQuercus(files)
      setResult({ sampleRows: data.sampleRows, auditInfo: data.auditInfo })
      setQuercusData({
        cleanedQuercusFile: data.cleanedQuercusFile,
        sampleRows: data.sampleRows,
        auditInfo: data.auditInfo,
        uploadedFileNames: data.uploadedFiles,
      })
      const url = URL.createObjectURL(data.cleanedQuercusFile)
      const a = document.createElement("a")
      a.href = url
      a.download = data.cleanedQuercusFile.name
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to process Quercus files")
    } finally {
      setLoading(false)
    }
  }

  if (step1Done && result) {
    return (
      <div className="space-y-4">
        <AuditSummary audit={result.auditInfo} />
        <div>
          <p className="mb-2 text-sm text-muted-foreground">
            Preview (first {result.sampleRows.length} rows):
          </p>
          <DataTable rows={result.sampleRows} />
        </div>
        <p className="text-sm text-green-600 dark:text-green-400">
          Quercus data processed and downloaded.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <FileUpload
        label="Upload Quercus CSV files"
        multiple
        onFilesSelected={setFiles}
      />
      <Button onClick={handleProcess} disabled={files.length === 0 || loading}>
        {loading ? "Processing..." : "Process Quercus Files"}
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
      {result && !loading && (
        <>
          <AuditSummary audit={result.auditInfo} />
          <div>
            <p className="mb-2 text-sm text-muted-foreground">
              Preview (first {result.sampleRows.length} rows):
            </p>
            <DataTable rows={result.sampleRows} />
          </div>
        </>
      )}
    </div>
  )
}
