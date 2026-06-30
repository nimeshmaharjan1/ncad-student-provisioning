"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { FileUpload } from "@/components/file-upload"
import { DataTable } from "@/components/data-table"
import { AuditSummary } from "@/components/audit-summary"
import { uploadQuercus, type AuditInfo } from "@/lib/api"
import { usePipeline } from "@/lib/pipeline-context"

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
      {error && <p className="text-sm text-destructive">{error}</p>}
      {result && (
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
