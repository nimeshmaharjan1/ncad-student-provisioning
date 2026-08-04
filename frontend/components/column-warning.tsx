"use client"

import type { MissingColumnsByFile } from "@/lib/api"
import { AlertTriangle, FileWarning, XCircle } from "lucide-react"

interface ColumnWarningProps {
  missingColumns: string[]
  missingColumnsByFile: MissingColumnsByFile[]
}

/**
 * Warning card shown after a successful Quercus upload when one or more
 * expected columns are missing from the uploaded files.
 *
 * This is a WARNING, not an error: processing completed and the download
 * happened. The message tells the user to recheck their Quercus export
 * settings before running downstream exports, because those exports
 * (LDAP, Canvas, Google, OpenAthens, Library) will reject the file or
 * produce incomplete output without these columns.
 */
export function ColumnWarning({ missingColumns, missingColumnsByFile }: ColumnWarningProps) {
  return (
    <div className="rounded-xl border border-amber-300 bg-amber-50 shadow-xs dark:border-amber-800/60 dark:bg-amber-950/20">
      <div className="flex items-center gap-3 rounded-t-xl bg-amber-100 px-4 py-3 dark:bg-amber-900/30">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600 dark:bg-amber-900/50 dark:text-amber-400">
          <AlertTriangle className="size-4" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
            Processed with warnings — missing columns
          </p>
          <p className="text-xs text-amber-700 dark:text-amber-400">
            Your files were processed, but some expected columns are missing.
          </p>
        </div>
      </div>

      <div className="space-y-3 px-4 py-4">
        {missingColumnsByFile.length > 0 && (
          <div className="space-y-2">
            {missingColumnsByFile.map((entry) => (
              <div key={entry.filename} className="rounded-lg border border-amber-200 bg-white px-3 py-2.5 dark:border-amber-900/50 dark:bg-card">
                <p className="flex items-center gap-1.5 text-xs font-medium text-amber-900 dark:text-amber-200">
                  <FileWarning className="size-3.5 shrink-0 text-amber-600 dark:text-amber-400" />
                  {entry.filename}
                </p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {entry.missing.map((col) => (
                    <span
                      key={col}
                      className="inline-flex items-center gap-1 rounded-md bg-amber-100 px-2 py-1 text-xs font-medium text-amber-800 dark:bg-amber-900/40 dark:text-amber-300"
                    >
                      <XCircle className="size-3 text-amber-600 dark:text-amber-400" />
                      {col}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-100/60 px-3 py-2.5 dark:border-amber-900/50 dark:bg-amber-900/20">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600 dark:text-amber-400" />
          <div>
            <p className="text-xs font-semibold text-amber-800 dark:text-amber-300">
              Recheck before continuing
            </p>
            <p className="mt-0.5 text-xs text-amber-700 dark:text-amber-400">
              Open your Quercus export settings, make sure all expected columns
              are included, and re-export the CSV before moving on. Downstream
              exports (LDAP, Canvas, Google, OpenAthens, Library) will reject
              the file or produce incomplete output without them.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
