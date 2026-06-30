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

export async function downloadLdapExport(
  baseline: File,
  quercusFile: File,
): Promise<Blob> {
  const formData = new FormData()
  formData.append("baseline", baseline)
  formData.append("quercus", quercusFile)
  const res = await fetch("/ldap/download?format=zip", {
    method: "POST",
    body: formData,
  })
  if (!res.ok) {
    throw new Error(`LDAP export failed: ${res.status}`)
  }
  return res.blob()
}

export async function downloadGoogleExport(
  baseline: File,
  quercusFile: File,
): Promise<Blob> {
  const formData = new FormData()
  formData.append("baseline", baseline)
  formData.append("quercus", quercusFile)
  const res = await fetch("/google/export", {
    method: "POST",
    body: formData,
  })
  if (!res.ok) {
    throw new Error(`Google export failed: ${res.status}`)
  }
  return res.blob()
}
