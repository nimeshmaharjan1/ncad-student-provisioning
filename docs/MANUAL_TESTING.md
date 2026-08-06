# Manual Testing Guide

How to manually test every feature of the NCAD Student Provisioning app,
including what to change in your input files to trigger each scenario.

All sample files referenced below live in the repo's `samples/` folder:

- Quercus uploads: `quercus_2025.csv`, `quercus_2026.csv`
- Baselines (NEVER modify these — they have fixed system schemas):
  `baseline_ldap.csv`, `baseline_canvas.csv`, `baseline_google.csv`, `baseline_athens.csv`

## Setup

1. Backend: `cd backend` → activate venv → `uvicorn app.main:app --reload --port 8000`
2. Frontend: `cd frontend` → `npm run dev` → http://localhost:3000
3. Make sure `frontend/.env` points at the LOCAL backend
   (`NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`), not the demo URL.

## Test 1 — Happy path (regression check)

| Step | Action | Expect |
|------|--------|--------|
| Quercus | Upload `quercus_2025.csv` + `quercus_2026.csv` | Green success toast, cleaned CSV downloads, stepper "Quercus" turns done, **no warning card** |
| LDAP | Upload `baseline_ldap.csv` + the **cleaned file from the Quercus step** | ZIP with `new_students.csv` + `updated_baseline.csv`, success card |
| Canvas / Google / Athens | Same pattern with their baseline files | ZIP downloads, all steps done |
| Library | Upload the two Quercus files directly | ZIP with cleaned + 46-column template |
| Anywhere | Open Export History | Entries with timestamps / row counts |

Key detail: at the LDAP / Canvas / Google / Athens steps you upload the
**cleaned** Quercus file (it gains `Term Email` + `Type`). At the Library step
you upload the raw files. Baselines are immutable — never edit them.

## Test 2 — Quercus missing-column warning (warns, never blocks)

1. Use the provided `quercus_2025_without_dob.csv` (a copy of
   `quercus_2025.csv` with the **`Date of Birth`** column deleted) — or make
   your own by copying `quercus_2025.csv` and deleting that column.
2. Upload it **together with** the unmodified `quercus_2026.csv`.
3. Expect:
   - Processing succeeds — the step is still "done" and the audit summary /
     preview render, but **no automatic download** happens.
   - Amber warning card **"Processed with warnings — missing columns"**
     with a row: `quercus_2025_without_dob.csv → Date of Birth` (the 2026
     file is absent from the list — it has all columns).
   - A **"Download cleaned file anyway"** button below the card; clicking it
     downloads the cleaned CSV (this is the only way to download when
     warnings exist). Before clicking, a note says "Processing finished —
     download the cleaned file when you're ready".
   - Amber warning toast and the "Recheck before continuing" tip.
4. In the same warning view, an **"Upload corrected files"** area is
   available — no need to click "Start over". Upload the unmodified
   `quercus_2025.csv` + `quercus_2026.csv` and click **"Process Corrected
   Files"** → the warning disappears and the cleaned CSV auto-downloads
   (happy path).
5. Click "Start over" → the upload area is fully empty (no preview, no
   audit summary, no file names in the dropzone, no warnings) — a full
   remount clears all previous state.

More warning scenarios (each = copy the file, delete one column, upload alone):

| Delete column | Expect |
|---------------|--------|
| `Date of Birth` | Warning (LDAP export would reject it) |
| `Status` | Warning (preprocessing's status filter would be silently skipped) |
| `LDAP ID` | Warning (LDAP export would reject it) |
| `Home Mobile Phone` | **No warning** — it is optional now |
| `Gender`, `Course Instance Start Date`, `Course Instance End Date` | **No warning** (optional for Library) |

The full expected-column list is computed from the schema registry:
`backend/app/core/quercus_schema.py` (`SOURCE_WARN_COLUMNS`). Adding/removing
a system there changes what upload warns about automatically.

## Test 3 — Strict 422 at export steps (unchanged behavior)

Use the **cleaned file from Test 1**, then:

| Test | Remove column from cleaned file | Expect |
|------|-------------------------------|--------|
| LDAP step | `Date of Birth` | Red "Export Failed" card, Missing Required badge, present columns, tip. **No ZIP.** |
| Canvas step | `First Name` | Same red card |
| Google step | `Last Name` | Same red card |
| Athens step | `Last Name` | Same red card |
| Library step | `ID Number` | Same red card |

This is the STRICT mode — missing required columns block the export with a
structured 422. Missing OPTIONAL columns (e.g. `Home Mobile Phone` at the LDAP
step) never block; they are left blank.

## Test 4 — Privacy notice (informational only)

- Home page: blue "Privacy at a glance" card is visible.
- Click the × — the card hides for the current session only (display
  preference, no consent tracked, nothing persisted).
- Reload the page → the card is visible again (it always shows on every load).
- "Learn more" → `/about#privacy`.

## Test 5 — Full pipeline regression (strongest proof)

With the venv activated:

```bash
cd backend
python samples/test_pipelines.py
```

Asserts exact row counts for the whole pipeline (5 cleaned Quercus rows,
3 new LDAP / Canvas / Athens students, 3 Google uploads + 1 reactivation,
rerun produces 0 new). Must end with `ALL PIPELINE SMOKE TESTS PASSED`.

## Test 6 — Error handling fallbacks

- Stop the backend, try an export → frontend shows a friendly error
  ("Export failed: ..." / "unexpected error"), no crash.
- Restart backend: everything works again; nothing was persisted server-side.

## Test 7 — Canvas staff tool

- Open **Staff** (top navigation) → **Canvas** tab.
- Type `Cian Delaney Byrne` on one line → **Generate rows**.
  - Preview row must show: first `Cian`, last `Delaney Byrne`,
    login/email `delaneybyrnec@staff.ncad.ie`, sortable `Delaney Byrne, Cian`,
    status `active`.
- Add a second line `Roisin Quigley` → generate again → 2 rows, second email
  `quigleyr@staff.ncad.ie`.
- Click **Download CSV** → downloads `YYYYMMDD_canvas_staff.csv` with the
  11-column header (`user_id, integration_id, login_id, ...`) and one row per
  name. Open it in Excel/Notepad to confirm.
- Empty textarea + generate → error toast "No names entered", no request.
- Single word `Cian` + generate → a row is generated with a warning: login
  `cian@staff.ncad.ie`, blank last name; the amber warning card + warning toast
  appear above the preview.
- Names with apostrophes/hyphens are accepted (`Liam O'Shea` →
  `osheal@staff.ncad.ie`).

## Test 8 — Library staff tool

- Open **Staff** (top navigation) → **Library** tab.
- Add a row: name `Cian Delaney Byrne`, card number `12345678`, gender `Male`,
  registration date `2026-07-14`, expiration date `2028-07-13` → **Generate rows**.
  - Preview must show: given `Cian`, family `Delaney Byrne`, gender `Male`,
    institutionId `46722`, barcode `12345678`, idAtSource `delaneybyrnec`,
    sourceSystem `https://idp.ncad.ie/idp/shibboleth`, borrowerCategory `FTS`,
    `circRegistrationDate` = `2026-07-14`, `oclcExpirationDate` = `2028-07-13`,
    homeBranch `266006`, email `delaneybyrnec@staff.ncad.ie`, username blank.
- Add a second row `Roisin Quigley`, card number `12345678`, no gender,
  registration date `2026-09-01`, no expiration date → generate →
  gender shows `UNKNOWN`; `circRegistrationDate = 2026-09-01`,
  `oclcExpirationDate` blank, email `quigleyr@staff.ncad.ie`.
- Missing values warn without blocking: a row with no card number, and a
  single-word name `Liam` with no registration date → both rows are still
  generated, `circRegistrationDate` blank for Liam, email `liam@staff.ncad.ie`; the
  amber warning card + warning toast list what's missing.
- Click **Download CSV (review)** → downloads `YYYYMMDD_library.csv` with the
  46-column header and one row per staff member.
- Click **Download TXT (SFTP)** → downloads `YYYYMMDDlibrary.txt`, tab-delimited
  (open in Notepad to confirm tabs and `YYYY-MM-DD` dates are intact).
- Row without a name + generate → error toast "No staff members entered".
- Remove-row button is disabled when only one row remains; **Add row** appends a blank row.

## Gotchas

- Test on **localhost:3000**, not the public onrender URL — the deployed app
  runs older code until main is pushed and auto-deploy runs, so new features
  (like the missing-column warning) will not appear there.
- The Quercus upload warning (`Test 2`) is the WARN mode; export validation
  (`Test 3`) is the STRICT mode. Both read from the same registry — the
  warning tells you in advance exactly which exports will fail if you
  continue without fixing the file.
- `npx next build` in `frontend/` and the compile check in `backend/` must
  stay green after any code change.
