"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import {
  ArrowLeft,
  Download,
  Upload,
  Play,
  Mail,
  Clock,
  Shield,
  Palette,
  Globe,
  BookOpen,
  Database,
  Server,
  Search,
  FileSpreadsheet,
  Check,
  AlertTriangle,
  UserPlus,
  FileText,
  Wifi,
  Key,
  Info,
  LogIn,
} from "lucide-react"
import { cn } from "@/lib/utils"

// ── Phase colors ──

const PHASE_META = [
  { id: 1, label: "Export from Quercus", color: "blue" },
  { id: 2, label: "Process Quercus Data", color: "emerald" },
  { id: 3, label: "Process Each System", color: "violet" },
  { id: 4, label: "Send Emails", color: "amber" },
] as const

function phaseStyles(color: string) {
  const map: Record<string, { bg: string; border: string; text: string; dot: string; light: string }> = {
    blue: {
      bg: "bg-blue-50 dark:bg-blue-950/30",
      border: "border-blue-200 dark:border-blue-800",
      text: "text-blue-700 dark:text-blue-300",
      dot: "bg-blue-500",
      light: "bg-blue-100 dark:bg-blue-900/40",
    },
    emerald: {
      bg: "bg-emerald-50 dark:bg-emerald-950/30",
      border: "border-emerald-200 dark:border-emerald-800",
      text: "text-emerald-700 dark:text-emerald-300",
      dot: "bg-emerald-500",
      light: "bg-emerald-100 dark:bg-emerald-900/40",
    },
    violet: {
      bg: "bg-violet-50 dark:bg-violet-950/30",
      border: "border-violet-200 dark:border-violet-800",
      text: "text-violet-700 dark:text-violet-300",
      dot: "bg-violet-500",
      light: "bg-violet-100 dark:bg-violet-900/40",
    },
    amber: {
      bg: "bg-amber-50 dark:bg-amber-950/30",
      border: "border-amber-200 dark:border-amber-800",
      text: "text-amber-700 dark:text-amber-300",
      dot: "bg-amber-500",
      light: "bg-amber-100 dark:bg-amber-900/40",
    },
  }
  return map[color] ?? map.blue
}

// ── System accent colors ──

const SYSTEM_ACCENT: Record<string, { dot: string; line: string; badge: string; badgeBg: string; border: string; bg: string }> = {
  blue: {
    dot: "bg-blue-500",
    line: "bg-blue-200 dark:bg-blue-700",
    badge: "bg-blue-500 text-white",
    badgeBg: "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300",
    border: "border-blue-200 dark:border-blue-800",
    bg: "bg-blue-50/50 dark:bg-blue-950/20",
  },
  rose: {
    dot: "bg-rose-500",
    line: "bg-rose-200 dark:bg-rose-700",
    badge: "bg-rose-500 text-white",
    badgeBg: "bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300",
    border: "border-rose-200 dark:border-rose-800",
    bg: "bg-rose-50/50 dark:bg-rose-950/20",
  },
  emerald: {
    dot: "bg-emerald-500",
    line: "bg-emerald-200 dark:bg-emerald-700",
    badge: "bg-emerald-500 text-white",
    badgeBg: "bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300",
    border: "border-emerald-200 dark:border-emerald-800",
    bg: "bg-emerald-50/50 dark:bg-emerald-950/20",
  },
  amber: {
    dot: "bg-amber-500",
    line: "bg-amber-200 dark:bg-amber-700",
    badge: "bg-amber-500 text-white",
    badgeBg: "bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300",
    border: "border-amber-200 dark:border-amber-800",
    bg: "bg-amber-50/50 dark:bg-amber-950/20",
  },
  violet: {
    dot: "bg-violet-500",
    line: "bg-violet-200 dark:bg-violet-700",
    badge: "bg-violet-500 text-white",
    badgeBg: "bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300",
    border: "border-violet-200 dark:border-violet-800",
    bg: "bg-violet-50/50 dark:bg-violet-950/20",
  },
}

// ── Phase tracker hook ──

function useActivePhase(phaseIds: string[]) {
  const [activePhase, setActivePhase] = useState(1)

  useEffect(() => {
    const handleScroll = () => {
      const offset = window.innerHeight * 0.35
      const scrollY = window.scrollY + offset
      let current = phaseIds[0]
      for (const id of phaseIds) {
        const el = document.getElementById(id)
        if (el && el.offsetTop <= scrollY) {
          current = id
        }
      }
      setActivePhase(Number(current.split("-")[1]))
    }

    window.addEventListener("scroll", handleScroll, { passive: true })
    handleScroll()
    return () => window.removeEventListener("scroll", handleScroll)
  }, [phaseIds])

  return activePhase
}

// ── Sub-components ──

function PhaseBanner({
  number,
  title,
  color,
  description,
}: {
  number: number
  title: string
  color: string
  description?: string
}) {
  const s = phaseStyles(color)
  return (
    <div
      id={`phase-${number}`}
      className={cn("scroll-mt-24 rounded-2xl border px-6 py-5 md:px-8 md:py-6", s.bg, s.border)}
    >
      <div className="flex items-center gap-3">
        <span
          className={cn(
            "flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white",
            s.dot,
          )}
        >
          {number}
        </span>
        <div>
          <p className={cn("text-xs font-semibold uppercase tracking-wider", s.text)}>
            Phase {number}
          </p>
          <h2 className="text-lg font-semibold md:text-xl">{title}</h2>
        </div>
      </div>
      {description && (
        <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      )}
    </div>
  )
}

function TimelineStep({
  number,
  icon: Icon,
  text,
  detail,
  type,
  isLast,
}: {
  number: number
  icon: React.ComponentType<{ className?: string }>
  text: string
  detail?: string
  type: "auto" | "manual" | "critical"
  isLast: boolean
}) {
  const badgeBorder =
    type === "critical"
      ? "border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300"
      : type === "manual"
        ? "border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300"
        : "border-primary/20 bg-primary/10 text-primary"

  const label =
    type === "critical"
      ? "Critical"
      : type === "manual"
        ? "Manual"
        : "Automated"

  return (
    <div className="relative flex gap-4">
      {/* Left column: number + connector */}
      <div className="flex flex-col items-center">
        <div
          className={cn(
            "flex size-8 shrink-0 items-center justify-center rounded-full border text-sm font-bold",
            badgeBorder,
          )}
        >
          {number}
        </div>
        {!isLast && (
          <div className={cn(
            "mt-1 w-px flex-1",
            type === "critical" ? "bg-rose-200 dark:bg-rose-800" :
            type === "manual" ? "bg-amber-200 dark:bg-amber-800" :
            "bg-border"
          )} />
        )}
      </div>

      {/* Right column: content */}
      <div className={cn("flex-1 pb-8", isLast && "pb-0")}>
        <div className="flex items-start gap-3">
          <div
            className={cn(
              "flex size-8 shrink-0 items-center justify-center rounded-lg",
              type === "critical"
                ? "bg-rose-100 text-rose-600 dark:bg-rose-900/40 dark:text-rose-400"
                : type === "manual"
                  ? "bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400"
                  : "bg-primary/10 text-primary",
            )}
          >
            <Icon className="size-4" />
          </div>
          <div className="min-w-0 flex-1 pt-1">
            <div className="flex items-center gap-2">
              <p className="text-sm font-medium">{text}</p>
              <span
                className={cn(
                  "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider",
                  type === "critical"
                    ? "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300"
                    : type === "manual"
                      ? "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300"
                      : "bg-primary/10 text-primary",
                )}
              >
                {label}
              </span>
            </div>
            {detail && (
              <p className="mt-2 text-xs text-muted-foreground">{detail}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function ZipContentsCard({ files }: { files: { file: string; desc: string }[] }) {
  return (
    <div className="relative flex gap-4">
      <div className="flex flex-col items-center">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full border-2 border-dashed border-muted-foreground/30 text-xs font-bold text-muted-foreground/50">
          <Download className="size-3.5" />
        </div>
        <div className="mt-1 w-px flex-1 bg-border" />
      </div>
      <div className="flex-1 pb-8">
        <div className="rounded-lg border bg-card p-4 shadow-xs">
          <div className="mb-2 flex items-center gap-2">
            <FileText className="size-4 text-muted-foreground" />
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              The .zip contains
            </p>
          </div>
          <div className="space-y-2">
            {files.map((f, i) => (
              <div key={i} className="flex items-start gap-2.5 rounded-md bg-muted/50 px-3 py-2">
                <FileSpreadsheet className="mt-0.5 size-4 shrink-0 text-primary" />
                <div>
                  <code className="text-xs font-medium">{f.file}</code>
                  <p className="text-[11px] text-muted-foreground">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function SystemCard({
  icon: Icon,
  title,
  accent,
  autoSteps,
  zipContents,
  manualSteps,
  criticalSteps,
}: {
  icon: React.ComponentType<{ className?: string }>
  title: string
  accent: string
  autoSteps: { number: number; icon: React.ComponentType<{ className?: string }>; text: string; detail?: string }[]
  zipContents: { file: string; desc: string }[]
  manualSteps: { number: number; icon: React.ComponentType<{ className?: string }>; text: string; detail?: string }[]
  criticalSteps?: { number: number; icon: React.ComponentType<{ className?: string }>; text: string; detail?: string }[]
}) {
  const a = SYSTEM_ACCENT[accent] ?? SYSTEM_ACCENT.blue

  return (
    <div
      id={`system-${title.toLowerCase().replace(/\s+/g, "-")}`}
      className={cn("scroll-mt-24 rounded-xl border bg-card shadow-xs", a.border)}
    >
      {/* Header */}
      <div className={cn("flex items-center gap-3 border-b px-5 py-3.5", a.border)}>
        <div className={cn("flex size-8 items-center justify-center rounded-lg", a.badgeBg)}>
          <Icon className="size-4" />
        </div>
        <h3 className="text-sm font-semibold">{title}</h3>
      </div>

      {/* Timeline */}
      <div className="px-5 pb-6 pt-6">
        {/* Automated steps */}
        {autoSteps.map((step, i) => (
          <TimelineStep
            key={`auto-${i}`}
            number={step.number}
            icon={step.icon}
            text={step.text}
            detail={step.detail}
            type="auto"
            isLast={i === autoSteps.length - 1 && zipContents.length === 0 && manualSteps.length === 0 && !criticalSteps}
          />
        ))}

        {/* Zip contents */}
        {zipContents.length > 0 && (
          <ZipContentsCard files={zipContents} />
        )}

        {/* Manual steps */}
        {manualSteps.map((step, i) => (
          <TimelineStep
            key={`manual-${i}`}
            number={step.number}
            icon={step.icon}
            text={step.text}
            detail={step.detail}
            type="manual"
            isLast={i === manualSteps.length - 1 && !criticalSteps}
          />
        ))}

        {/* Critical steps */}
        {criticalSteps?.map((step, i) => (
          <TimelineStep
            key={`critical-${i}`}
            number={step.number}
            icon={step.icon}
            text={step.text}
            detail={step.detail}
            type="critical"
            isLast={true}
          />
        ))}
      </div>
    </div>
  )
}



// ── Page ──

export default function GuidePage() {
  const phaseIds = PHASE_META.map((p) => `phase-${p.id}`)
  const activePhase = useActivePhase(phaseIds)

  useEffect(() => {
    document.title = "User Guide — NCAD Student Provisioning"
  }, [])

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      {/* Back link + header */}
      <div className="mb-6 flex items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" />
          Home
        </Link>
      </div>

      <h1 className="text-2xl font-semibold md:text-3xl">User Guide</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        A complete walkthrough — from exporting Quercus data to sending student
        emails. Each phase is a self-contained section; scroll through or jump
        using the tracker above.
      </p>

      {/* ── Sticky Phase Tracker ── */}
      <div className="sticky top-3 z-30 mt-6 rounded-xl border bg-card/80 px-3 py-2 shadow-xs backdrop-blur-sm md:px-5">
        <div className="flex items-center justify-between gap-1 md:gap-3">
          {PHASE_META.map((p) => {
            const isActive = activePhase === p.id
            const s = phaseStyles(p.color)
            return (
              <a
                key={p.id}
                href={`#phase-${p.id}`}
                onClick={(e) => {
                  e.preventDefault()
                  document.getElementById(`phase-${p.id}`)?.scrollIntoView({ behavior: "smooth" })
                }}
                className={cn(
                  "flex flex-1 flex-col items-center gap-1 rounded-lg px-2 py-1.5 text-center transition-colors md:flex-row md:gap-2 md:px-3 md:text-left",
                  isActive ? s.bg : "hover:bg-muted/50",
                )}
              >
                <span
                  className={cn(
                    "flex size-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white transition-transform md:size-6 md:text-xs",
                    s.dot,
                    isActive && "scale-110",
                  )}
                >
                  {p.id}
                </span>
                <span
                  className={cn(
                    "text-[10px] font-medium leading-tight md:text-xs",
                    isActive ? s.text : "text-muted-foreground",
                  )}
                >
                  {p.label}
                </span>
              </a>
            )
          })}
        </div>
      </div>

      {/* ── PHASE 1: Export from Quercus ── */}
      <section className="mt-8 space-y-5">
        <PhaseBanner
          number={1}
          title="Export from Quercus"
          color="blue"
          description="Do this before opening the provisioning system. You'll need 2 CSV files."
        />

        <div className="space-y-3 pl-4">
          {[
            { icon: Search, text: "Open Quercus Reporting", detail: "eu-quercus.elluciancloud.com → 2nd Reporting → Ad Hoc → Configure Reports" },
            { icon: Search, text: "Search for all students 2025", detail: 'Select the first report (ignore the second)' },
            { icon: FileText, text: "Filter by year 2025, then Download → CSV", detail: "Save as 2025_all_students.csv" },
            { icon: FileText, text: "Repeat for 2026", detail: "Save as 2026_all_students.csv" },
          ].map((step, i) => (
            <div key={i} className="flex items-start gap-3">
              <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400">
                <step.icon className="size-3.5" />
              </div>
              <div className="pt-1">
                <p className="text-sm font-medium">{step.text}</p>
                <p className="text-xs text-muted-foreground">{step.detail}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-xs text-blue-800 dark:border-blue-800 dark:bg-blue-950/30 dark:text-blue-300">
          <Info className="size-4 shrink-0" />
          <span>
            Both files will be uploaded into the system together. It handles merging.
          </span>
        </div>
      </section>

      {/* ── PHASE 2: Process Quercus Data ── */}
      <section className="mt-10 space-y-5">
        <PhaseBanner
          number={2}
          title="Process Quercus Data"
          color="emerald"
          description="Open the system and upload your CSVs. This phase runs entirely in the browser."
        />

        <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 px-5 py-4 dark:border-emerald-800 dark:bg-emerald-950/20">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">
            Getting started
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/quercus"
              className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 transition-colors"
            >
              <Server className="size-3.5" />
              Open provisioning pipeline
            </Link>
            <span className="inline-flex items-center text-xs text-muted-foreground">
              or go to localhost:3000
            </span>
          </div>
        </div>

        <div className="space-y-3 pl-4">
          {[
            { icon: Upload, text: "Upload your CSV files", detail: 'Drag 2025_all_students.csv + 2026_all_students.csv into the upload area on the Quercus card' },
            { icon: Play, text: "Click Process Quercus Files", detail: "Wait for the progress bar to complete" },
            { icon: FileText, text: "Review the results", detail: "Audit summary, preview table, and automatic download of the cleaned CSV" },
            { icon: Download, text: "Keep the downloaded file", detail: "This is your processed Quercus data — save it for reference" },
          ].map((step, i) => (
            <div key={i} className="flex items-start gap-3">
              <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400">
                <step.icon className="size-3.5" />
              </div>
              <div className="pt-1">
                <p className="text-sm font-medium">{step.text}</p>
                <p className="text-xs text-muted-foreground">{step.detail}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300">
          <Check className="size-4 shrink-0" />
          <span>
            Once Quercus is processed, 4 pipeline cards appear below it — one
            for each downstream system.
          </span>
        </div>
      </section>

      {/* ── PHASE 3: Process Each System ── */}
      <section className="mt-10 space-y-5">
        <PhaseBanner
          number={3}
          title="Process Each System"
          color="violet"
          description="Each system has its own card with an automated export followed by manual upload steps."
        />

        <div className="space-y-6">
          {/* LDAP */}
          <SystemCard
            icon={Server}
            title="LDAP"
            accent="blue"
            autoSteps={[
              { number: 1, icon: Upload, text: "Upload the most recent LDAP baseline CSV", detail: "e.g. pre_20260612_ldap.csv from your LDAP_2025/ folder" },
              { number: 2, icon: Play, text: "Click Run LDAP Export" },
              { number: 3, icon: Download, text: "Download the .zip" },
            ]}
            zipContents={[
              { file: "YYYYMMDD_ldap_new_students.csv", desc: "Includes passcodes" },
              { file: "YYYYMMDD_ldap_updated_baseline.csv", desc: "Save as your next baseline" },
            ]}
            manualSteps={[
              { number: 4, icon: Upload, text: "Open your SFTP client and connect to the Triangle LDAP server", detail: "Using Cyberduck" },
              { number: 5, icon: Upload, text: "Upload YYYYMMDD_ldap_new_students.csv" },
              { number: 6, icon: Mail, text: "Email Triangle Service Desk to confirm the upload" },
            ]}
            criticalSteps={[
              { number: 7, icon: Clock, text: "Wait for confirmation that LDAP accounts have been created", detail: "Do not proceed to send any student communications until confirmed" },
            ]}
          />

          {/* Canvas */}
          <SystemCard
            icon={Palette}
            title="Canvas"
            accent="rose"
            autoSteps={[
              { number: 1, icon: Upload, text: "Upload the most recent Canvas baseline CSV", detail: "e.g. canvas_all_pre_20260616.csv from your Canvas_2025/ folder" },
              { number: 2, icon: Play, text: "Click Run Canvas Export" },
              { number: 3, icon: Download, text: "Download the .zip" },
            ]}
            zipContents={[
              { file: "YYYYMMDD_canvas.csv", desc: "Ready for Canvas SIS Import" },
              { file: "YYYYMMDD_canvas_all_pre.csv", desc: "Save as your next baseline" },
            ]}
            manualSteps={[
              { number: 4, icon: LogIn, text: "Log into Canvas administration" },
              { number: 5, icon: Upload, text: "Navigate to SIS Import and upload YYYYMMDD_canvas.csv" },
              { number: 6, icon: Check, text: "Confirm the import completes without errors" },
              { number: 7, icon: Upload, text: "Upload the file via filesender2.heanet.ie and notify Rene" },
              { number: 8, icon: AlertTriangle, text: "Verify no duplicate accounts exist", detail: "Check the Canvas user list for duplicates" },
            ]}
          />

          {/* Google Workspace */}
          <SystemCard
            icon={Globe}
            title="Google Workspace"
            accent="emerald"
            autoSteps={[
              { number: 1, icon: Upload, text: "Upload the most recent Google Workspace baseline CSV", detail: "The bulk export from Google Admin" },
              { number: 2, icon: Play, text: "Click Run Google Export" },
              { number: 3, icon: Download, text: "Download the .zip" },
            ]}
            zipContents={[
              { file: "YYYYMMDD_google_upload.csv", desc: "New accounts with UUID passwords (force-change enabled)" },
              { file: "YYYYMMDD_google_reactivate.csv", desc: "Suspended students who reappeared in Quercus" },
            ]}
            manualSteps={[
              { number: 4, icon: LogIn, text: "Log into Google Workspace Admin Console (student domain)" },
              { number: 5, icon: Upload, text: "Go to Users → Bulk upload users and upload YYYYMMDD_google_upload.csv" },
              { number: 6, icon: Check, text: "New accounts are created with temporary passwords" },
            ]}
            criticalSteps={[
              { number: 7, icon: UserPlus, text: "Review reactivations in YYYYMMDD_google_reactivate.csv", detail: "Check status in Quercus, reactivate in Google Admin, add to correct mailing group (CEAD/UG/PG), send password reset to personal email" },
            ]}
          />

          {/* OpenAthens */}
          <SystemCard
            icon={BookOpen}
            title="OpenAthens"
            accent="amber"
            autoSteps={[
              { number: 1, icon: Upload, text: "Upload the most recent OpenAthens baseline CSV", detail: "The account export from admin.openathens.net" },
              { number: 2, icon: Play, text: "Click Run OpenAthens Export" },
              { number: 3, icon: Download, text: "Download the .zip" },
            ]}
            zipContents={[
              { file: "YYYYMMDD_athens.csv", desc: "Ready for Bulk Upload (21-column template, status = pending)" },
              { file: "YYYYMMDD_athens_new_users.csv", desc: "Debug list for verification" },
            ]}
            manualSteps={[
              { number: 4, icon: LogIn, text: "Log into admin.openathens.net" },
              { number: 5, icon: Upload, text: "Go to Accounts → Bulk Upload and upload YYYYMMDD_athens.csv" },
              { number: 6, icon: Check, text: "Confirm the upload completes and new accounts appear" },
            ]}
          />

          {/* Library */}
          <SystemCard
            icon={Database}
            title="Library"
            accent="violet"
            autoSteps={[
              { number: 1, icon: Upload, text: "Upload the raw Quercus Library export CSVs", detail: "2025 + 2026 files" },
              { number: 2, icon: Play, text: "Click Run Library Export" },
              { number: 3, icon: Download, text: "Download the .zip" },
            ]}
            zipContents={[
              { file: "YYYYMMDD_library.csv", desc: "Ready for SFTP upload (46-column template)" },
              { file: "YYYYMMDD_library_cleaned.csv", desc: "Intermediate file for verification" },
            ]}
            manualSteps={[
              { number: 4, icon: Upload, text: "Open your SFTP client and connect using the Library SFTP credentials", detail: "Provided by John" },
              { number: 5, icon: Upload, text: "Upload YYYYMMDD_library.csv" },
              { number: 6, icon: Check, text: "The Library system handles merging automatically" },
            ]}
          />
        </div>
      </section>

      {/* ── PHASE 4: Send Student Emails ── */}
      <section className="mt-10 space-y-5">
        <PhaseBanner
          number={4}
          title="Send Student Emails"
          color="amber"
          description="The system does not send emails. Use Thunderbird with the Mail Merge add-on for 3 separate campaigns."
        />

        <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-300">
          <AlertTriangle className="size-4 shrink-0" />
          <span>
            All instructions assume Thunderbird is set up with the NCAD email
            account (provided by John).
          </span>
        </div>

        <div className="rounded-xl border border-amber-200 bg-card shadow-xs dark:border-amber-800">
          <div className="flex items-center gap-3 border-b border-amber-200 px-5 py-3.5 dark:border-amber-800">
            <div className="flex size-8 items-center justify-center rounded-lg bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400">
              <Mail className="size-4" />
            </div>
            <h3 className="text-sm font-semibold">Thunderbird Mail Merge</h3>
          </div>

          <div className="px-5 pb-6 pt-6">
            {/* Email 1: LDAP */}
            <div className="relative flex gap-4">
              <div className="flex flex-col items-center">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-full border border-amber-200 bg-amber-50 text-sm font-bold text-amber-700 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
                  1
                </div>
                <div className="mt-1 w-px flex-1 bg-amber-200 dark:bg-amber-800" />
              </div>
              <div className="flex-1 pb-8">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <Key className="size-4 text-amber-600 dark:text-amber-400" />
                  <p className="text-sm font-medium">LDAP Credentials</p>
                  <span className="inline-flex items-center rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-rose-700 dark:bg-rose-900/40 dark:text-rose-300">
                    Wait for LDAP
                  </span>
                </div>
                <div className="space-y-1.5 rounded-lg bg-amber-50/50 px-3 py-2.5 dark:bg-amber-950/20">
                  <div className="flex items-center gap-2 text-xs">
                    <Clock className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-muted-foreground">When:</span>
                    <span>After Triangle confirms LDAP accounts are created</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <FileText className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-muted-foreground">Template:</span>
                    <span>LDAP email template</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <UserPlus className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-muted-foreground">Recipients:</span>
                    <span>YYYYMMDD_ldap_new_students.csv</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <Mail className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-muted-foreground">Tool:</span>
                    <span>Thunderbird → Tools → Mail Merge</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Email 2: Eduroam */}
            <div className="relative flex gap-4">
              <div className="flex flex-col items-center">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-full border border-amber-200 bg-amber-50 text-sm font-bold text-amber-700 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
                  2
                </div>
                <div className="mt-1 w-px flex-1 bg-amber-200 dark:bg-amber-800" />
              </div>
              <div className="flex-1 pb-8">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <Wifi className="size-4 text-amber-600 dark:text-amber-400" />
                  <p className="text-sm font-medium">Eduroam Wi-Fi</p>
                  <span className="inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-amber-700 dark:bg-amber-900/40 dark:text-amber-300">
                    Same recipients
                  </span>
                </div>
                <div className="space-y-1.5 rounded-lg bg-amber-50/50 px-3 py-2.5 dark:bg-amber-950/20">
                  <div className="flex items-center gap-2 text-xs">
                    <Clock className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-muted-foreground">When:</span>
                    <span>After LDAP credentials are sent</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <FileText className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-muted-foreground">Template:</span>
                    <span>Eduroam email template</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <UserPlus className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-muted-foreground">Recipients:</span>
                    <span>YYYYMMDD_ldap_new_students.csv (same file)</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <Mail className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-muted-foreground">Tool:</span>
                    <span>Thunderbird → Tools → Mail Merge</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Email 3: Student Email */}
            <div className="relative flex gap-4">
              <div className="flex flex-col items-center">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-full border border-amber-200 bg-amber-50 text-sm font-bold text-amber-700 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
                  3
                </div>
              </div>
              <div className="flex-1 pb-6">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <Mail className="size-4 text-amber-600 dark:text-amber-400" />
                  <p className="text-sm font-medium">Student Email Details</p>
                  <span className="inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-amber-700 dark:bg-amber-900/40 dark:text-amber-300">
                    Personal emails
                  </span>
                </div>
                <div className="space-y-1.5 rounded-lg bg-amber-50/50 px-3 py-2.5 dark:bg-amber-950/20">
                  <div className="flex items-center gap-2 text-xs">
                    <Clock className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-muted-foreground">When:</span>
                    <span>After LDAP credentials are sent</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <FileText className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-muted-foreground">Template:</span>
                    <span>Student email template</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <UserPlus className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-muted-foreground">Recipients:</span>
                    <span>to_mail file (in Email_2025/ folder)</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <Mail className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-muted-foreground">Tool:</span>
                    <span>Thunderbird → Tools → Mail Merge</span>
                  </div>
                </div>
                <div className="mt-3 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50/50 px-3 py-2 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950/20 dark:text-amber-300">
                  <Info className="size-3.5 shrink-0" />
                  <span>
                    The <code className="rounded bg-amber-100 px-1 py-0.5 text-[11px] dark:bg-amber-900/40">to_mail</code> file is maintained separately and contains personal email addresses, not NCAD student email addresses.
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="mt-12 mb-8">
        <div className="rounded-2xl border bg-gradient-to-br from-primary/5 to-primary/10 px-6 py-8 text-center shadow-xs md:px-10">
          <h2 className="text-lg font-semibold md:text-xl">Ready to start?</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Begin with Phase 1: export your CSVs from Quercus, then head to the
            provisioning pipeline.
          </p>
          <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/quercus"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Server className="size-4" />
              Go to Provisioning Pipeline
            </Link>
            <Link
              href="/library"
              className="inline-flex items-center gap-2 rounded-lg border bg-card px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
            >
              <BookOpen className="size-4" />
              Library Export
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}


