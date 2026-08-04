const GDPR_NOTICE_KEY = "_gdpr_notice"
const GDPR_NOTICE_VALUE = "Only non-personal metadata is stored on this device (pipeline progress, export timestamps, row counts, file names). No student or staff personal data is ever saved."
const STORAGE_VERSION_KEY = "_storage_version"
const STORAGE_VERSION = 1
const PRIVACY_NOTICE_HIDDEN_KEY = "_privacy_notice_hidden"

export interface ExportHistoryEntry {
  ts: string
  system: string
  status: "success" | "error"
  rowCount: number | null
  fileCount: number
  detail?: string
}

export interface PipelineState {
  quercusDone: boolean
  uploadedFileNames: string[]
  cleanedQuercusFileName: string | null
}

const PIPELINE_KEY = "pipelineState"
const HISTORY_KEY = "exportHistory"

function isAvailable(): boolean {
  try {
    const k = "_test"
    localStorage.setItem(k, "1")
    localStorage.removeItem(k)
    return true
  } catch {
    return false
  }
}

function getItem<T>(key: string, fallback: T): T {
  if (!isAvailable()) return fallback
  try {
    const raw = localStorage.getItem(key)
    if (raw === null) return fallback
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

function setItem<T>(key: string, value: T): void {
  if (!isAvailable()) return
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // localStorage full or disabled — silently ignore
  }
}

function removeItem(key: string): void {
  if (!isAvailable()) return
  try {
    localStorage.removeItem(key)
  } catch {
    // silently ignore
  }
}

function ensureGdprNotice(): void {
  if (!isAvailable()) return
  try {
    if (!localStorage.getItem(GDPR_NOTICE_KEY)) {
      localStorage.setItem(GDPR_NOTICE_KEY, GDPR_NOTICE_VALUE)
    }
    if (!localStorage.getItem(STORAGE_VERSION_KEY)) {
      localStorage.setItem(STORAGE_VERSION_KEY, String(STORAGE_VERSION))
    }
  } catch {
    // silently ignore
  }
}

export function loadPipelineState(): PipelineState {
  ensureGdprNotice()
  return getItem<PipelineState>(PIPELINE_KEY, {
    quercusDone: false,
    uploadedFileNames: [],
    cleanedQuercusFileName: null,
  })
}

export function savePipelineState(state: PipelineState): void {
  ensureGdprNotice()
  setItem(PIPELINE_KEY, state)
}

export function clearPipelineState(): void {
  removeItem(PIPELINE_KEY)
}

export function loadExportHistory(): ExportHistoryEntry[] {
  ensureGdprNotice()
  return getItem<ExportHistoryEntry[]>(HISTORY_KEY, [])
}

export function saveExportHistory(entries: ExportHistoryEntry[]): void {
  ensureGdprNotice()
  setItem(HISTORY_KEY, entries.slice(0, 50))
}

export function addExportHistoryEntry(entry: ExportHistoryEntry): ExportHistoryEntry[] {
  const history = loadExportHistory()
  history.unshift(entry)
  saveExportHistory(history)
  return history
}

export function clearAllLocalData(): void {
  removeItem(PIPELINE_KEY)
  removeItem(HISTORY_KEY)
}

export function getGdprNoticeText(): string {
  return GDPR_NOTICE_VALUE
}

export function isPrivacyNoticeHidden(): boolean {
  ensureGdprNotice()
  return getItem<boolean>(PRIVACY_NOTICE_HIDDEN_KEY, false)
}

export function hidePrivacyNotice(): void {
  ensureGdprNotice()
  setItem(PRIVACY_NOTICE_HIDDEN_KEY, true)
}

export function showPrivacyNotice(): void {
  removeItem(PRIVACY_NOTICE_HIDDEN_KEY)
}
