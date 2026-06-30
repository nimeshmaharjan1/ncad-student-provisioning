/*
 * Library Export — /library
 *
 * Standalone page — no dependency on the provisioning pipeline.
 *
 * Accepts raw Quercus Library export CSV files (typically 2025 + 2026) and
 * transforms them into the 46-column Library upload schema. The backend does:
 *   - Merge files in upload order
 *   - 8-digit zero-padded ID → Term Email
 *   - Deduplicate by Term Email (keep first)
 *   - Remove "NCAD Elective - External Students"
 *   - Assign borrower category (CEAD / FTUG / FTPG) from course number
 *   - Validate gender (MALE / FEMALE / UNKNOWN)
 *   - Format dates as yyyy-mm-dd
 *
 * Why this is a separate route from /quercus:
 *   Library does not use PipelineContext. It sends files directly to
 *   POST /library/export and downloads the resulting CSV. A separate page
 *   makes the independence visually obvious — there is no "step 5" coupling.
 */

"use client"

import Link from "next/link"
import { ArrowLeft, BookOpen } from "lucide-react"
import { LibraryStep } from "@/components/library-step"

export default function LibraryPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      {/* Back link */}
      <div className="mb-6">
        <Link
          href="/"
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" />
          Home
        </Link>
      </div>

      <div className="rounded-xl border bg-card shadow-xs">
        <div className="border-b px-5 py-3.5">
          <div className="flex items-center gap-3">
            <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <BookOpen className="size-4" />
            </div>
            <div>
              <h1 className="text-sm font-semibold">Library Export</h1>
              <p className="text-xs text-muted-foreground">
                Standalone — upload Quercus Library export files directly. Runs
                independently of the provisioning pipeline.
              </p>
            </div>
          </div>
        </div>
        <div className="px-5 py-4">
          <LibraryStep />
        </div>
      </div>
    </div>
  )
}
