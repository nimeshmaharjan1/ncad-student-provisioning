"use client"

import { useState } from "react"
import Link from "next/link"
import { motion, AnimatePresence } from "motion/react"
import { Shield, X } from "lucide-react"

export function PrivacyNotice() {
  const [hidden, setHidden] = useState(false)

  const handleDismiss = () => {
    setHidden(true)
  }

  return (
    <AnimatePresence>
      {!hidden && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, height: 0, marginBottom: 0 }}
          transition={{ duration: 0.25 }}
          className="overflow-hidden"
        >
          <div className="mb-8 rounded-xl border border-blue-200 bg-blue-50 px-5 py-4 dark:border-blue-900/50 dark:bg-blue-950/20">
            <div className="flex items-start gap-3">
              <Shield className="mt-0.5 size-5 shrink-0 text-blue-600 dark:text-blue-400" />
              <div className="min-w-0 flex-1 space-y-2">
                <p className="text-sm font-semibold text-blue-900 dark:text-blue-300">
                  Privacy at a glance
                </p>
                <ul className="list-inside list-disc space-y-1 text-sm text-blue-800 dark:text-blue-400">
                  <li>
                    <strong>Your uploaded data is never saved.</strong>{" "}The
                    system reads your CSV, processes it, and sends the result
                    back as a download — then it&apos;s gone. Nothing is written
                    to disk or stored in a database.
                  </li>
                  <li>
                    <strong>Only simple progress notes</strong>{" "} (timestamps,
                    row counts, system names) are kept on this computer so you
                    don&apos;t lose your place. No names, emails, or ID numbers
                    are ever stored.
                  </li>
                  <li>
                    <strong>Why is it safe to run?</strong>{" "}
                    There is no database, no accounts, and no file
                    storage behind it — uploads are processed and discarded
                    instantly. This instance runs on your own machine; the
                    same code stays transient wherever it runs.
                  </li>
                </ul>
                <Link
                  href="/about#privacy"
                  className="inline-block text-xs font-medium text-blue-700 underline-offset-4 hover:underline dark:text-blue-300"
                >
                  Learn more about how your data is handled
                </Link>
              </div>
              <button
                type="button"
                onClick={handleDismiss}
                aria-label="Hide privacy notice"
                title="Hide"
                className="shrink-0 rounded-md p-1 text-blue-400 transition-colors hover:bg-blue-100 hover:text-blue-700 dark:hover:bg-blue-900/40 dark:hover:text-blue-300"
              >
                <X className="size-4" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
