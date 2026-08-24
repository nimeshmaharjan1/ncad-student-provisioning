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
import { downloadLdapExport, ExportError as ExportErrorClass } from "@/lib/api"
import { usePipeline } from "@/lib/pipeline-context"
import { useToast } from "@/lib/toast-context"
import { addExportHistoryEntry } from "@/lib/local-storage"
import { Upload, Mail, Clock, Server, Info } from "lucide-react"

export function LdapStep() {
  const { step1Done, cleanedQuercusFile, setStepStatus } = usePipeline()
  const { addToast } = useToast()
  const [baselineFile, setBaselineFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorDetail, setErrorDetail] = useState<ExportErrorClass | null>(null)
  const [done, setDone] = useState(false)
  const [doneTs, setDoneTs] = useState<Date | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])

  const handleRun = async () => {
    if (!baselineFile || !cleanedQuercusFile) return
    setLoading(true)
    setError(null)
    setErrorDetail(null)
    setWarnings([])
    setDone(false)
    setDoneTs(null)
    try {
      const { blob, filename, missingRequired } = await downloadLdapExport(baselineFile, cleanedQuercusFile)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
      setDone(true)
      setDoneTs(new Date())
      setStepStatus("ldap", "done")
      addExportHistoryEntry({
        ts: new Date().toISOString(),
        system: "LDAP",
        status: "success",
        rowCount: null,
        fileCount: filename.endsWith(".zip") ? 3 : 1,
      })
      addToast({
        type: "success",
        title: "LDAP export successful",
        description: filename,
      })
      setWarnings(missingRequired)
    } catch (e) {
      const message = e instanceof Error ? e.message : "LDAP export failed"
      if (e instanceof ExportErrorClass) {
        setError(message)
        setErrorDetail(e)
      } else {
        setError(message)
      }
      setStepStatus("ldap", "error")
      addExportHistoryEntry({
        ts: new Date().toISOString(),
        system: "LDAP",
        status: "error",
        rowCount: null,
        fileCount: 0,
        detail: message,
      })
      addToast({
        type: "error",
        title: "LDAP export failed",
        description: message,
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <FileUpload
        label="Upload LDAP Baseline CSV"
        accept=".csv,.xlsx"
        disabled={!step1Done}
        onFilesSelected={(f) => setBaselineFile(f[0] ?? null)}
      />
      <Button
        onClick={handleRun}
        disabled={!baselineFile || !cleanedQuercusFile || loading}
      >
        {loading ? "Exporting..." : "Run LDAP Export"}
      </Button>
      <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-300">
        <Info className="mt-0.5 size-3.5 shrink-0" />
        <span>
          Save your ZIPs before you click Run again — re-running makes new
          passwords that won’t match what you already put into the student
          accounts or emailed. If you need to run again, use the{" "}
          <code>pre_YYYYMMDD_ldap.csv</code> it just gave you as the new
          starting list.
        </span>
      </div>
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
      {warnings.length > 0 && (
        <WarnBanner missingColumns={warnings} system="LDAP" />
      )}
      {done && doneTs && (
        <SuccessCard
          system="LDAP"
          timestamp={doneTs}
          systemIcon={Server}
        />
      )}
      {!step1Done && (
        <p className="text-xs text-muted-foreground">
          Complete Step 1 (Quercus) first.
        </p>
      )}
      <WorkflowChips
        systemId="ldap"
        chips={[
          { number: 4, icon: Upload, title: "SFTP to Triangle server", detail: "Upload via Cyberduck", type: "manual" },
          { number: 5, icon: Mail, title: "Email Triangle Service Desk", detail: "Confirm the upload was received", type: "manual" },
          { number: 6, icon: Clock, title: "Wait for confirmation", detail: "Do not send student emails until LDAP accounts are confirmed", type: "critical" },
        ]}
      />
    </div>
  )
}
