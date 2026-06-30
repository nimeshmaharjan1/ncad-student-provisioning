/*
 * Dashboard home — landing page.
 *
 * Shows a 2-card grid navigating to the two main sections:
 *   - Provisioning Pipeline (/quercus) — Quercus → LDAP → Canvas → Google
 *   - Library Export (/library) — standalone transformation
 *
 * Status text on the Quercus card reflects whether step 1 has been completed.
 */

"use client"

import { useEffect } from "react"
import Link from "next/link"
import { Database, BookOpen } from "lucide-react"
import { usePipeline } from "@/lib/pipeline-context"

export default function HomePage() {
  const { step1Done } = usePipeline()

  useEffect(() => {
    document.title = "Home — NCAD Student Provisioning"
  }, [])

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold">NCAD Student Provisioning</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload Quercus student data, then generate downstream system exports.
        </p>
      </div>

      <div className="flex flex-col gap-4">
        <Link
          href="/quercus"
          className="group rounded-xl border bg-card p-5 shadow-xs transition-all hover:shadow-md"
        >
          <div className="flex items-start gap-4">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Database className="size-5" />
            </div>
            <div className="min-w-0">
              <h3 className="font-semibold">Provisioning Pipeline</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Upload Quercus CSV files, then generate LDAP, Canvas, and Google
                Workspace exports.
              </p>
              <span className="mt-2 inline-block text-xs font-medium text-primary">
                {step1Done ? "Resume pipeline" : "Start here"}
              </span>
            </div>
          </div>
        </Link>

        <Link
          href="/library"
          className="group rounded-xl border bg-card p-5 shadow-xs transition-all hover:shadow-md"
        >
          <div className="flex items-start gap-4">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <BookOpen className="size-5" />
            </div>
            <div className="min-w-0">
              <h3 className="font-semibold">Library Export</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Standalone — upload Quercus Library export files directly. No
                dependency on the pipeline above.
              </p>
              <span className="mt-2 inline-block text-xs font-medium text-primary">
                Open Library
              </span>
            </div>
          </div>
        </Link>
      </div>
    </div>
  )
}
