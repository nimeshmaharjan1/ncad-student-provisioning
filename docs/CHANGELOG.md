# Changelog

## 2026-08-05

### Canvas Staff Tool
- Added `POST /staff/canvas/generate` (preview JSON) and `POST /staff/canvas/export` (CSV download) endpoints
- New `/staff` page with tool tabs: type staff names one per line, preview the Canvas rows, download `YYYYMMDD_canvas_staff.csv`
- Login rule: surname(s) + first initial, letters only, lowercased (e.g. `Cian Delaney Byrne` → `delaneybyrnec@staff.ncad.ie`)
- Single-word names (no last name) are generated with a warning and blank last name (login = name lowercased) instead of being rejected
- Output uses the same 11-column Canvas schema as the student pipeline; nothing is stored server-side
- Added Canvas staff assertions to `backend/samples/test_pipelines.py`

### Library Staff Tool
- Added `POST /staff/library/generate` (preview JSON), `POST /staff/library/export` (review CSV) and `POST /staff/library/export-text` (tab-delimited `.txt` for SFTP) endpoints
- New **Library** tab on the `/staff` page: row editor with name, library card number (barcode) and optional gender per staff member; registration date picker (required) + optional expiration date picker
- Output reuses the 46-column library schema from the student pipeline: `borrowerCategory = FTS`, `idAtSource` = login, `emailAddress` = `login@staff.ncad.ie`, `gender` = typed value or `UNKNOWN` when blank, dates always written `YYYY-MM-DD`
- Downloads: `YYYYMMDD_library.csv` (for review — spreadsheet apps may re-format dates) and `YYYYMMDDlibrary.txt` (tab-delimited, dates untouched, ready for SFTP)
- Missing barcode or missing last name → row generated with a warning, so it can be completed before the SFTP upload
- Added Library staff assertions to `backend/samples/test_pipelines.py`

## 2026-08-04

### UX & Privacy
- Added "Privacy at a glance" informational card on the home page (dismissible, no consent tracking)
- Card explains what is/isn't stored and why public hosting is safe (transient processing, no database)
- Added "Show privacy notice again" restore link in the `/about` Privacy section

### Quercus Schema Registry & Missing-Column Warnings
- Added `backend/app/core/quercus_schema.py` — single source of truth for all systems' required/optional Quercus columns
- All 5 export endpoints (LDAP, Canvas, Google, OpenAthens, Library) refactored to use the registry (removed ~30 duplicated lines each)
- Added two validation modes: STRICT (exports → 422) and WARN (Quercus upload → warning card, never blocks)
- Quercus upload now returns `missing_columns` + `missing_columns_by_file` — per-file missing column warnings
- Added `ColumnWarning` component — amber card listing which files are missing which columns, with a "recheck before continuing" tip
- Added `warning` toast type; Quercus step shows "processed with warnings" toast when columns are missing
- "How to add a new system" = add one entry to `SCHEMAS` — validation and upload warnings pick it up automatically (documented in backend README)

### Testing
- Added `docs/MANUAL_TESTING.md` — step-by-step manual test guide (what to change in input files to trigger each scenario), linked from the in-app `/about` page

### Planning
- Added `docs/AUTOMATION_ROADMAP.md` — master project document for the manager: end goal (weekly zero-touch automation), scheduler concept, harsh realities/blockers with workarounds, phased plan, and a credentials & access checklist (what credentials are needed, who to ask, where to get them, fallbacks)

## 2026-07-28

### UX & Documentation
- Added in-app System Guide page at `/about` with full documentation
- Added "About" link to navigation bar
- Added Pipeline Status Dashboard (visual stepper: Quercus → LDAP → Canvas → Google → Athens → Library)
- Added Export History log with GDPR-safe localStorage (anonymized metadata only, max 50 entries, clear button)
- Added Toast notifications for export success/failure
- Added Success Cards (animated green cards replacing plain green text)
- Added Start Over button on pipeline page
- Added session persistence — pipeline state survives page refresh
- Added privacy notice banner in Export History

### Error Handling (all endpoints)
- Added global exception handler with logging in `backend/app/main.py`
- Added structured 422 JSON responses for missing required columns (LDAP, Canvas, Google, OpenAthens, Library)
- Added per-module logging (`logger.exception()` with full traceback)
- Added try/except with 400/422/500 error codes in all route handlers
- Frontend: `ExportError` component with rich column-level error display
- Frontend: `ExportError` class in `api.ts` parses structured error JSON
- Frontend: All 6 step components (Quercus, LDAP, Canvas, Google, Athens, Library) now use `ExportError`

### Schema Changes
- Made `Home Mobile Phone` optional in LDAP Quercus schema validation
- Added `QUERCUS_SCHEMA_OPTIONAL_COLUMNS` — optional columns are logged but don't block processing
- Added per-system required/optional column lists for Canvas, Google, Athens, Library

## Previous Releases

### Initial Application
- Quercus CSV upload → merge → clean → deduplicate → preview
- LDAP pipeline: baseline diff, new students with passcodes, updated baseline
- Canvas pipeline: baseline diff, SIS format output
- Google Workspace pipeline: baseline diff, upload + reactivation export
- OpenAthens pipeline: baseline diff, 21-column upload template
- Library pipeline: standalone clean → 46-column template
- Audit summary, data preview table
- Start scripts (start.bat, start.sh) with dependency checks
- Dark/light theme toggle
- User guide at /guide
