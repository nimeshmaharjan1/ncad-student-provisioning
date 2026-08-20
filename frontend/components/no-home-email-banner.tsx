"use client"

import { AlertTriangle } from "lucide-react"

interface NoHomeEmailBannerProps {
  students: string[]
}

/**
 * Banner shown after a successful Google export when some new students have
 * no home email on record. They are still included in to_email_3 with a blank
 * email column, so the operator must fill in their personal addresses before
 * running the Mail Merge.
 */
export function NoHomeEmailBanner({ students }: NoHomeEmailBannerProps) {
  return (
    <div className="rounded-xl border border-amber-300 bg-amber-50 shadow-xs dark:border-amber-800/60 dark:bg-amber-950/20">
      <div className="flex items-start gap-3 px-4 py-3">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600 dark:bg-amber-900/50 dark:text-amber-400">
          <AlertTriangle className="size-4" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
            {students.length} student{students.length === 1 ? " has" : "s have"} no home email on record
          </p>
          <p className="mt-0.5 text-xs text-amber-700 dark:text-amber-400">
            These students are still included in{" "}
            <span className="font-medium">to_email_3</span> with a blank email
            column: <span className="font-medium">{students.join(", ")}</span>.
            Add their personal email addresses to the file before running the
            Mail Merge.
          </p>
        </div>
      </div>
    </div>
  )
}