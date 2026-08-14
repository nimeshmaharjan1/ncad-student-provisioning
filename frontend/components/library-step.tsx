"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "motion/react"
import { Button } from "@/components/ui/button"
import { FileUpload } from "@/components/file-upload"
import { ProcessingProgress } from "@/components/processing-progress"
import { WorkflowChips } from "@/components/workflow-chips"
import { ExportError } from "@/components/export-error"
import { SuccessCard } from "@/components/success-card"
import { WarnBanner } from "@/components/warn-banner"
import { downloadLibraryExport, ExportError as ExportErrorClass } from "@/lib/api"
import { usePipeline } from "@/lib/pipeline-context"
import { useToast } from "@/lib/toast-context"
import { addExportHistoryEntry } from "@/lib/local-storage"
import { Upload, Check, BookOpen } from "lucide-react"

export function LibraryStep() {
  const { setStepStatus } = usePipeline()
  const { addToast } = useToast()
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorDetail, setErrorDetail] = useState<ExportErrorClass | null>(null)
  const [done, setDone] = useState(false)
  const [doneTs, setDoneTs] = useState<Date | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])

  const handleRun = async () => {
    if (!files.length) return
    setLoading(true)
    setError(null)
    setErrorDetail(null)
    setWarnings([])
    setDone(false)
    setDoneTs(null)
    try {
      const { blob, filename, missingRequired } = await downloadLibraryExport(files)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
      setDone(true)
      setDoneTs(new Date())
      setStepStatus("library", "done")
      addExportHistoryEntry({
        ts: new Date().toISOString(),
        system: "Library",
        status: "success",
        rowCount: null,
        fileCount: filename.endsWith(".zip") ? 2 : 1,
      })
      addToast({
        type: "success",
        title: "Library export successful",
        description: filename,
      })
      setWarnings(missingRequired)
    } catch (e) {
      const message = e instanceof Error ? e.message : "Library export failed"
      if (e instanceof ExportErrorClass) {
        setError(message)
        setErrorDetail(e)
      } else {
        setError(message)
      }
      setStepStatus("library", "error")
      addExportHistoryEntry({
        ts: new Date().toISOString(),
        system: "Library",
        status: "error",
        rowCount: null,
        fileCount: 0,
        detail: message,
      })
      addToast({
        type: "error",
        title: "Library export failed",
        description: message,
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <FileUpload
        label="Upload Quercus Library export CSV files"
        multiple
        onFilesSelected={setFiles}
      />
      <Button onClick={handleRun} disabled={files.length === 0 || loading}>
        {loading ? "Exporting..." : "Run Library Export"}
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
            <ProcessingProgress stages={["Processing library data...", "Generating download..."]} />
          </motion.div>
        )}
      </AnimatePresence>
      {error && (
        <ExportError
          message={error}
          detail={errorDetail?.exportError ?? null}
        />
      )}
      {warnings.length > 0 && (
        <WarnBanner missingColumns={warnings} system="Library" />
      )}
      {done && doneTs && (
        <SuccessCard
          system="Library"
          timestamp={doneTs}
          systemIcon={BookOpen}
        />
      )}
      <WorkflowChips
        systemId="library"
        chips={[
          { number: 4, icon: Upload, title: "SFTP upload to Library system", detail: "Connect using the Library SFTP credentials from John", type: "manual" },
          { number: 5, icon: Check, title: "Library handles merging", detail: "Just upload the file and the system does the rest", type: "manual" },
        ]}
      />
    </div>
  )
}
