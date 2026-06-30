"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { FileUpload } from "@/components/file-upload"
import { downloadGoogleExport } from "@/lib/api"
import { usePipeline } from "@/lib/pipeline-context"

export function GoogleStep() {
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
      const blob = await downloadGoogleExport(baselineFile, cleanedQuercusFile)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = "google_export.zip"
      a.click()
      URL.revokeObjectURL(url)
      setDone(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Google export failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <FileUpload
        label="Upload Google Workspace Baseline CSV"
        disabled={!step1Done}
        onFilesSelected={(f) => setBaselineFile(f[0] ?? null)}
      />
      <Button
        onClick={handleRun}
        disabled={!baselineFile || !cleanedQuercusFile || loading}
      >
        {loading ? "Exporting..." : "Run Google Export"}
      </Button>
      {error && <p className="text-sm text-destructive">{error}</p>}
      {done && (
        <p className="text-sm text-green-600 dark:text-green-400">
          Google export downloaded.
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
