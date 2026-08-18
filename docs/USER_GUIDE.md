# User Guide: NCAD Student Provisioning System

## Overview

This system automates the **file processing and export** part of student provisioning.
It handles everything between downloading CSVs from Quercus and producing ready-to-upload
files for each downstream system.

**What the system does for you:**
- Merges and cleans Quercus student data (dedup, filter by status, assign course types)
- Compares against baselines to detect only new students
- Generates passcodes (LDAP), UUID passwords (Google)
- Formats dates and data correctly per system
- Produces export CSVs ready to upload

**What you still do manually:**
- Download CSVs from Quercus website
- Upload export files to each system (SFTP, Admin consoles)
- Send emails via Thunderbird Mail Merge

---

## Prerequisites

Before using this system, make sure you have:

| Item | Where to get it |
|---|---|
| Quercus login | https://eu-quercus.elluciancloud.com/ |
| Google Workspace Admin access | admin.google.com (student domain) |
| Canvas Admin access | Provided by IT |
| OpenAthens Admin access | https://admin.openathens.net |
| SFTP client | e.g. Cyberduck |
| Thunderbird | With **Mail Merge** add-on installed |
| Baseline CSV files | From the previous month's run (stored in system folders) |
| Latest Quercus CSVs | Export from Quercus (see Phase 1) |

---

## Step-by-Step Workflow

### Phase 1: Export from Quercus (Manual)

Do this before opening the provisioning system.

1. Open https://eu-quercus.elluciancloud.com/app/ncad/f?p=1001:LOGIN::::
2. Click the **2nd Reporting** card → **AD HOC** → **Configure Reports**
3. Search for `all students 2025`
4. Select the **first** report (ignore the second)
5. Filter by year `2025`, click **Download** → **CSV**
6. Save as `2025_all_students.csv`
7. Repeat for `2026` → save as `2026_all_students.csv`

> Both files will be uploaded into the system together. It handles merging.

> **Date of Birth (GDPR):** the new Quercus Discoverer report no longer
> includes `Date of Birth`. This is expected — the upload shows a missing-column
> warning and LDAP exports include the `Date of Birth` column **blank** (the
> LDAP admin confirmed the column must remain, but empty is fine).

---

### Phase 2: Process Quercus Data (Automated)

Open the provisioning system:
- **Local:** http://localhost:3000
- **Demo:** https://ncad-student-provisioning.vercel.app/

Click **Provisioning Pipeline** on the home page.

#### Step 2a: Upload and Clean

1. On the **Quercus — Source of Truth** card, drag your CSV files
   (`2025_all_students.csv` + `2026_all_students.csv`) into the upload area
   — or click to select them
2. Click **Process Quercus Files**
3. Wait for the progress bar to complete

#### Step 2b: Review Results

After processing, you'll see:
- **Audit summary** showing student counts at each stage
- **Preview table** of the first 10 cleaned rows
- A cleaned CSV file downloads automatically

Keep this download — it's your processed Quercus data.

---

### Phase 3: Process Each System

After Phase 2 completes, 4 pipeline cards appear below the Quercus card.
Each system's workflow is self-contained — the automated export followed by
the manual steps needed to complete it.

---

#### LDAP

**In the system:**

1. Upload the most recent LDAP baseline CSV (e.g. `pre_20260612_ldap.csv` from your `LDAP_2025/` folder)
2. Click **Run LDAP Export**
3. Download the `.zip`

**The `.zip` contains:**
- `YYYYMMDD_ldap_new_students.csv` — includes **passcodes**
- `YYYYMMDD_ldap_updated_baseline.csv` — save as your next baseline

> **Date of Birth:** since the GDPR change, the Quercus Discoverer report no
> longer exports `Date of Birth`. This is expected: the system **auto-adds
> the column with empty values** in the LDAP export (per the LDAP admin —
> "leave the DOB column in place but we can leave it empty of data"), and an
> amber banner tells you exactly that. Date of Birth never blocks an export,
> even in Block mode; a column present with empty cells never blocks either.
> See **Validation Settings** below.

**Once the file is downloaded:**

4. Open your SFTP client and connect to the Triangle LDAP server
5. Upload `YYYYMMDD_ldap_new_students.csv`
6. Email **Triangle Service Desk** to confirm the upload
7. **Wait** for confirmation that LDAP accounts have been created
8. Do not proceed to send any student communications until confirmed

---

#### Canvas

**In the system:**

1. Upload the most recent Canvas baseline CSV (e.g. `canvas_all_pre_20260616.csv` from your `Canvas_2025/` folder)
2. Click **Run Canvas Export**
3. Download the `.zip`

**The `.zip` contains:**
- `YYYYMMDD_canvas.csv` — ready for Canvas SIS Import
- `YYYYMMDD_canvas_all_pre.csv` — save as your next baseline

**Once the file is downloaded:**

4. Log into **Canvas** administration
5. Navigate to **SIS Import** and upload `YYYYMMDD_canvas.csv`
6. Confirm the import completes without errors
7. Upload the file via https://filesender2.heanet.ie and notify **the Canvas administrator**
8. Verify no duplicate accounts exist

---

#### Canvas Staff

A separate tool for **staff** accounts — not part of the student pipeline.
Go to **Staff** in the top navigation and open the **Canvas** tab.

**In the system:**

1. Type staff names into the text box, one per line (e.g. `Cian Delaney Byrne`)
2. Click **Generate rows** — each name becomes a Canvas-ready row
3. Review the preview table
4. Click **Download CSV** — get `YYYYMMDD_canvas_staff.csv`, ready for Canvas SIS Import

**How a name becomes a row:**

| Typed name | First name | Last name | Login / email | Sortable name |
| --- | --- | --- | --- | --- |
| `Cian Delaney Byrne` | Cian | Delaney Byrne | `delaneybyrnec@staff.ncad.ie` | Delaney Byrne, Cian |
| `Roisin Quigley` | Roisin | Quigley | `quigleyr@staff.ncad.ie` | Quigley, Roisin |

- Login = surname(s) + first initial, letters only, lowercased
- A single-word name has no last name — the row is still generated with a
  warning and a blank last name (login = the name itself, e.g. `Cian` →
  `cian@staff.ncad.ie`). Enter the full name where possible, because Canvas
  imports expect first and last names.
- `user_id`, `integration_id`, `password`, `short_name` and `status` follow the same Canvas schema as the student export
- Nothing is stored — rows are generated from what you type and are gone when you leave the page

---

#### Library Staff

A tool for **staff library accounts** — not part of the student pipeline.
Go to **Staff** in the top navigation and open the **Library** tab.

**In the system:**

1. Fill in one row per staff member: name, library card number, optional
   gender (blank = `UNKNOWN`), that person's **registration date** and an
   optional **expiration date**
2. Leave the registration date blank if unknown — the row is still generated
   with a warning so it can be completed before upload
3. Click **Generate rows** — each row becomes a library patron row
4. Review the preview table
5. Click **Download TXT (SFTP)** — get `YYYYMMDDlibrary.txt`, tab-delimited and
   ready to upload via SFTP. Click **Download CSV (review)** if you want to
   check the data in a spreadsheet first

**How a row is built (46-column library schema, same as the student export):**

| Typed name | Given name | Family name | Barcode | Registration date | Expiration date | idAtSource / email | Category |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Cian Delaney Byrne` | Cian | Delaney Byrne | `12345678` | `2026-07-14` | | `delaneybyrnec@staff.ncad.ie` | FTS |
| `Roisin Quigley` | Roisin | Quigley | `12345678` | `2026-09-01` | `2027-01-30` | `quigleyr@staff.ncad.ie` | FTS |

- Fixed values: `institutionId = 46722`, `sourceSystem = https://idp.ncad.ie/idp/shibboleth`,
  `borrowerCategory = FTS`, `homeBranch = 266006`, `gender = UNKNOWN` when left blank
- `circRegistrationDate` and `oclcExpirationDate` are taken from each row's
  date pickers and always written as `YYYY-MM-DD`
- The **CSV is for review only** — Excel / Google Sheets may re-format dates
  to their platform defaults. The **TXT keeps `YYYY-MM-DD` untouched** and is
  the file to upload via SFTP
- Missing card number, missing last name or missing registration date → the
  row is still generated, with a warning telling you to complete it before the
  SFTP upload
- Nothing is stored — rows are generated from what you type and are gone when you leave the page

---

#### Google Workspace

**In the system:**

1. Upload the most recent Google Workspace baseline CSV (the bulk export from Google Admin)
2. Click **Run Google Export**
3. Download the `.zip`

**The `.zip` contains:**
- `YYYYMMDD_google_upload.csv` — new accounts with UUID passwords (force-change enabled)
- `YYYYMMDD_google_reactivate.csv` — suspended students who reappeared in Quercus

**Once the file is downloaded:**

4. Log into **Google Workspace Admin Console** (student domain)
5. Go to **Users** → **Bulk upload users**
6. Upload `YYYYMMDD_google_upload.csv`
7. New accounts are created with temporary passwords

8. **Review reactivations:** Open `YYYYMMDD_google_reactivate.csv` — for each student:
   - Check their status in Quercus
   - Reactivate the account in Google Admin if needed
   - Add them to the correct mailing group:
     - CEAD → "NCAD CEAD 2025"
     - UG → "NCAD Undergraduate 2025"
     - PG → "NCAD Postgraduate 2025"
   - Send a password reset to their personal email

---

#### OpenAthens

**In the system:**

1. Upload the most recent OpenAthens baseline CSV (the account export from `admin.openathens.net`)
2. Click **Run OpenAthens Export**
3. Download the `.zip`

**The `.zip` contains:**
- `YYYYMMDD_athens.csv` — ready for Bulk Upload (21-column template, status = pending)
- `YYYYMMDD_athens_new_users.csv` — debug list for verification

**Once the file is downloaded:**

4. Log into https://admin.openathens.net
5. Go to **Accounts** → **Bulk Upload**
6. Upload `YYYYMMDD_athens.csv`
7. Confirm the upload completes and new accounts appear

---

#### Library

The Library page is standalone (no pipeline dependency). Access it from the home page or `/library`.

**In the system:**

1. Upload the raw Quercus Library export CSVs (2025 + 2026)
2. Click **Run Library Export**
3. Download the `.zip`

**The `.zip` contains:**
- `YYYYMMDD_library.csv` — ready for SFTP upload (46-column template)
- `YYYYMMDD_library_cleaned.csv` — intermediate file for verification

**Once the file is downloaded:**

4. Open your SFTP client and connect using the Library SFTP credentials (provided by IT support)
5. Upload `YYYYMMDD_library.csv`
6. The Library system handles merging automatically

---

### Phase 4: Send Student Emails (Thunderbird Mail Merge)

The system does **not** send emails. You use **Thunderbird with the Mail Merge add-on** for 3 separate email campaigns.

All instructions assume Thunderbird is set up with the NCAD email account (provided by IT support).

#### Email 1: LDAP Credentials

Send this **after** Triangle confirms LDAP accounts have been created.

| Setting | Value |
|---|---|
| Email template | LDAP email template |
| Recipient source | `YYYYMMDD_ldap_new_students.csv` |
| Mail Merge tool | Thunderbird **Tools → Mail Merge** |

This sends each student their LDAP username and passcode.

#### Email 2: Eduroam Wi-Fi Information

| Setting | Value |
|---|---|
| Email template | Eduroam email template |
| Recipient source | `YYYYMMDD_ldap_new_students.csv` (same file) |
| Mail Merge tool | Thunderbird **Tools → Mail Merge** |

This sends each student their Eduroam Wi-Fi login details.

#### Email 3: Student Email Account Details

| Setting | Value |
|---|---|
| Email template | Student email template |
| Recipient source | `to_mail` file (located in `Email_2025/` folder) |
| Mail Merge tool | Thunderbird **Tools → Mail Merge** |

This sends each student their email account login details to their **personal email address**.

> The `to_mail` file is maintained separately and contains personal email addresses,
> not NCAD student email addresses.

---

### Validation Settings

Each system (LDAP, Canvas, Google Workspace, OpenAthens, Library) has a
**validation mode** controlling what happens when a Quercus file is missing
required columns. Configure them on the **Settings** page (top navigation):

| Mode | Behavior |
|---|---|
| **Warn** | The export runs. Missing required columns are **auto-added with empty values**, and an amber banner on the export step lists exactly which columns were blanked. |
| **Block** (strict) | The export is rejected with a red error card listing the missing columns — nothing is downloaded. |

**All systems default to Warn.** Exception baked into the schema: **`Date of
Birth` never blocks for LDAP** — in any mode it is auto-added as an empty
column and the export proceeds (per the LDAP admin's agreement, since the
Discoverer report no longer exports DOB).

- Changes apply **immediately** — no redeploy or re-upload needed.
- Each system's toggle shows a badge: **Default** (not changed yet),
  **Saved** (set via this page), or **Environment override** (a
  `VALIDATION_MODE_<SYSTEM>` environment variable is set on the server —
  it always wins over the saved setting).
- When to use **Block**: when a missing column would silently corrupt the
  downstream file (e.g. a missing `ID Number` for Library, or `First Name`
  for LDAP). DOB is the one exception — it always exports as an empty column
  rather than blocking.

---

## File Naming Convention

All files generated by the system use the format:

```
YYYYMMDD_system_description.csv
```

| Example | What it is |
|---|---|
| `20260701_quercus.csv` | Cleaned Quercus data |
| `20260701_ldap_new_students.csv` | New LDAP accounts with passcodes |
| `20260701_ldap_updated_baseline.csv` | Updated LDAP baseline (save for next run) |
| `20260701_canvas.csv` | Canvas SIS import file |
| `20260701_canvas_all_pre.csv` | Updated Canvas baseline |
| `20260701_google_upload.csv` | Google Workspace bulk upload |
| `20260701_google_reactivate.csv` | Google accounts to review for reactivation |
| `20260701_athens.csv` | OpenAthens bulk upload |
| `20260701_library.csv` | Library upload file |

---

## Folder Structure (Reference)

This is the folder layout used during the manual process. Keep your baseline
files organised the same way:

```
Parent folder/
├── Quercus_2025/
├── LDAP_2025/
├── Canvas_2025/
│   └── Students_canvas/
├── Email_2025/
├── Google_2025/
├── Athens_2025/
├── Library_2025/
└── scripts/
```

---

## Troubleshooting

| Problem | Likely cause | What to do |
|---|---|---|
| "Failed to process Quercus files" | CSV has missing required columns (ID Number, Status, etc.) | Check that your Quercus export includes all columns |
| Export downloads but shows an amber "generated with warnings" banner | Missing required columns exported as blank (warn mode) | Recheck the Quercus export columns, or switch that system to **Block** in Settings to force rejection instead |
| LDAP file has blank `Date of Birth` values | Quercus Discoverer report no longer exports DOB (GDPR) | Expected — the LDAP admin confirmed blank is fine; the column must stay in the file |
| "Failed to install dependencies" | Python or Node.js not installed | Run `start.bat` / `start.sh` — it checks dependencies automatically |
| Port 3000 / 8000 already in use | Previous instance still running | The launcher now auto-kills orphaned processes — just re-run it |
| Wrong number of students in export | Baseline file might be outdated | Merge recent export files into your baseline first |
| Dates show as `#VALUE!` or wrong format | Input date format not recognised | The system handles most formats. If one slips through, check the raw CSV |

---

## Still Need Help?

- Developer docs: [`ONBOARDING.md`](ONBOARDING.md)
- Legacy manual process (for reference): [`MANUAL_PROCESS.md`](MANUAL_PROCESS.md)
- System architecture: [`architecture.md`](architecture.md)
