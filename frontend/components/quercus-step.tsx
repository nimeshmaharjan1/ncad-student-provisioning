"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "motion/react"
import { Button } from "@/components/ui/button"
import { FileUpload } from "@/components/file-upload"
import { DataTable } from "@/components/data-table"
import { AuditSummary } from "@/components/audit-summary"
import { ProcessingProgress } from "@/components/processing-progress"
import { ExportError } from "@/components/export-error"
import { uploadQuercus, type AuditInfo } from "@/lib/api"
import { usePipeline } from "@/lib/pipeline-context"
import { useToast } from "@/lib/toast-context"
import { addExportHistoryEntry } from "@/lib/local-storage"

export function QuercusStep() {
  const { step1Done, setQuercusData, setStepStatus } = usePipeline()
  const { addToast } = useToast()
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
      setStepStatus("quercus", "done")
      addExportHistoryEntry({
        ts: new Date().toISOString(),
        system: "Quercus",
        status: "success",
        rowCount: data.auditInfo.cleaned_row_count,
        fileCount: data.uploadedFiles.length,
      })
      addToast({
        type: "success",
        title: "Quercus data processed",
        description: `${data.auditInfo.cleaned_row_count} cleaned rows from ${data.uploadedFiles.length} file(s)`,
      })
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed to process Quercus files"
      setError(message)
      setStepStatus("quercus", "error")
      addExportHistoryEntry({
        ts: new Date().toISOString(),
        system: "Quercus",
        status: "error",
        rowCount: null,
        fileCount: 0,
        detail: message,
      })
      addToast({
        type: "error",
        title: "Quercus processing failed",
        description: message,
      })
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
            <ProcessingProgress stages={["Uploading files...", "Cleaning data...", "Generating download..."]} duration={5.4} />
          </motion.div>
        )}
      </AnimatePresence>
      {error && <ExportError message={error} detail={null} />}
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
