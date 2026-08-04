"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "motion/react"
import { Button } from "@/components/ui/button"
import { FileUpload } from "@/components/file-upload"
import { DataTable } from "@/components/data-table"
import { AuditSummary } from "@/components/audit-summary"
import { ProcessingProgress } from "@/components/processing-progress"
import { ExportError } from "@/components/export-error"
import { ColumnWarning } from "@/components/column-warning"
import { uploadQuercus, downloadQuercus, type AuditInfo, type MissingColumnsByFile } from "@/lib/api"
import { usePipeline } from "@/lib/pipeline-context"
import { useToast } from "@/lib/toast-context"
import { addExportHistoryEntry } from "@/lib/local-storage"
import { Download } from "lucide-react"

function saveBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function DownloadAnywayButton({
  downloading,
  onDownload,
}: {
  downloading: boolean
  onDownload: () => void
}) {
  return (
    <Button onClick={onDownload} disabled={downloading} variant="secondary" size="sm">
      <Download className="size-4" />
      {downloading ? "Preparing download..." : "Download cleaned file anyway"}
    </Button>
  )
}

export function QuercusStep() {
  const { step1Done, setQuercusData, setStepStatus } = usePipeline()
  const { addToast } = useToast()
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [missingColumns, setMissingColumns] = useState<string[]>([])
  const [missingColumnsByFile, setMissingColumnsByFile] = useState<MissingColumnsByFile[]>([])
  const [processedFiles, setProcessedFiles] = useState<File[]>([])
  const [reUploadFiles, setReUploadFiles] = useState<File[]>([])
  const [downloading, setDownloading] = useState(false)
  const [downloaded, setDownloaded] = useState(false)
  const [result, setResult] = useState<{
    sampleRows: Record<string, unknown>[]
    auditInfo: AuditInfo
  } | null>(null)

  const handleDownloadNow = async () => {
    if (processedFiles.length === 0) return
    setDownloading(true)
    try {
      const { blob, filename } = await downloadQuercus(processedFiles)
      saveBlobDownload(blob, filename)
      setDownloaded(true)
      addToast({
        type: "success",
        title: "Cleaned file downloaded",
        description: filename,
      })
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed to download the cleaned file"
      addToast({
        type: "error",
        title: "Download failed",
        description: message,
      })
    } finally {
      setDownloading(false)
    }
  }

  const handleProcess = async (processFiles: File[] = files) => {
    if (processFiles.length === 0) return
    setLoading(true)
    setError(null)
    setMissingColumns([])
    setMissingColumnsByFile([])
    setDownloaded(false)
    try {
      const data = await uploadQuercus(processFiles)
      setProcessedFiles(processFiles)
      setResult({ sampleRows: data.sampleRows, auditInfo: data.auditInfo })
      setMissingColumns(data.missingColumns)
      setMissingColumnsByFile(data.missingColumnsByFile)
      setQuercusData({
        cleanedQuercusFile: data.cleanedQuercusFile,
        sampleRows: data.sampleRows,
        auditInfo: data.auditInfo,
        uploadedFileNames: data.uploadedFiles,
      })
      setStepStatus("quercus", "done")
      addExportHistoryEntry({
        ts: new Date().toISOString(),
        system: "Quercus",
        status: "success",
        rowCount: data.auditInfo.cleaned_row_count,
        fileCount: data.uploadedFiles.length,
      })
      if (data.missingColumns.length > 0) {
        addToast({
          type: "warning",
          title: "Quercus processed with warnings",
          description: `Missing columns: ${data.missingColumns.join(", ")}. Recheck your Quercus export settings before continuing.`,
          duration: 8000,
        })
      } else {
        const { blob, filename } = await downloadQuercus(processFiles)
        saveBlobDownload(blob, filename)
        setDownloaded(true)
        addToast({
          type: "success",
          title: "Quercus data processed",
          description: `${data.auditInfo.cleaned_row_count} cleaned rows from ${data.uploadedFiles.length} file(s)`,
        })
      }
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
    const hasWarnings = missingColumns.length > 0
    return (
      <div className="space-y-4">
        {hasWarnings && (
          <>
            <ColumnWarning
              missingColumns={missingColumns}
              missingColumnsByFile={missingColumnsByFile}
            />
            {!downloaded && (
              <div className="flex flex-wrap items-center gap-3">
                <DownloadAnywayButton
                  downloading={downloading}
                  onDownload={handleDownloadNow}
                />
                <p className="text-xs text-muted-foreground">
                  Processing finished — download the cleaned file when you're ready.
                </p>
              </div>
            )}
            <div className="rounded-xl border border-border bg-muted/30 px-4 py-4">
              <p className="text-sm font-semibold">Upload corrected files</p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Re-export the CSV with the missing columns included, then process it here to replace the current data.
              </p>
              <div className="mt-3 space-y-3">
                <FileUpload
                  label="Upload corrected Quercus CSV files"
                  multiple
                  onFilesSelected={setReUploadFiles}
                />
                <Button
                  onClick={() => handleProcess(reUploadFiles)}
                  disabled={reUploadFiles.length === 0 || loading}
                >
                  {loading ? "Processing..." : "Process Corrected Files"}
                </Button>
              </div>
            </div>
          </>
        )}
        <AuditSummary audit={result.auditInfo} />
        <div>
          <p className="mb-2 text-sm text-muted-foreground">
            Preview (first {result.sampleRows.length} rows):
          </p>
          <DataTable rows={result.sampleRows} />
        </div>
        <p
          className={
            hasWarnings
              ? "text-sm text-amber-600 dark:text-amber-400"
              : "text-sm text-green-600 dark:text-green-400"
          }
        >
          {hasWarnings
            ? downloaded
              ? "Cleaned file downloaded — review the warnings above before continuing."
              : "Quercus data processed — review the warnings above, then download the cleaned file."
            : "Quercus data processed and downloaded."}
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
      <Button onClick={() => handleProcess()} disabled={files.length === 0 || loading}>
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
          {missingColumns.length > 0 && (
            <>
              <ColumnWarning
                missingColumns={missingColumns}
                missingColumnsByFile={missingColumnsByFile}
              />
              {!downloaded && (
                <DownloadAnywayButton
                  downloading={downloading}
                  onDownload={handleDownloadNow}
                />
              )}
            </>
          )}
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
