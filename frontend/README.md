# Frontend — NCAD Student Provisioning

Next.js 16 UI with shadcn/ui components. Tailwind CSS v4.

## Pages

| Route | File | Purpose |
|-------|------|---------|
| `/` | `app/page.tsx` | Home — 2-card navigation (Pipeline / Library) |
| `/quercus` | `app/quercus/page.tsx` | Main pipeline: Quercus → LDAP, Canvas, Google, Athens |
| `/library` | `app/library/page.tsx` | Standalone Library export (no pipeline dependency) |
| `/about` | `app/about/page.tsx` | System Guide — full documentation for IT staff |
| `/guide` | `app/guide/page.tsx` | User Guide — step-by-step walkthrough |

## Components

### Step Components (one per pipeline)
| Component | File | Purpose |
|-----------|------|---------|
| `QuercusStep` | `quercus-step.tsx` | Upload Quercus CSVs → process → preview |
| `LdapStep` | `ldap-step.tsx` | Upload LDAP baseline → download ZIP |
| `CanvasStep` | `canvas-step.tsx` | Upload Canvas baseline → download ZIP |
| `GoogleStep` | `google-step.tsx` | Upload Google baseline → download ZIP |
| `AthensStep` | `athens-step.tsx` | Upload Athens baseline → download ZIP |
| `LibraryStep` | `library-step.tsx` | Upload Library CSVs → download ZIP |

### Shared Components
| Component | File | Purpose |
|-----------|------|---------|
| `FileUpload` | `file-upload.tsx` | Reusable drag-and-drop file upload zone |
| `DataTable` | `data-table.tsx` | Preview table for sample rows |
| `AuditSummary` | `audit-summary.tsx` | Row count summary display |
| `ProcessingProgress` | `processing-progress.tsx` | Animated indeterminate progress bar |
| `ExportError` | `export-error.tsx` | Rich error card showing required/optional/missing columns |
| `SuccessCard` | `success-card.tsx` | Animated green success card after export |
| `PipelineStepper` | `pipeline-stepper.tsx` | 6-step visual status dashboard (Quercus → Library) |
| `ExportHistory` | `export-history.tsx` | Collapsible export history log with GDPR notice |
| `ToastViewport` | `toast-viewport.tsx` | Animated slide-in toast notifications |
| `WorkflowChips` | `workflow-chips.tsx` | Post-download manual step cards |
| `NavBar` | `nav-bar.tsx` | Top navigation (Home, Quercus, Library, About, Guide) |

### UI Primitives
| Component | File | Purpose |
|-----------|------|---------|
| `Button` | `ui/button.tsx` | shadcn Button with multiple variants |

## State Management

`lib/pipeline-context.tsx` — React Context storing:
- `cleanedQuercusFile`: the File object from Quercus processing (used by downstream exports)
- `stepStatuses`: `Record<string, "pending" | "done" | "error">` for the stepper dashboard
- `uploadedFileNames`: original file names for display
- `auditInfo` / `sampleRows`: Quercus preprocessing results

Persists across page navigation via React state. Also syncs to localStorage for session persistence (only non-personal metadata: step booleans, file names). Survives page refresh.

## API Layer

`lib/api.ts` — typed fetch wrappers for every backend endpoint.
- `uploadQuercus(files)` — POST `/quercus/upload` → returns JSON + triggers `/quercus/download` for the cleaned CSV
- `downloadLdapExport(baseline, quercusFile)` — POST `/ldap/download?format=zip`
- `downloadCanvasExport(baseline, quercusFile)` — POST `/canvas/export`
- `downloadGoogleExport(baseline, quercusFile)` — POST `/google/export`
- `downloadAthensExport(baseline, quercusFile)` — POST `/athens/export`
- `downloadLibraryExport(files)` — POST `/library/export`

All export functions use a shared `downloadExport()` helper that:
1. POSTs FormData to the endpoint
2. On error: parses the structured JSON response (ExportErrorDetail) and throws an `ExportError` with status + detail + structured error body
3. On success: extracts filename from Content-Disposition header, returns `{ blob, filename }`

### ExportError class
```typescript
export class ExportError extends Error {
  status: number
  exportError: ExportErrorDetail | null  // { detail, error_code, missing_required, ... }
}
```

## Toast System

`lib/toast-context.tsx` + `components/toast-viewport.tsx`:
- `ToastProvider` wraps the app in `layout.tsx`
- `useToast()` hook returns `{ addToast, removeToast, toasts }`
- `addToast({ type: "success" | "error" | "info", title, description, duration? })`
- Toasts auto-dismiss after `duration` ms (default 4000)
- Rendered as animated slide-in cards via `ToastViewport` (fixed position, top-right on desktop)

## Local Storage (GDPR-safe)

`lib/local-storage.ts`:
- `loadPipelineState()` / `savePipelineState()` — persists pipeline step booleans and file names
- `loadExportHistory()` / `saveExportHistory()` / `addExportHistoryEntry()` — persists up to 50 export history entries
- `clearAllLocalData()` — wipes all stored data
- **No PII is ever stored**: only `{ ts, system, status, rowCount, fileCount }` for history, and `{ quercusDone, uploadedFileNames, cleanedQuercusFileName }` for pipeline state
- GDPR notice is automatically written to localStorage on first use

## Proxy Config

`next.config.ts` rewrites `/quercus/*`, `/ldap/*`, `/canvas/*`, `/google/*`, `/athens/*`, `/library/*`, `/export/*` to `http://localhost:8000`.

## Run

```bash
cd frontend
npm install
npm run dev    # → http://localhost:3000
```

For production:
```bash
npm run build
npm run start
```

## Dependencies

Next.js 16, React 19, shadcn/ui, lucide-react, motion (framer-motion), tailwindcss v4, next-themes.

For full developer onboarding, see [`../docs/ONBOARDING.md`](../docs/ONBOARDING.md).
