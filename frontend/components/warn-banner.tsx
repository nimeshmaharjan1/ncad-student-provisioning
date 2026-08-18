"use client"

import { AlertTriangle } from "lucide-react"

interface WarnBannerProps {
  missingColumns: string[]
  system: string
}

/**
 * Banner shown after a successful export that proceeded in warn mode:
 * required columns were missing from the Quercus file, so the system
 * auto-added them as empty columns (e.g. Date of Birth, which the Quercus
 * Discoverer report no longer exports). Admonishes the admin to recheck the
 * file or switch the system to strict mode in Settings.
 */
export function WarnBanner({ missingColumns, system }: WarnBannerProps) {
  return (
    <div className="rounded-xl border border-amber-300 bg-amber-50 shadow-xs dark:border-amber-800/60 dark:bg-amber-950/20">
      <div className="flex items-start gap-3 px-4 py-3">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600 dark:bg-amber-900/50 dark:text-amber-400">
          <AlertTriangle className="size-4" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
            {system} export generated with warnings
          </p>
          <p className="mt-0.5 text-xs text-amber-700 dark:text-amber-400">
            The system auto-added the missing required columns with empty
            values: <span className="font-medium">{missingColumns.join(", ")}</span>.
            Review the exported files before sending them on. Recheck your
            Quercus export settings before uploading, or enable strict mode
            for this system in{" "}
            <a href="/settings" className="underline underline-offset-2">
              Settings
            </a>{" "}
            to block exports with other missing columns. Date of Birth never
            blocks — the LDAP admin requires the column to stay with empty
            values allowed.
          </p>
        </div>
      </div>
    </div>
  )
}
