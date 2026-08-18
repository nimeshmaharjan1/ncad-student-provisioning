/*
 * Admin Settings — /settings
 *
 * Per-system validation mode toggles. Controls what happens when a Quercus
 * export is missing required columns:
 *   - warn   (default): the export proceeds and the missing columns are
 *     exported as blank, with a warning banner on the export step.
 *   - strict: the export is rejected with a structured 422 error.
 *
 * State lives server-side in backend/app/core/settings.json (gitignored,
 * per-deployment), with env vars (VALIDATION_MODE_<SYSTEM>) taking precedence
 * over anything persisted here.
 */

"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { ArrowLeft, ArrowUpDown, Settings2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  getValidationSettings,
  updateValidationSettings,
  type ValidationMode,
  type ValidationSettings,
} from "@/lib/api"
import { useToast } from "@/lib/toast-context"

const SYSTEM_LABELS: Record<string, string> = {
  ldap: "LDAP",
  canvas: "Canvas",
  google: "Google Workspace",
  athens: "OpenAthens",
  library: "Library",
}

const SOURCE_LABELS: Record<string, string> = {
  default: "Default",
  file: "Saved",
  env: "Environment override",
}

export default function SettingsPage() {
  const { addToast } = useToast()
  const [settings, setSettings] = useState<ValidationSettings | null>(null)
  const [draft, setDraft] = useState<Record<string, ValidationMode> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    document.title = "Settings — NCAD Student Provisioning"
    getValidationSettings()
      .then((data) => {
        setSettings(data)
        setDraft({ ...data.modes })
        setLoading(false)
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Unknown error")
        setLoading(false)
      })
  }, [])

  const hasChanges =
    draft !== null && settings !== null &&
    Object.keys(draft).some((system) => draft[system] !== settings.modes[system])

  const handleSave = async () => {
    if (!draft) return
    setSaving(true)
    try {
      const updated = await updateValidationSettings(draft)
      setSettings(updated)
      setDraft({ ...updated.modes })
      addToast({
        type: "success",
        title: "Settings saved",
        description: "Validation modes updated. Changes apply immediately.",
      })
    } catch (e) {
      addToast({
        type: "error",
        title: "Failed to save settings",
        description: e instanceof Error ? e.message : "Unknown error",
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6">
        <Link
          href="/"
          className="flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Home
        </Link>
      </div>

      <div className="rounded-xl border bg-card shadow-xs">
        <div className="flex items-center gap-3 border-b px-5 py-3.5">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Settings2 className="size-4" />
          </div>
          <div>
            <h1 className="text-sm font-semibold">Validation Settings</h1>
            <p className="text-xs text-muted-foreground">
              Per-system behavior when a Quercus export is missing required
              columns. Changes apply immediately — no redeploy needed.
            </p>
          </div>
        </div>

        <div className="space-y-4 px-5 py-4">
          {loading && (
            <p className="text-sm text-muted-foreground">Loading settings...</p>
          )}

          {!loading && error && (
            <p className="rounded-lg border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm text-destructive">
              Failed to load settings: {error}. Check that the backend is
              running and reachable.
            </p>
          )}

          {!loading && !error && settings && draft && (
            <>
              {settings.systems.map((system) => (
                <div
                  key={system}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-lg border px-4 py-3"
                >
                  <div className="min-w-0">
                    <p className="flex items-center gap-2 text-sm font-semibold">
                      {SYSTEM_LABELS[system] ?? system}
                      <span
                        className={cn(
                          "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide",
                          settings.sources[system] === "env"
                            ? "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
                            : settings.sources[system] === "file"
                              ? "bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300"
                              : "bg-muted text-muted-foreground",
                        )}
                      >
                        <ArrowUpDown className="size-2.5" />
                        {SOURCE_LABELS[settings.sources[system]]}
                      </span>
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {draft[system] === "warn"
                        ? "Missing required columns are auto-added as blank columns, with a warning."
                        : "Missing required columns block the export with an error."}
                      {system === "ldap" &&
                        " Date of Birth is always auto-added with empty values and never blocks (per LDAP admin)."}
                    </p>
                  </div>

                  <div className="flex rounded-lg border p-0.5">
                    {(["warn", "strict"] as const).map((mode) => (
                      <button
                        key={mode}
                        type="button"
                        onClick={() =>
                          setDraft((prev) => (prev ? { ...prev, [system]: mode } : prev))
                        }
                        className={cn(
                          "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                          draft[system] === mode
                            ? mode === "strict"
                              ? "bg-rose-600 text-white"
                              : "bg-amber-500 text-white"
                            : "text-muted-foreground hover:text-foreground",
                        )}
                      >
                        {mode === "warn" ? "Warn" : "Block"}
                      </button>
                    ))}
                  </div>
                </div>
              ))}

              <div className="flex items-center justify-between gap-3 border-t pt-4">
                <p className="text-xs text-muted-foreground">
                  Environment variables (<code className="rounded bg-muted px-1 py-0.5">VALIDATION_MODE_&lt;SYSTEM&gt;</code>)
                  take precedence over saved settings.
                </p>
                <Button
                  type="button"
                  onClick={handleSave}
                  disabled={!hasChanges || saving}
                >
                  {saving ? "Saving..." : "Save changes"}
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
