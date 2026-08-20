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
   (the frontend always targets the local backend at `http://127.0.0.1:8000`
   by default — no `.env` needed.)

## Test 1 — Happy path (regression check)

| Step | Action | Expect |
|------|--------|--------|
| Quercus | Upload `quercus_2025.csv` + `quercus_2026.csv` | Green success toast, cleaned CSV downloads, stepper "Quercus" turns done, **no warning card** |
| LDAP | Upload `baseline_ldap.csv` + the **cleaned file from the Quercus step** | ZIP with `YYYYMMDD_ldap.csv` + `pre_YYYYMMDD_ldap.csv`, success card |
| Canvas / Google / Athens | Same pattern with their baseline files | ZIP downloads, all steps done |
| Library | Upload the two Quercus files directly | ZIP with cleaned CSV + tab-delimited 46-column `.txt` template |
| Anywhere | Open Export History | Entries with timestamps / row counts |

Key detail: at the LDAP / Canvas / Google / Athens steps you upload the
**cleaned** Quercus file (it gains `Term Email` + `Type`). At the Library step
you upload the raw files. Baselines are immutable — never edit them.

## Test 2 — Quercus missing-column warning (warns, never blocks)

1. Make a copy of `quercus_2025.csv` and delete a genuinely required column
   (e.g. **`First Name`**) so the warning actually triggers — deleting
   `Date of Birth` no longer does (see the table below).
2. Upload it **together with** the unmodified `quercus_2026.csv`.
3. Expect:
   - Processing succeeds — the step is still "done" and the audit summary /
     preview render, but **no automatic download** happens.
   - Amber warning card **"Processed with warnings — missing columns"**
     with a row for the modified file listing the deleted column (the 2026
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
| `Date of Birth` | **No warning** — expected to be absent (GDPR); LDAP auto-adds it blank and never blocks (see Test 3) |
| `First Name` | Warning (required everywhere) |
| `Status` | Warning (preprocessing's status filter would be silently skipped) |
| `LDAP ID` | Warning (LDAP export proceeds with blank LDAP ID under warn mode) |
| `Home Mobile Phone` | **No warning** — it is optional now |
| `Gender`, `Course Instance Start Date`, `Course Instance End Date` | **No warning** (optional for Library) |

The full expected-column list is computed from the schema registry:
`backend/app/core/quercus_schema.py` (`SOURCE_WARN_COLUMNS`). Adding/removing
a system there changes what upload warns about automatically.

## Test 3 — Missing required columns at export steps (warn default; Date of Birth never blocks)

Validation behavior is per-system, controlled from the `/settings` page:
**Warn** = export proceeds, missing columns are **auto-added with empty
values**, amber banner shown. **Block** (strict) = export rejected with
structured 422. **Every system defaults to Warn.** Exception baked into the
schema registry: `Date of Birth` for LDAP is non-blocking in **any** mode —
the Quercus Discoverer report no longer exports DOB (GDPR) and the LDAP
admin requires the column to stay with empty values allowed.

### Test 3a — Warn mode (default behavior)

1. Complete Test 1 to get the cleaned Quercus file, then make a copy and
   delete the `Date of Birth` column (or use `samples/quercus_2025_without_dob.csv`
   at the Quercus step — the cleanest path, since the warning card appears there).
2. At the **LDAP step**, upload `baseline_ldap.csv` + a cleaned file missing
   `Date of Birth` (or just use the without-dob variant through the Quercus
   step first).
3. Expect:
   - The ZIP **downloads** (no red card).
   - **Amber banner** "LDAP export generated with warnings — the system
     auto-added the missing required columns with empty values: `Date of
     Birth` (and `Type`, `Term Email` if the without-dob raw file was used)."
   - Unzip (or open the CSV): both files **still contain the `Date of Birth`
     column header**, with blank values.

### Test 3b — Strict mode (toggle it on)

1. Go to **Settings** and switch **LDAP → Block**, then Save.
2. Repeat the LDAP export from Test 3a (file missing only `Date of Birth`) →
   the ZIP **still downloads** with the amber banner: DOB is non-blocking even
   in strict mode (see `NON_BLOCKING_REQUIRED_COLUMNS`).
3. Now upload a cleaned file missing `First Name` instead → expect the red
   "Export Failed" card with Missing Required badge, present columns list,
   and **no ZIP**. The 422 body lists `First Name` (not DOB).
4. Switch LDAP back to **Warn** and re-run → downloads again.

### Test 3c — Strict mode per system

With each system set to **Block**, remove the column below from the cleaned
file:

| Test | Remove column from cleaned file | Expect |
|------|-------------------------------|--------|
| LDAP step | `First Name` | Red "Export Failed" card, no download |
| LDAP step | `Date of Birth` | **Downloads** (DOB never blocks) |
| Canvas step | `First Name` | Red "Export Failed" card, no download |
| Google step | `Last Name` | Same red card |
| Athens step | `Last Name` | Same red card |
| Library step | `ID Number` | Same red card |

Missing OPTIONAL columns (e.g. `Home Mobile Phone` at the LDAP step) never
block in either mode; they are left blank.

### Test 3d — Settings page

- Open `/settings` — one toggle row per system (LDAP, Canvas, Google,
  OpenAthens, Library); all five show **Warn** with a "Default" badge. The
  LDAP row notes that Date of Birth is always auto-added with empty values
  and never blocks.
- Toggle one system → "Save changes" enables → toast "Settings saved".
- Badge becomes **Saved**. Reload the page → the choice persists.
- Delete `backend/app/core/settings.json` (or set a fresh
  `NCAD_SETTINGS_FILE`) so no file overrides apply → all rows show **Warn /
  Default** again.
- Reopen the Settings page after the backend restarts but with
  `VALIDATION_MODE_LDAP=strict` set in the environment → the LDAP row shows
  **Block** with an "Environment override" badge, and the toggle is still
  editable (saved values have no effect while the env var exists).

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

Also run the settings registry tests (defaults, persistence, env precedence):

```bash
python samples/test_settings.py
```

Must end with `0 failed, 26 passed` (per-system defaults, persistence, env
precedence, and the non-blocking-column registry).

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

- Test on **localhost:3000** — the app runs locally; there is no deployed
  environment anymore.
- The Quercus upload warning (`Test 2`) and the export warn mode (`Test 3a`)
  are WARN behavior; the export rejection (`Test 3b/3c`) is strict behavior.
  All read from the same registry — the upload warning tells you in advance
  which columns a downstream export will blank out (warn) or reject on (block).
- `npx next build` in `frontend/` and the compile check in `backend/` must
  stay green after any code change.
