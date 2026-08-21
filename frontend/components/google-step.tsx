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
import { NoHomeEmailBanner } from "@/components/no-home-email-banner"
import { downloadGoogleExport, ExportError as ExportErrorClass } from "@/lib/api"
import { usePipeline } from "@/lib/pipeline-context"
import { useToast } from "@/lib/toast-context"
import { addExportHistoryEntry } from "@/lib/local-storage"
import { Upload, UserPlus, Globe, AlertTriangle } from "lucide-react"

export function GoogleStep() {
  const { step1Done, cleanedQuercusFile, setStepStatus } = usePipeline()
  const { addToast } = useToast()
  const [baselineFile, setBaselineFile] = useState<File | null>(null)
  const [ldapExportFile, setLdapExportFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorDetail, setErrorDetail] = useState<ExportErrorClass | null>(null)
  const [done, setDone] = useState(false)
  const [doneTs, setDoneTs] = useState<Date | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])
  const [noHomeEmail, setNoHomeEmail] = useState<string[]>([])
  const [missingLdapPasscodes, setMissingLdapPasscodes] = useState<string[]>([])

  const handleRun = async () => {
    if (!baselineFile || !cleanedQuercusFile || !ldapExportFile) return
    setLoading(true)
    setError(null)
    setErrorDetail(null)
    setWarnings([])
    setNoHomeEmail([])
    setMissingLdapPasscodes([])
    setDone(false)
    setDoneTs(null)
    try {
      const { blob, filename, missingRequired, noHomeEmail, missingLdapPasscodes } = await downloadGoogleExport(baselineFile, cleanedQuercusFile, ldapExportFile)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
      setDone(true)
      setDoneTs(new Date())
      setStepStatus("google", "done")
      addExportHistoryEntry({
        ts: new Date().toISOString(),
        system: "Google Workspace",
        status: "success",
        rowCount: null,
        fileCount: filename.endsWith(".zip") ? 4 : 1,
      })
      addToast({
        type: "success",
        title: "Google export successful",
        description: filename,
      })
      setWarnings(missingRequired)
      setNoHomeEmail(noHomeEmail)
      setMissingLdapPasscodes(missingLdapPasscodes)
    } catch (e) {
      const message = e instanceof Error ? e.message : "Google export failed"
      if (e instanceof ExportErrorClass) {
        setError(message)
        setErrorDetail(e)
      } else {
        setError(message)
      }
      setStepStatus("google", "error")
      addExportHistoryEntry({
        ts: new Date().toISOString(),
        system: "Google Workspace",
        status: "error",
        rowCount: null,
        fileCount: 0,
        detail: message,
      })
      addToast({
        type: "error",
        title: "Google export failed",
        description: message,
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <FileUpload
        label="Upload Google Workspace Baseline CSV"
        accept=".csv,.xlsx"
        disabled={!step1Done}
        onFilesSelected={(f) => setBaselineFile(f[0] ?? null)}
      />
      <FileUpload
        label="Upload LDAP Export CSV (from the LDAP step — supplies the real SSO passwords for Email 1)"
        accept=".csv"
        disabled={!step1Done}
        onFilesSelected={(f) => setLdapExportFile(f[0] ?? null)}
      />
      <Button
        onClick={handleRun}
        disabled={!baselineFile || !cleanedQuercusFile || !ldapExportFile || loading}
      >
        {loading ? "Exporting..." : "Run Google Export"}
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
      {warnings.length > 0 && (
        <WarnBanner missingColumns={warnings} system="Google" />
      )}
      {noHomeEmail.length > 0 && (
        <NoHomeEmailBanner students={noHomeEmail} />
      )}
      {missingLdapPasscodes.length > 0 && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-300">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          <span>
            No SSO passcode found in the LDAP export for:{" "}
            <strong>{missingLdapPasscodes.join(", ")}</strong>. Their password
            column in <code>to_email_1_2.csv</code> is blank — fill it in from{" "}
            <code>YYYYMMDD_ldap.csv</code> before sending Email 1.
          </span>
        </div>
      )}
      {done && doneTs && (
        <SuccessCard
          system="Google Workspace"
          timestamp={doneTs}
          systemIcon={Globe}
        />
      )}
      {!step1Done && (
        <p className="text-xs text-muted-foreground">
          Complete Step 1 (Quercus) first.
        </p>
      )}
      <WorkflowChips
        systemId="google-workspace"
        chips={[
          { number: 4, icon: Upload, title: "Bulk upload to Google Workspace", detail: "Users → Bulk upload users in Admin Console", type: "manual" },
          { number: 5, icon: UserPlus, title: "Review reactivations", detail: "Check suspended students, add to mailing groups, send password reset", type: "critical" },
        ]}
      />
    </div>
  )
}
