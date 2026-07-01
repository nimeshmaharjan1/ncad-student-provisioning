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
| SFTP client | e.g. FileZilla, WinSCP, or command-line sftp |
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
7. Upload the file via https://filesender2.heanet.ie and notify **Rene**
8. Verify no duplicate accounts exist

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

4. Open your SFTP client and connect using the Library SFTP credentials (provided by John)
5. Upload `YYYYMMDD_library.csv`
6. The Library system handles merging automatically

---

### Phase 4: Send Student Emails (Thunderbird Mail Merge)

The system does **not** send emails. You use **Thunderbird with the Mail Merge add-on** for 3 separate email campaigns.

All instructions assume Thunderbird is set up with the NCAD email account (provided by John).

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
| "Failed to install dependencies" | Python or Node.js not installed | Run `start.bat` / `start.sh` — it checks dependencies automatically |
| Port 3000 / 8000 already in use | Previous instance still running | The launcher now auto-kills orphaned processes — just re-run it |
| Wrong number of students in export | Baseline file might be outdated | Merge recent export files into your baseline first |
| Dates show as `#VALUE!` or wrong format | Input date format not recognised | The system handles most formats. If one slips through, check the raw CSV |

---

## Still Need Help?

- Developer docs: [`ONBOARDING.md`](ONBOARDING.md)
- Legacy manual process (for reference): [`MANUAL_PROCESS.md`](MANUAL_PROCESS.md)
- System architecture: [`architecture.md`](architecture.md)
