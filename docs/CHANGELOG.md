# Changelog

## 2026-08-19

### Self-healing launcher & shared-drive operating model
- `scripts/bootstrap.py` (new): the launchers now self-heal every setup step —
  venv + Python deps (reinstall when `requirements.txt` changes), a hard
  `words.txt` check (never auto-created; clear copy-or-set instructions),
  frontend `node_modules` and the `.next` build — each guarded by a sha256
  marker, so installs/builds happen once and later runs skip them.
- **Shared-drive master copy:** the operational home is the NCAD shared drive;
  both launchers refuse to run from a network/shared path (`\\` on Windows;
  `/Volumes/`, `/mnt/`, `/media/` on macOS/Linux) and tell you to copy the
  folder first. README has the "copy before you run" callout; the public demo
  (GitHub + Vercel/Render) has been **retired**.
- **Cross-platform:** `.gitattributes` forces LF for `.sh` and CRLF for `.bat`;
  the `start.sh` executable bit is tracked; the header documents `bash start.sh`
  vs `chmod +x` for the "Permission denied" case on macOS.
- **Frontend `.env` removed:** the API URL is now a static constant in
  `next.config.ts` (`http://127.0.0.1:8000`); the launcher no longer creates a
  `.env`, and `frontend/.env.example` was deleted — both servers always run on
  the same machine.
- **Launcher messaging:** `start.bat`/`start.sh` now wait up to ~4 minutes for
  the frontend (first start is slow) and print an honest end banner — "This
  window stays open while the servers run. To stop them, close this window (X)
  or press Ctrl+C."
- **words.txt instructions rewritten** (launcher + ONBOARDING.md): explains what
  the file is and that `PASSCODE_WORD_FILE` is an environment variable the
  backend reads at startup — set it before running, point it at the absolute
  path, and the difference between "this session" and "permanent".

## 2026-08-18

### LDAP Date of Birth fix (auto-added blank column)
- **LDAP defaults back to `warn`** (all systems warn by default again). The
  Quercus Discoverer report never exports `Date of Birth` anymore, so blocking
  rejected the weekly LDAP export every time.
- Added `NON_BLOCKING_REQUIRED_COLUMNS` to `app/core/quercus_schema.py`:
  `Date of Birth` (LDAP) is required **and never blocks**, in any mode — a
  missing DOB column is always auto-added as an empty column and the export
  proceeds. Rationale documented in-code (LDAP admin email, John O Donnell,
  2026-08-13: column stays in place, empty values allowed). New
  `blocking_missing_required()` helper; all 5 export endpoints now reject only
  on the blocking subset of missing columns.
- `X-Missing-Required` header still lists every auto-added column, so the
  amber banner says exactly what the system blanked.
- UI copy updated everywhere: banner says "the system auto-added the missing
  required columns with empty values"; Settings page notes DOB never blocks
  for LDAP; Quercus warning card explains the Discoverer/DOB situation.
- `backend/samples/test_settings.py` now 26 assertions (non-blocking registry
  covered); E2E verified: warn + missing DOB → download; strict + DOB-only
  missing → still downloads; strict + missing `First Name` → 422.

## 2026-08-14

### Per-System Validation Modes (Warn vs Block)
- Added `backend/app/core/settings.py` — per-system validation mode registry: `warn` / `strict`
- `warn` mode: exports **proceed** when required Quercus columns are missing — the missing columns are added as blank and the response carries an `X-Missing-Required` header; the export step shows an amber warning banner
- `strict` mode: the original behavior — missing required columns reject the export with a structured 422
- **Defaults are per-system: `ldap` → `strict` (Block), all other systems → `warn`.** LDAP blocks by default per the LDAP admin: a *missing* column must never go out blank — while a DOB column **present with empty cells** is fine and never blocks
- Mode resolution order: env var `VALIDATION_MODE_<SYSTEM>` → `backend/app/core/settings.json` → per-system default; settings file path overridable via `NCAD_SETTINGS_FILE`
- Added `GET/PUT /admin/settings` API (registered under `/admin`) and a new `/settings` page with a Warn/Block toggle per system (LDAP, Canvas, Google, OpenAthens, Library) + a "source" badge (default / saved / env override)
- All 5 export endpoints use the mode gate; added `backfill_missing_columns()` to `df_utils.py`; services unchanged
- **Date of Birth**: the new Quercus Discoverer report no longer includes DOB (GDPR). The LDAP output keeps the `Date of Birth` column when warn is enabled (blank values); with LDAP's default Block mode a missing column rejects the export. The Settings page can toggle LDAP to Warn if blank DOB is accepted
- `settings.json` is gitignored (per-deployment state; resets on redeploy unless an env var is set)
- Added `backend/samples/test_settings.py` — 22 assertions for per-system defaults, persistence, env precedence, validation, and corrupt-file degradation

## 2026-08-05

### Home Page & Privacy
- "Privacy at a glance" card now shows on **every page load** — dismissing it hides it for the current session only; nothing is persisted in localStorage anymore
- Removed the "Show privacy notice again" button on `/about` (no longer needed)
- Home page redesigned: featured **Provisioning Pipeline** card + two-card grid for **Library Export** and **Staff Provisioning** (new)

### Canvas Staff Tool
- Added `POST /staff/canvas/generate` (preview JSON) and `POST /staff/canvas/export` (CSV download) endpoints
- New `/staff` page with tool tabs: type staff names one per line, preview the Canvas rows, download `YYYYMMDD_canvas_staff.csv`
- Login rule: surname(s) + first initial, letters only, lowercased (e.g. `Cian Delaney Byrne` → `delaneybyrnec@staff.ncad.ie`)
- Single-word names (no last name) are generated with a warning and blank last name (login = name lowercased) instead of being rejected
- Output uses the same 11-column Canvas schema as the student pipeline; nothing is stored server-side
- Added Canvas staff assertions to `backend/samples/test_pipelines.py`

### Library Staff Tool
- Added `POST /staff/library/generate` (preview JSON), `POST /staff/library/export` (review CSV) and `POST /staff/library/export-text` (tab-delimited `.txt` for SFTP) endpoints
- New **Library** tab on the `/staff` page: row editor with name, library card number (barcode), optional gender, and per-person registration + expiration date inputs
- Output reuses the 46-column library schema from the student pipeline: `borrowerCategory = FTS`, `idAtSource` = login, `emailAddress` = `login@staff.ncad.ie`, `gender` = typed value or `UNKNOWN` when blank, dates always written `YYYY-MM-DD`
- Registration and expiration dates are set **per staff member** in the row editor (registration date missing → warning + blank column, never blocks)
- Downloads: `YYYYMMDD_library.csv` (for review — spreadsheet apps may re-format dates) and `YYYYMMDDlibrary.txt` (tab-delimited, dates untouched, ready for SFTP)
- Missing barcode, missing last name or missing registration date → row generated with a warning, so it can be completed before the SFTP upload
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
