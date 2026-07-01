"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "motion/react"
import { Button } from "@/components/ui/button"
import { FileUpload } from "@/components/file-upload"
import { ProcessingProgress } from "@/components/processing-progress"
import { downloadLibraryExport } from "@/lib/api"

export function LibraryStep() {
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  const handleRun = async () => {
    if (files.length === 0) return
    setLoading(true)
    setError(null)
    setDone(false)
    try {
      const { blob, filename } = await downloadLibraryExport(files)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
      setDone(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Library export failed")
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
      {error && <p className="text-sm text-destructive">{error}</p>}
      {done && (
        <p className="text-sm text-green-600 dark:text-green-400">
          Library export downloaded.
        </p>
      )}
    </div>
  )
}
