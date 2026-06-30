export interface AuditInfo {
  raw_row_count: number
  cleaned_row_count: number
  filtered_out_status_count: number
  external_students_removed_count: number
  duplicate_rows_detected: number
}

export interface UploadQuercusResult {
  cleanedQuercusFile: File
  auditInfo: AuditInfo
  sampleRows: Record<string, unknown>[]
  uploadedFiles: string[]
}

export async function uploadQuercus(files: File[]): Promise<UploadQuercusResult> {
  const formData = new FormData()
  for (const f of files) {
    formData.append("files", f)
  }

  const uploadRes = await fetch("/quercus/upload", {
    method: "POST",
    body: formData,
  })
  if (!uploadRes.ok) {
    throw new Error(`Quercus upload failed: ${uploadRes.status}`)
  }
  const uploadJson = await uploadRes.json()

  const downloadForm = new FormData()
  for (const f of files) {
    downloadForm.append("files", f)
  }
  const downloadRes = await fetch("/quercus/download", {
    method: "POST",
    body: downloadForm,
  })
  if (!downloadRes.ok) {
    throw new Error(`Quercus download failed: ${downloadRes.status}`)
  }

  const blob = await downloadRes.blob()
  const now = new Date()
  const dateStr = now.toISOString().slice(0, 10).replace(/-/g, "")
  const cleanedQuercusFile = new File([blob], `${dateStr}_quercus.csv`, { type: "text/csv" })

  return {
    cleanedQuercusFile,
    auditInfo: {
      raw_row_count: uploadJson.raw_row_count,
      cleaned_row_count: uploadJson.cleaned_row_count,
      filtered_out_status_count: uploadJson.filtered_out_status_count,
      external_students_removed_count: uploadJson.external_students_removed_count,
      duplicate_rows_detected: uploadJson.duplicate_rows_detected,
    },
    sampleRows: uploadJson.sample_rows,
    uploadedFiles: uploadJson.uploaded_files,
  }
}

async function downloadExport(url: string, formData: FormData): Promise<{ blob: Blob; filename: string }> {
  const res = await fetch(url, { method: "POST", body: formData })
  if (!res.ok) {
    throw new Error(`Export failed: ${res.status}`)
  }
  const disposition = res.headers.get("Content-Disposition") ?? ""
  const match = disposition.match(/filename="?(.+?)"?$/)
  const filename = match ? match[1] : "export.zip"
  const blob = await res.blob()
  return { blob, filename }
}

export function downloadLdapExport(baseline: File, quercusFile: File): Promise<{ blob: Blob; filename: string }> {
  const formData = new FormData()
  formData.append("baseline", baseline)
  formData.append("quercus", quercusFile)
  return downloadExport("/ldap/download?format=zip", formData)
}

export function downloadGoogleExport(baseline: File, quercusFile: File): Promise<{ blob: Blob; filename: string }> {
  const formData = new FormData()
  formData.append("baseline", baseline)
  formData.append("quercus", quercusFile)
  return downloadExport("/google/export", formData)
}

export function downloadAthensExport(baseline: File, quercusFile: File): Promise<{ blob: Blob; filename: string }> {
  const formData = new FormData()
  formData.append("baseline", baseline)
  formData.append("quercus", quercusFile)
  return downloadExport("/athens/export", formData)
}

export function downloadCanvasExport(baseline: File, quercusFile: File): Promise<{ blob: Blob; filename: string }> {
  const formData = new FormData()
  formData.append("baseline", baseline)
  formData.append("quercus", quercusFile)
  return downloadExport("/canvas/export", formData)
}

export async function downloadLibraryExport(files: File[]): Promise<{ blob: Blob; filename: string }> {
  const formData = new FormData()
  for (const f of files) {
    formData.append("files", f)
  }
  const res = await fetch("/library/export", {
    method: "POST",
    body: formData,
  })
  if (!res.ok) {
    throw new Error(`Library export failed: ${res.status}`)
  }
  const disposition = res.headers.get("Content-Disposition") ?? ""
  const match = disposition.match(/filename="?(.+?)"?$/)
  const filename = match ? match[1] : "library_export.csv"
  const blob = await res.blob()
  return { blob, filename }
}
