"use client"

import { useEffect } from "react"
import Link from "next/link"
import { ArrowLeft, Server, Palette, Globe, BookOpen, Shield, FileText, AlertTriangle, Info, ExternalLink } from "lucide-react"

const section = "flex flex-col gap-1.5"

const heading = "text-lg font-semibold"

const subheading = "text-sm font-medium text-muted-foreground"

const body = "text-sm text-muted-foreground leading-relaxed"

function Badge({ children, variant }: { children: React.ReactNode; variant: "required" | "optional" | "info" }) {
  const styles = {
    required: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
    optional: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
    info: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  }
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${styles[variant]}`}>
      {children}
    </span>
  )
}

const systems = [
  {
    id: "quercus",
    icon: FileText,
    title: "Quercus",
    description: "Source of Truth — Upload and clean student data.",
    required: ["ID Number", "Course Code", "Course Description", "Course Instance Course Year", "Status", "First Name", "Last Name", "Date of Birth"],
    optional: ["Home Mobile Phone"],
    output: "A cleaned, deduplicated CSV with Term Email generated. Feeds all downstream exports.",
  },
  {
    id: "ldap",
    icon: Server,
    title: "LDAP",
    description: "Triangle LDAP server — new student accounts + passcodes.",
    required: ["ID Number", "Course Code", "Course Description", "Course Instance Course Year", "Type", "First Name", "Last Name", "Date of Birth", "Term Email", "LDAP ID"],
    optional: ["Home Mobile Phone"],
    output: "ZIP with 2 files: new_students.csv (with generated passcodes) + updated_baseline.csv.",
    postSteps: ["SFTP upload to Triangle server via Cyberduck", "Email Triangle Service Desk to confirm", "Wait for confirmation before sending student emails"],
  },
  {
    id: "canvas",
    icon: Palette,
    title: "Canvas",
    description: "Canvas SIS Import — student accounts for LMS.",
    required: ["ID Number", "First Name", "Last Name", "Term Email"],
    optional: [],
    output: "ZIP with 2 files: canvas.csv (new users) + canvas_all_pre.csv (updated baseline in SIS format).",
    postSteps: ["SIS Import in Canvas administration", "Upload via FileSender and notify Rene", "Verify no duplicate accounts"],
  },
  {
    id: "google",
    icon: Globe,
    title: "Google Workspace",
    description: "Google Workspace — new accounts + reactivations.",
    required: ["ID Number", "First Name", "Last Name"],
    optional: [],
    output: "ZIP with 2 files: google_upload.csv (new accounts) + google_reactivate.csv (reactivations).",
    postSteps: ["Bulk upload users in Google Admin Console", "Review reactivations, send password reset emails"],
  },
  {
    id: "athens",
    icon: BookOpen,
    title: "OpenAthens",
    description: "OpenAthens — federated access management.",
    required: ["ID Number", "First Name", "Last Name"],
    optional: [],
    output: "ZIP with 2 files: athens_new_users.csv + athens.csv (21-column upload template).",
    postSteps: ["Bulk upload in admin.openathens.net", "Confirm new accounts appear in user list"],
  },
  {
    id: "library",
    icon: BookOpen,
    title: "Library",
    description: "Library system — patron records.",
    required: ["ID Number"],
    optional: ["First Name", "Last Name", "Gender", "Course Code", "Course Instance Start Date", "Course Instance End Date"],
    output: "ZIP with 2 files: library_cleaned.csv + library.csv (46-column template).",
    postSteps: ["SFTP upload to Library system", "Library handles merging automatically"],
  },
]

export default function AboutPage() {
  useEffect(() => {
    document.title = "System Guide — NCAD Student Provisioning"
  }, [])

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-6">
        <Link
          href="/"
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" />
          Home
        </Link>
      </div>

      <div className="mb-8">
        <h1 className="text-2xl font-semibold">NCAD Student Provisioning — System Guide</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Complete documentation for IT staff. This document explains how the system works,
          what each export does, which columns are required, and what to do after downloading.
        </p>
      </div>

      {/* Architecture */}
      <section className="mb-10 space-y-3">
        <h2 className="text-xl font-semibold">Architecture</h2>
        <div className="rounded-xl border bg-card p-5">
          <pre className="overflow-x-auto text-xs leading-relaxed text-muted-foreground font-mono">
            {`Quercus CSV export(s)
        │
        ▼
  preprocess_quercus()  —  merge, clean, deduplicate, assign Type
        │
        ├──→  LDAP     (baseline diff → new students + passcodes)
        ├──→  Canvas   (baseline diff → SIS import)
        ├──→  Google   (baseline diff → upload + reactivation)
        ├──→  Athens   (baseline diff → 21-col template)
        └──→  Library  (direct mapping → 46-col template)`}
          </pre>
        </div>
        <p className={body}>
          Upload one or more Quercus CSV exports. The system merges them, filters by status
          (Registered / Recommend*), removes external students, deduplicates by Term Email,
          and assigns a course Type (CEAD/UG/PG). Each downstream pipeline then compares the
          cleaned data against a system-specific baseline to detect new users.
        </p>
      </section>

      {/* Pipeline Steps */}
      <section className="mb-10 space-y-5">
        <h2 className="text-xl font-semibold">Pipeline Steps</h2>
        {systems.map((sys) => (
          <div key={sys.id} id={`system-${sys.id}`} className="rounded-xl border bg-card shadow-xs scroll-mt-20">
            <div className="flex items-center gap-3 border-b px-5 py-3.5">
              <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <sys.icon className="size-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold">{sys.title}</h3>
                <p className="text-xs text-muted-foreground">{sys.description}</p>
              </div>
            </div>
            <div className="space-y-4 px-5 py-4">
              {/* Required columns */}
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Required Columns</p>
                <div className="flex flex-wrap gap-1.5">
                  {sys.required.map((col) => (
                    <span key={col} className="inline-flex items-center gap-1 rounded-md bg-red-50 px-2 py-1 text-xs text-red-700 dark:bg-red-950/30 dark:text-red-400">
                      <AlertTriangle className="size-3" />
                      {col}
                      <Badge variant="required">Required</Badge>
                    </span>
                  ))}
                </div>
              </div>
              {/* Optional columns */}
              {sys.optional.length > 0 && (
                <div>
                  <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Optional Columns</p>
                  <div className="flex flex-wrap gap-1.5">
                    {sys.optional.map((col) => (
                      <span key={col} className="inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-1 text-xs text-amber-700 dark:bg-amber-950/30 dark:text-amber-400">
                        <Info className="size-3" />
                        {col}
                        <Badge variant="optional">Optional</Badge>
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {/* Output */}
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Output</p>
                <p className="text-sm text-muted-foreground">{sys.output}</p>
              </div>
              {/* Post-export steps */}
              {sys.postSteps && (
                <div>
                  <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">After Download</p>
                  <ol className="list-inside list-decimal space-y-1 text-sm text-muted-foreground">
                    {sys.postSteps.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </div>
        ))}
      </section>

      {/* Error Handling */}
      <section className="mb-10 space-y-3">
        <h2 className="text-xl font-semibold">Error Handling</h2>
        <div className={section}>
          <h3 className={subheading}>Missing Columns</h3>
          <p className={body}>
            If your CSV file is missing a required column, the system returns a clear error
            message listing exactly which columns are missing, which are present, and which
            are optional. You will see:
          </p>
          <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
            <li><strong>Missing Required Columns</strong> (red) — these must be added to your Quercus export settings</li>
            <li><strong>Missing Optional Columns</strong> (amber) — these will be left blank, no action needed</li>
            <li><strong>Present Columns</strong> (green) — already in your file</li>
            <li>A tip explaining how to fix the issue</li>
          </ul>
        </div>
        <div className={section}>
          <h3 className={subheading}>Unexpected Errors</h3>
          <p className={body}>
            If an unexpected server error occurs, the system logs the full error details
            (visible in the backend terminal) and shows a friendly message in the UI.
            Contact IT support with the timestamp and system name.
          </p>
        </div>
      </section>

      {/* GDPR & Privacy */}
      <section id="privacy" className="mb-10 space-y-3">
        <h2 className="text-xl font-semibold">Privacy &amp; Data Handling</h2>
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 dark:border-amber-900/50 dark:bg-amber-950/20">
          <div className="flex items-start gap-3">
            <Shield className="mt-0.5 size-5 shrink-0 text-amber-600 dark:text-amber-400" />
            <div className="space-y-2">
              <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">GDPR Compliance</p>
              <ul className="list-inside list-disc space-y-1 text-sm text-amber-700 dark:text-amber-400">
                <li><strong>Processing is transient.</strong> Your data is never saved on the server. When you upload a CSV file, the system reads it, processes it, and sends the result back to your browser as a download — then it's gone. Nothing is written to disk, stored in a database, or kept. If the server restarts, everything is wiped clean.</li>
                <li><strong>What's stored on your computer (in your browser):</strong> Only simple progress notes — like "LDAP was exported at 2:30pm" or "Step 1 is done" — so you don't lose your place if you refresh the page. <strong>No student names, emails, ID numbers, or any personal details are ever saved.</strong> Just timestamps and row counts.</li>
                <li><strong>Clear all stored data.</strong> Click "Start over" on the pipeline page or "Clear all stored data" in the Export History section at any time to delete everything saved on your computer.</li>
                <li><strong>Server logs.</strong> The backend writes operational logs (errors, warnings). No names, emails, or ID numbers are included in these logs.</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Changelog */}
      <section className="mb-10 space-y-3">
        <h2 className="text-xl font-semibold">Recent Changes</h2>
        <div className="rounded-xl border bg-card">
          <div className="max-h-80 overflow-y-auto divide-y">
            {[
              { date: "2026-08-04", changes: ["Added Privacy at a glance card on the home page — informational, dismissible, no consent tracking", "Explains why public hosting is safe: no database, transient processing", "Added missing-column warnings on Quercus upload — files missing expected columns (e.g. Date of Birth) still process, but a warning card lists exactly which columns are missing from which files so you can recheck before continuing", "Centralised all required/optional column lists into one registry (backend/app/core/quercus_schema.py) — adding a new system is now a one-entry change"] },
              { date: "2026-07-28", changes: ["Added in-app System Guide page (/about)", "Added Pipeline Status Dashboard with visual stepper", "Added Export History log with GDPR-safe localStorage", "Added Toast notifications for exports", "Added Success Cards replacing plain green text", "Added structured error handling (422) for all 5 system endpoints", "Added schema validation with required/optional column checking", "Made Home Mobile Phone column optional in LDAP export", "Added global exception handler with logging", "Added session persistence (pipeline state survives page refresh)", "Added Start Over button on pipeline page"] },
              { date: "2026-07-28 (earlier)", changes: ["Initial structured error handling for LDAP endpoint", "ExportError component for rich error displays", "Fixed frontend pointing to demo backend instead of local"] },
              { date: "Previous releases", changes: ["Initial application with Quercus preprocessing", "LDAP, Canvas, Google, OpenAthens, Library pipelines", "Baseline comparison and diff detection", "Audit summary and data preview"] },
            ].map((release) => (
              <div key={release.date} className="px-5 py-3">
                <p className="text-xs font-semibold text-muted-foreground">{release.date}</p>
                <ul className="mt-1 space-y-0.5">
                  {release.changes.map((change, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="mt-1.5 block size-1 rounded-full bg-muted-foreground/30 shrink-0" />
                      {change}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Links */}
      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Further Reading</h2>
        <div className="flex flex-wrap gap-3">
          <Link href="/guide" className="inline-flex items-center gap-1.5 rounded-lg border bg-card px-4 py-2.5 text-sm font-medium hover:bg-muted transition-colors">
            <ExternalLink className="size-4" />
            Full User Guide
          </Link>
          <Link
            href="/docs/manual-testing"
            className="inline-flex items-center gap-1.5 rounded-lg border bg-card px-4 py-2.5 text-sm font-medium hover:bg-muted transition-colors"
          >
            <FileText className="size-4" />
            Manual Testing Guide
          </Link>
          <Link
            href="/docs/automation-roadmap"
            className="inline-flex items-center gap-1.5 rounded-lg border bg-card px-4 py-2.5 text-sm font-medium hover:bg-muted transition-colors"
          >
            <FileText className="size-4" />
            Automation Roadmap
          </Link>
          <Link
            href="/docs"
            className="inline-flex items-center gap-1.5 rounded-lg border bg-card px-4 py-2.5 text-sm font-medium hover:bg-muted transition-colors"
          >
            <BookOpen className="size-4" />
            All Documentation
          </Link>
        </div>
      </section>
    </div>
  )
}
