/*
 * Provisioning Pipeline — /quercus
 *
 * Main pipeline page. Flow:
 *   1. Upload raw Quercus CSV files (typically 2025 + 2026)
 *   2. Backend merges, cleans, and deduplicates
 *   3. Cleaned CSV is stored in PipelineContext
 *   4. Once processed, LDAP / Canvas / Google export cards appear
 *
 * Each downstream card:
 *   - Uploads a system-specific baseline CSV
 *   - Sends it + the stored cleaned Quercus file (from PipelineContext) to the backend
 *   - Downloads the resulting ZIP
 *
 * Why cards are hidden before Quercus is processed:
 *   LDAP, Canvas, and Google depend on cleanedQuercusFile from PipelineContext.
 *   If Quercus has not been processed, the downstream cards have no data to send
 *   and the user would see empty upload states. Hiding them avoids confusion.
 */

"use client"

import { useEffect } from "react"
import Link from "next/link"
import { ArrowLeft, Server, Palette, Globe, BookOpen, FileText } from "lucide-react"
import { usePipeline } from "@/lib/pipeline-context"
import { QuercusStep } from "@/components/quercus-step"
import { LdapStep } from "@/components/ldap-step"
import { CanvasStep } from "@/components/canvas-step"
import { GoogleStep } from "@/components/google-step"
import { AthensStep } from "@/components/athens-step"
import { cn } from "@/lib/utils"

function Card({
  icon: Icon,
  title,
  description,
  dimmed = false,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>
  title: string
  description?: string
  dimmed?: boolean
  children: React.ReactNode
}) {
  return (
    <div
      className={cn(
        "rounded-xl border bg-card shadow-xs transition-opacity",
        dimmed && "pointer-events-none opacity-40 select-none",
      )}
    >
      <div className="border-b px-5 py-3.5">
        <div className="flex items-center gap-3">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Icon className="size-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold">{title}</h2>
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
        </div>
      </div>
      <div className="px-5 py-4">{children}</div>
    </div>
  )
}

export default function QuercusPage() {
  const { step1Done, cleanedQuercusFile, uploadedFileNames, reset } = usePipeline()

  useEffect(() => {
    document.title = "Provisioning Pipeline — NCAD Student Provisioning"
  }, [])

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      {/* Back link + header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="size-4" />
            Home
          </Link>
        </div>
        {step1Done && (
          <button
            onClick={reset}
            className="text-xs text-muted-foreground underline underline-offset-2 hover:text-foreground"
          >
            Start over
          </button>
        )}
      </div>

      <h1 className="mb-2 text-xl font-semibold md:text-2xl">Provisioning Pipeline</h1>
      <p className="mb-8 text-sm text-muted-foreground">
        Upload Quercus student data, then generate LDAP, Canvas, Google Workspace, and OpenAthens exports.
      </p>

      {step1Done && cleanedQuercusFile && (
        <div className="mb-6 flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-800">
          <FileText className="size-3.5 shrink-0" />
          <span className="font-medium">Active Quercus file:</span>
          <span>{cleanedQuercusFile.name}</span>
          {uploadedFileNames.length > 1 && (
            <span className="text-muted-foreground">
              (from {uploadedFileNames.join(", ")})
            </span>
          )}
        </div>
      )}

      {/* Quercus upload card — always visible */}
      <Card
        icon={Server}
        title="Quercus — Source of Truth"
        description="Upload and clean student data. Feeds all pipeline exports below."
      >
        <QuercusStep />
      </Card>

      {/* Downstream export cards — visible only after Quercus is processed */}
      {step1Done && (
        <div className="mt-5 grid grid-cols-1 gap-5 md:grid-cols-2">
          <Card
            icon={Server}
            title="LDAP"
            description="Upload baseline CSV to generate LDAP export."
          >
            <LdapStep />
          </Card>
          <Card
            icon={Palette}
            title="Canvas"
            description="Upload baseline CSV to generate Canvas export."
          >
            <CanvasStep />
          </Card>
          <Card
            icon={Globe}
            title="Google Workspace"
            description="Upload baseline CSV to generate Google export."
          >
            <GoogleStep />
          </Card>
          <Card
            icon={BookOpen}
            title="OpenAthens"
            description="Upload baseline CSV to generate OpenAthens export."
          >
            <AthensStep />
          </Card>
        </div>
      )}
    </div>
  )
}
