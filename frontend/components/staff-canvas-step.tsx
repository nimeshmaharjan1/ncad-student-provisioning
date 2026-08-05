"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { DataTable } from "@/components/data-table"
import {
  generateCanvasStaff,
  downloadCanvasStaffExport,
  type CanvasStaffRow,
} from "@/lib/api"
import { useToast } from "@/lib/toast-context"
import { AlertTriangle, Download, Sparkles } from "lucide-react"

function saveBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function linesFromNames(names: string): string[] {
  return names
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
}

export function StaffCanvasStep() {
  const { addToast } = useToast()
  const [names, setNames] = useState("")
  const [rows, setRows] = useState<CanvasStaffRow[] | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])
  const [generatedNames, setGeneratedNames] = useState<string[]>([])
  const [generating, setGenerating] = useState(false)
  const [downloading, setDownloading] = useState(false)

  const handleGenerate = async () => {
    const parsed = linesFromNames(names)
    if (parsed.length === 0) {
      addToast({
        type: "error",
        title: "No names entered",
        description: "Type at least one staff name, one per line.",
      })
      return
    }
    setGenerating(true)
    try {
      const result = await generateCanvasStaff(parsed)
      setRows(result.rows)
      setWarnings(result.warnings ?? [])
      setGeneratedNames(parsed)
      if ((result.warnings ?? []).length > 0) {
        addToast({
          type: "warning",
          title: `${result.count} staff row${result.count === 1 ? "" : "s"} generated with warnings`,
          description: "One or more names have no last name. Review the warnings below.",
          duration: 8000,
        })
      } else {
        addToast({
          type: "success",
          title: `${result.count} staff row${result.count === 1 ? "" : "s"} generated`,
          description: "Review the preview below, then download the CSV.",
        })
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed to generate staff rows"
      addToast({
        type: "error",
        title: "Generation failed",
        description: message,
      })
    } finally {
      setGenerating(false)
    }
  }

  const handleDownload = async () => {
    if (generatedNames.length === 0) return
    setDownloading(true)
    try {
      const { blob, filename } = await downloadCanvasStaffExport(generatedNames)
      saveBlobDownload(blob, filename)
      addToast({
        type: "success",
        title: "CSV downloaded",
        description: filename,
      })
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed to download the CSV"
      addToast({
        type: "error",
        title: "Download failed",
        description: message,
      })
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <label htmlFor="staff-names" className="block text-sm font-medium">
          Staff names
        </label>
        <textarea
          id="staff-names"
          value={names}
          onChange={(e) => setNames(e.target.value)}
          placeholder={"One name per line, e.g.\nCian Delaney Byrne\nRoisin Quigley"}
          rows={4}
          className="w-full resize-y rounded-lg border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
        <p className="text-xs text-muted-foreground">
          Each name becomes a Canvas user: first word = first name, the rest =
          last name. Login = surname(s) + first initial (e.g.{" "}
          <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">
            delaneybyrnec@staff.ncad.ie
          </code>
          ). A single-word name is generated with a warning and a blank last
          name (login = the name itself, e.g.{" "}
          <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">
            cian@staff.ncad.ie
          </code>
          ).
        </p>
      </div>

      <div className="flex items-center gap-3">
        <Button onClick={handleGenerate} disabled={generating}>
          <Sparkles className="size-4" />
          {generating ? "Generating..." : "Generate rows"}
        </Button>
        <Button
          onClick={handleDownload}
          disabled={downloading || generatedNames.length === 0}
          variant="secondary"
        >
          <Download className="size-4" />
          {downloading ? "Preparing download..." : "Download CSV"}
        </Button>
      </div>

      {warnings.length > 0 && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 shadow-xs dark:border-amber-800/60 dark:bg-amber-950/20">
          <div className="flex items-center gap-3 px-4 py-3">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600 dark:bg-amber-900/50 dark:text-amber-400">
              <AlertTriangle className="size-4" />
            </div>
            <div className="space-y-1.5">
              <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
                Generated with warnings — missing last names
              </p>
              {warnings.map((warning, i) => (
                <p key={i} className="text-xs text-amber-700 dark:text-amber-400">
                  {warning}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}

      {rows && rows.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold">Preview ({rows.length} row{rows.length === 1 ? "" : "s"})</h2>
          <DataTable rows={rows as unknown as Record<string, unknown>[]} />
        </div>
      )}
    </div>
  )
}
