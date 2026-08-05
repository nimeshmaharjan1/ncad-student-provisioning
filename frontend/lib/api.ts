export interface AuditInfo {
  raw_row_count: number
  cleaned_row_count: number
  filtered_out_status_count: number
  external_students_removed_count: number
  duplicate_rows_detected: number
}

export interface MissingColumnsByFile {
  filename: string
  missing: string[]
}

export interface UploadQuercusResult {
  cleanedQuercusFile: File
  auditInfo: AuditInfo
  sampleRows: Record<string, unknown>[]
  uploadedFiles: string[]
  missingColumns: string[]
  missingColumnsByFile: MissingColumnsByFile[]
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
    missingColumns: uploadJson.missing_columns ?? [],
    missingColumnsByFile: uploadJson.missing_columns_by_file ?? [],
  }
}

export interface ExportErrorDetail {
  detail: string
  error_code: string
  missing_required?: string[]
  missing_optional?: string[]
  present_columns?: string[]
  all_required?: string[]
  all_optional?: string[]
}

export class ExportError extends Error {
  status: number
  exportError: ExportErrorDetail | null

  constructor(status: number, detail: string, exportError: ExportErrorDetail | null) {
    super(detail)
    this.name = "ExportError"
    this.status = status
    this.exportError = exportError
  }
}

async function downloadExport(url: string, formData: FormData): Promise<{ blob: Blob; filename: string }> {
  const res = await fetch(url, { method: "POST", body: formData })
  if (!res.ok) {
    let errorBody: ExportErrorDetail | null = null
    try {
      errorBody = await res.json()
    } catch {
      // response body isn't JSON — fall back to status-only error
    }
    const message = errorBody?.detail ?? `Export failed: ${res.status}`
    throw new ExportError(res.status, message, errorBody)
  }
  const disposition = res.headers.get("Content-Disposition") ?? ""
  const match = disposition.match(/filename="?(.+?)"?$/)
  const filename = match ? match[1] : "export.zip"
  const blob = await res.blob()
  return { blob, filename }
}

export function downloadQuercus(files: File[]): Promise<{ blob: Blob; filename: string }> {
  const formData = new FormData()
  for (const f of files) {
    formData.append("files", f)
  }
  return downloadExport("/quercus/download", formData)
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
    let errorBody: ExportErrorDetail | null = null
    try {
      errorBody = await res.json()
    } catch {
      // not JSON
    }
    const message = errorBody?.detail ?? `Library export failed: ${res.status}`
    throw new ExportError(res.status, message, errorBody)
  }
  const disposition = res.headers.get("Content-Disposition") ?? ""
  const match = disposition.match(/filename="?(.+?)"?$/)
  const filename = match ? match[1] : "library_export.csv"
  const blob = await res.blob()
  return { blob, filename }
}

export interface CanvasStaffRow {
  user_id: string
  integration_id: string
  login_id: string
  password: string
  first_name: string
  last_name: string
  full_name: string
  sortable_name: string
  short_name: string
  email: string
  status: string
}

export interface GenerateCanvasStaffResult {
  rows: CanvasStaffRow[]
  count: number
  warnings: string[]
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let errorBody: ExportErrorDetail | null = null
    try {
      errorBody = await res.json()
    } catch {
      // response body isn't JSON — fall back to status-only error
    }
    const message = errorBody?.detail ?? `Request failed: ${res.status}`
    throw new ExportError(res.status, message, errorBody)
  }
  return res.json()
}

export function generateCanvasStaff(names: string[]): Promise<GenerateCanvasStaffResult> {
  return postJson("/staff/canvas/generate", { names })
}

export async function downloadCanvasStaffExport(
  names: string[],
): Promise<{ blob: Blob; filename: string }> {
  const res = await fetch("/staff/canvas/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ names }),
  })
  if (!res.ok) {
    let errorBody: ExportErrorDetail | null = null
    try {
      errorBody = await res.json()
    } catch {
      // response body isn't JSON — fall back to status-only error
    }
    const message = errorBody?.detail ?? `Canvas staff export failed: ${res.status}`
    throw new ExportError(res.status, message, errorBody)
  }
  const disposition = res.headers.get("Content-Disposition") ?? ""
  const match = disposition.match(/filename="?(.+?)"?$/)
  const filename = match ? match[1] : "canvas_staff.csv"
  const blob = await res.blob()
  return { blob, filename }
}

export interface LibraryStaffPerson {
  name: string
  barcode: string
  gender: string
  registrationDate: string
  expirationDate: string
}

export interface GenerateLibraryStaffResult {
  rows: Record<string, string>[]
  count: number
  warnings: string[]
}

function libraryStaffPayload(people: LibraryStaffPerson[]) {
  return {
    people: people.map((person) => ({
      name: person.name,
      barcode: person.barcode,
      gender: person.gender,
      registration_date: person.registrationDate,
      expiration_date: person.expirationDate,
    })),
  }
}

export function generateLibraryStaff(
  people: LibraryStaffPerson[],
): Promise<GenerateLibraryStaffResult> {
  return postJson("/staff/library/generate", libraryStaffPayload(people))
}

async function downloadJsonExport(
  url: string,
  body: unknown,
  fallbackFilename: string,
): Promise<{ blob: Blob; filename: string }> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let errorBody: ExportErrorDetail | null = null
    try {
      errorBody = await res.json()
    } catch {
      // response body isn't JSON — fall back to status-only error
    }
    const message = errorBody?.detail ?? `Export failed: ${res.status}`
    throw new ExportError(res.status, message, errorBody)
  }
  const disposition = res.headers.get("Content-Disposition") ?? ""
  const match = disposition.match(/filename="?(.+?)"?$/)
  const filename = match ? match[1] : fallbackFilename
  const blob = await res.blob()
  return { blob, filename }
}

export function downloadLibraryStaffExport(
  people: LibraryStaffPerson[],
): Promise<{ blob: Blob; filename: string }> {
  return downloadJsonExport(
    "/staff/library/export",
    libraryStaffPayload(people),
    "library.csv",
  )
}

export function downloadLibraryStaffText(
  people: LibraryStaffPerson[],
): Promise<{ blob: Blob; filename: string }> {
  return downloadJsonExport(
    "/staff/library/export-text",
    libraryStaffPayload(people),
    "library.txt",
  )
}
