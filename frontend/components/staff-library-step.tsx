"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { DataTable } from "@/components/data-table"
import {
  generateLibraryStaff,
  downloadLibraryStaffExport,
  downloadLibraryStaffText,
  type GenerateLibraryStaffResult,
  type LibraryStaffPerson,
} from "@/lib/api"
import { useToast } from "@/lib/toast-context"
import { AlertTriangle, Download, FileText, Plus, Sparkles, Trash2 } from "lucide-react"

interface EditorRow {
  id: number
  name: string
  barcode: string
  gender: string
  registrationDate: string
  expirationDate: string
}

let nextRowId = 1

function saveBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const emptyRow = (): EditorRow => ({
  id: nextRowId++,
  name: "",
  barcode: "",
  gender: "",
  registrationDate: "",
  expirationDate: "",
})

export function StaffLibraryStep() {
  const { addToast } = useToast()
  const [rows, setRows] = useState<EditorRow[]>([emptyRow()])
  const [generated, setGenerated] = useState<GenerateLibraryStaffResult | null>(null)
  const [generatedPeople, setGeneratedPeople] = useState<LibraryStaffPerson[]>([])
  const [generating, setGenerating] = useState(false)
  const [downloadingCsv, setDownloadingCsv] = useState(false)
  const [downloadingTxt, setDownloadingTxt] = useState(false)

  const updateRow = (id: number, field: keyof EditorRow, value: string) => {
    setRows((prev) => prev.map((row) => (row.id === id ? { ...row, [field]: value } : row)))
  }

  const addRow = () => {
    setRows((prev) => [...prev, emptyRow()])
  }

  const removeRow = (id: number) => {
    setRows((prev) => (prev.length > 1 ? prev.filter((row) => row.id !== id) : prev))
  }

  const validPeople = rows
    .filter((row) => row.name.trim() !== "")
    .map((row) => ({
      name: row.name.trim(),
      barcode: row.barcode.trim(),
      gender: row.gender.trim(),
      registrationDate: row.registrationDate,
      expirationDate: row.expirationDate,
    }))

  const handleGenerate = async () => {
    if (validPeople.length === 0) {
      addToast({
        type: "error",
        title: "No staff members entered",
        description: "Add at least one row with a name.",
      })
      return
    }
    setGenerating(true)
    try {
      const result = await generateLibraryStaff(validPeople)
      setGenerated(result)
      setGeneratedPeople(validPeople)
      if (result.warnings.length > 0) {
        addToast({
          type: "warning",
          title: `${result.count} row${result.count === 1 ? "" : "s"} generated with warnings`,
          description: "One or more rows are missing a barcode, last name or registration date. Review the warnings below.",
          duration: 8000,
        })
      } else {
        addToast({
          type: "success",
          title: `${result.count} row${result.count === 1 ? "" : "s"} generated`,
          description: "Review the preview below, then download the .txt for SFTP.",
        })
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed to generate library staff rows"
      addToast({
        type: "error",
        title: "Generation failed",
        description: message,
      })
    } finally {
      setGenerating(false)
    }
  }

  const handleDownloadCsv = async () => {
    if (generatedPeople.length === 0) return
    setDownloadingCsv(true)
    try {
      const { blob, filename } = await downloadLibraryStaffExport(generatedPeople)
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
      setDownloadingCsv(false)
    }
  }

  const handleDownloadTxt = async () => {
    if (generatedPeople.length === 0) return
    setDownloadingTxt(true)
    try {
      const { blob, filename } = await downloadLibraryStaffText(generatedPeople)
      saveBlobDownload(blob, filename)
      addToast({
        type: "success",
        title: "TXT downloaded",
        description: `${filename} — tab-delimited, ready for SFTP.`,
      })
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed to download the TXT"
      addToast({
        type: "error",
        title: "Download failed",
        description: message,
      })
    } finally {
      setDownloadingTxt(false)
    }
  }

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <label className="block text-sm font-medium">Staff members</label>
        <div className="overflow-x-auto rounded-md border">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-3 py-2 font-medium text-muted-foreground">Name</th>
                <th className="px-3 py-2 font-medium text-muted-foreground">Library card number</th>
                <th className="px-3 py-2 font-medium text-muted-foreground">Gender (optional)</th>
                <th className="px-3 py-2 font-medium text-muted-foreground">Registration date</th>
                <th className="px-3 py-2 font-medium text-muted-foreground">Expiration date (optional)</th>
                <th className="w-10 px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-b last:border-0">
                  <td className="px-3 py-1.5">
                    <input
                      value={row.name}
                      onChange={(e) => updateRow(row.id, "name", e.target.value)}
                      placeholder="Cian Delaney Byrne"
                      className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
                    />
                  </td>
                  <td className="px-3 py-1.5">
                    <input
                      value={row.barcode}
                      onChange={(e) => updateRow(row.id, "barcode", e.target.value)}
                      placeholder="e.g. 12345678"
                      className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
                    />
                  </td>
                  <td className="px-3 py-1.5">
                    <input
                      value={row.gender}
                      onChange={(e) => updateRow(row.id, "gender", e.target.value)}
                      placeholder="Blank = UNKNOWN"
                      className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
                    />
                  </td>
                  <td className="px-3 py-1.5">
                    <input
                      type="date"
                      value={row.registrationDate}
                      onChange={(e) => updateRow(row.id, "registrationDate", e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                    />
                  </td>
                  <td className="px-3 py-1.5">
                    <input
                      type="date"
                      value={row.expirationDate}
                      onChange={(e) => updateRow(row.id, "expirationDate", e.target.value)}
                      className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                    />
                  </td>
                  <td className="px-3 py-1.5 text-right">
                    <Button
                      size="icon-sm"
                      variant="ghost"
                      onClick={() => removeRow(row.id)}
                      disabled={rows.length <= 1}
                      aria-label="Remove row"
                    >
                      <Trash2 />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Button size="sm" variant="outline" onClick={addRow}>
          <Plus className="size-4" />
          Add row
        </Button>
        <p className="text-xs text-muted-foreground">
          Each row becomes a library patron row: first word = given name, the rest
          = family name. Login = surname(s) + first initial (e.g.{" "}
          <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">
            delaneybyrnec@staff.ncad.ie
          </code>
          ). Borrower category is always <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">FTS</code>.
          Registration and expiration dates apply to each staff member separately.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={handleGenerate} disabled={generating}>
          <Sparkles className="size-4" />
          {generating ? "Generating..." : "Generate rows"}
        </Button>
        <Button
          onClick={handleDownloadCsv}
          disabled={downloadingCsv || generatedPeople.length === 0}
          variant="secondary"
        >
          <Download className="size-4" />
          {downloadingCsv ? "Preparing..." : "Download CSV (review)"}
        </Button>
        <Button
          onClick={handleDownloadTxt}
          disabled={downloadingTxt || generatedPeople.length === 0}
          variant="secondary"
        >
          <FileText className="size-4" />
          {downloadingTxt ? "Preparing..." : "Download TXT (SFTP)"}
        </Button>
      </div>

      <div className="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-xs text-sky-800 dark:border-sky-900/50 dark:bg-sky-950/20 dark:text-sky-300">
        The <strong>CSV</strong> is for your own review only — spreadsheet apps
        (Excel, Google Sheets) may re-format dates to their platform defaults. The{" "}
        <strong>TXT</strong> is tab-delimited with dates kept as{" "}
        <code className="font-mono">YYYY-MM-DD</code>, ready to upload via SFTP.
      </div>

      {generated && generated.warnings.length > 0 && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 shadow-xs dark:border-amber-800/60 dark:bg-amber-950/20">
          <div className="flex items-center gap-3 px-4 py-3">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600 dark:bg-amber-900/50 dark:text-amber-400">
              <AlertTriangle className="size-4" />
            </div>
            <div className="space-y-1.5">
              <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
                Generated with warnings — missing barcodes, last names or registration dates
              </p>
              {generated.warnings.map((warning, i) => (
                <p key={i} className="text-xs text-amber-700 dark:text-amber-400">
                  {warning}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}

      {generated && generated.rows.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold">
            Preview ({generated.count} row{generated.count === 1 ? "" : "s"})
          </h2>
          <DataTable rows={generated.rows as unknown as Record<string, unknown>[]} />
        </div>
      )}
    </div>
  )
}