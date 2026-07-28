# Changelog

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
