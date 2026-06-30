# NCAD Student Provisioning — Developer Onboarding

## What This System Does

NCAD Student Provisioning automates the creation and update of student accounts across **5 institutional systems** from a single Quercus (student records) export. It replaces manual Excel-based workflows.

**Input:** One or more Quercus CSV exports.

**Outputs:** System-specific CSV files ready for import into:
- LDAP (account credentials)
- Canvas (SIS enrollment)
- Google Workspace (account provisioning + reactivation)
- OpenAthens (access management)
- Library (borrower records)

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 20+
- npm

### Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r ..\requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000`.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The UI is now at `http://localhost:3000`.

### Smoke Test

1. Open `http://localhost:3000`
2. Click **Provisioning Pipeline** → upload a Quercus CSV
3. Upload a baseline CSV to LDAP / Canvas / Google / Athens cards
4. Download the resulting ZIP files

---

## Repository Map

```
ncad-student-provisioning/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── routes.py        # Router → prefix registration
│   │   │   ├── quercus.py       # POST /quercus/upload, /quercus/download
│   │   │   ├── ldap.py          # POST /ldap/export, /ldap/download
│   │   │   ├── canvas.py        # POST /canvas/export
│   │   │   ├── google.py        # POST /google/export
│   │   │   ├── athens.py        # POST /athens/export
│   │   │   ├── library.py       # POST /library/export
│   │   │   └── export.py        # POST /export/all, /export/bundle (legacy)
│   │   ├── services/
│   │   │   ├── quercus_preprocess.py   # Source of truth: preprocess_quercus()
│   │   │   ├── quercus_transform.py    # Legacy variant (used by /export/*)
│   │   │   ├── ldap_export.py          # LDAP diff + passcode generation
│   │   │   ├── ldap_service.py         # Legacy LDAP mapper (used by /export/*)
│   │   │   ├── canvas_service.py       # Canvas diff pipeline + legacy mapper
│   │   │   ├── google_service.py       # Google diff + reactivation
│   │   │   ├── athens_service.py       # Athens diff + 21-col upload template
│   │   │   ├── library_service.py      # Library clean + 46-col template
│   │   │   └── export_pipeline.py      # Legacy: runs all legacy mappers at once
│   │   ├── utils/
│   │   │   ├── passcode_generator.py   # Word-based passcode generation
│   │   │   └── file_handler.py         # (currently empty — placeholder)
│   │   ├── core/
│   │   │   └── config.py              # (currently empty — placeholder)
│   │   └── models/
│   │       └── student.py             # (currently empty — placeholder)
│   └── README.md              # Backend quick reference
├── frontend/
│   ├── app/
│   │   ├── layout.tsx         # Root layout: nav + PipelineProvider
│   │   ├── page.tsx           # Home: 2-card navigation
│   │   ├── quercus/page.tsx   # Pipeline page (Quercus → LDAP/Canvas/Google/Athens)
│   │   └── library/page.tsx   # Standalone Library export page
│   ├── components/
│   │   ├── quercus-step.tsx   # Upload + process Quercus files
│   │   ├── ldap-step.tsx      # LDAP baseline upload + download
│   │   ├── canvas-step.tsx    # Canvas baseline upload + download
│   │   ├── google-step.tsx    # Google baseline upload + download
│   │   ├── athens-step.tsx    # OpenAthens baseline upload + download
│   │   ├── library-step.tsx   # Library file upload + download
│   │   ├── file-upload.tsx    # Reusable file upload dropzone
│   │   ├── data-table.tsx     # Preview table for sample rows
│   │   ├── audit-summary.tsx  # Row count summary card
│   │   └── ui/               # shadcn/ui primitives
│   ├── lib/
│   │   ├── api.ts             # fetch wrappers for all endpoints
│   │   ├── pipeline-context.tsx # React context: stores cleaned Quercus file
│   │   └── utils.ts           # cn() utility
│   └── README.md
├── docs/
│   ├── architecture.md        # Original design doc (slightly outdated)
│   └── ONBOARDING.md          # ← YOU ARE HERE
├── samples/                   # Empty — place sample CSVs here
├── scripts/                   # Shell test scripts
├── requirements.txt           # Python dependencies
└── README.md                  # Project overview
```

---

## API Endpoints (Entry Points)

Every endpoint is a `POST` (file uploads). All accept `multipart/form-data`.

### Quercus Pipeline

#### `POST /quercus/upload`
Upload one or more Quercus CSV files. Returns JSON with audit info and first 10 sample rows.

| Field | Type | Description |
|-------|------|-------------|
| `files` | `UploadFile[]` | Quercus CSV files (multiple) |

**Response (JSON):**
```json
{
  "uploaded_files": ["2025.csv", "2026.csv"],
  "raw_row_count": 1500,
  "cleaned_row_count": 1200,
  "filtered_out_status_count": 200,
  "external_students_removed_count": 50,
  "duplicate_rows_detected": 50,
  "sample_rows": [...]
}
```

#### `POST /quercus/download`
Same input as upload. Returns `YYYYMMDD_quercus.csv` — the cleaned, preprocessed CSV.

---

### LDAP Pipeline

#### `POST /ldap/export` (JSON preview)
| Field | Type | Description |
|-------|------|-------------|
| `baseline` | `UploadFile` | Current LDAP snapshot (`.csv` or `.xlsx`) |
| `quercus` | `UploadFile` | Cleaned Quercus CSV |

Returns JSON: `{ new_students: [...], updated_baseline: [...], audit_info: {...} }`

#### `POST /ldap/download` (file download)
Same inputs. Returns a ZIP containing:
- `YYYYMMDD_ldap_new_students.csv` — 13 cols (Student ID, Code, Description, Year, ... Passcode)
- `YYYYMMDD_ldap_updated_baseline.csv` — merged baseline + new students

Optional query params: `format=csv` (returns single CSV with section headers),
`new_students_filename`, `updated_baseline_filename`.

---

### Canvas Pipeline

#### `POST /canvas/export`
| Field | Type | Description |
|-------|------|-------------|
| `baseline` | `UploadFile` | Current Canvas snapshot |
| `quercus` | `UploadFile` | Cleaned Quercus CSV |

Returns ZIP:
- `YYYYMMDD_canvas.csv` — 11-col Canvas SIS import (new users only)
- `YYYYMMDD_canvas_all_pre.csv` — updated reference file

---

### Google Workspace Pipeline

#### `POST /google/export`
| Field | Type | Description |
|-------|------|-------------|
| `baseline` | `UploadFile` | Current Google snapshot |
| `quercus` | `UploadFile` | Cleaned Quercus CSV |

Returns ZIP:
- `YYYYMMDD_google_upload.csv` — 24-col Google upload (UUID passwords)
- `YYYYMMDD_google_reactivate.csv` — 7-col reactivation candidates (suspended + in Quercus)

---

### OpenAthens Pipeline

#### `POST /athens/export`
| Field | Type | Description |
|-------|------|-------------|
| `baseline` | `UploadFile` | Current Athens snapshot |
| `quercus` | `UploadFile` | Cleaned Quercus CSV |

Returns ZIP:
- `YYYYMMDD_athens_new_users.csv` — debug file of detected new users
- `YYYYMMDD_athens.csv` — 21-col Athens upload template

Constants: `groups=ncad_students`, `status=pending`, `expiry=2026-09-23`,
`permissionSets=cad#0001`, `emailUser?=TRUE`, `allowEmailLogin?=TRUE`.

---

### Library Pipeline (Standalone)

#### `POST /library/export`
| Field | Type | Description |
|-------|------|-------------|
| `files` | `UploadFile[]` | Raw Quercus CSV files (no baseline needed) |

Returns ZIP:
- `YYYYMMDD_library_cleaned.csv` — debug: cleaned intermediate data
- `YYYYMMDD_library.csv` — 46-col Library upload template

Constants: `institutionId=46722`, `homeBranch=266006`, `sourceSystem=https://idp.ncad.ie/idp/shibboleth`.

---

### Legacy Endpoints

#### `POST /export/all`
Single Quercus file → JSON preview of all 4 legacy pipelines. Uses `quercus_transform.py` (not `quercus_preprocess.py`).

#### `POST /export/bundle`
Single Quercus file → ZIP with all 4 legacy exports. Same machinery as `/export/all`.

---

## Data Flow Architecture

### Preprocessing (shared by all pipelines)

```
Quercus CSV(s)
    │ merge in upload order
    │ strip column names
    ▼
merge_quercus_files()
    │
    ▼
preprocess_quercus()
    1. Create Term Email from zero-padded 8-digit ID Number
    2. Remove blank emails
    3. Keep only Status="Registered" or starts with "Recommend"
    4. Remove "NCAD Elective - External Students"
    5. Deduplicate by Term Email (keep first)
    6. Assign Type: CEAD (<101), UG (101-400), PG (401+)
    │
    ▼
Cleaned DataFrame (stored in PipelineContext on frontend)
    │
    ├──→ LDAP pipeline     (baseline comparison via email)
    ├──→ Canvas pipeline    (baseline comparison via email)
    ├──→ Google pipeline    (baseline comparison via email)
    ├──→ Athens pipeline    (baseline comparison via email)
    └──→ Library pipeline   (direct mapping, no baseline)
```

### Baseline Comparison Pattern (LDAP / Canvas / Google / Athens)

```
Quercus (cleaned)                     Baseline (system snapshot)
       │                                     │
       │ map_quercus_to_*()                  │ normalize_baseline_schema()
       │                                     │
       ▼                                     ▼
  Quercus-mapped DataFrame           Normalized Baseline DataFrame
       │                                     │
       └─────────────┬──────────────────────┘
                     │ detect_new_users() — email identity check
                     │ (Quercus email NOT in baseline emails)
                     ▼
              New Users DataFrame
                     │
                     ├──→ generate_upload_export()
                     ├──→ generate_reactivation_export()  (Google only)
                     │
                     └──→ update_baseline_state() — concat + deduplicate
                              │
                              ▼
                         Updated Baseline
```

### Library (no baseline, direct mapping)

```
Quercus CSV(s)
    │ merge
    │ clean_library_data() (calls preprocess_quercus internally)
    ▼
Cleaned DataFrame (with borrowerCategory)
    │
    ▼
build_library_template() — pure 46-column mapping
    │
    ▼
Library CSV
```

---

## File-by-File Walkthrough

### Backend

#### `api/routes.py`
Mounts all routers under prefixes. The single registration point for every endpoint. Add a new pipeline here.

#### `api/quercus.py`
Two endpoints:
- `/quercus/upload`: merges files → preprocesses → returns JSON (preview + audit)
- `/quercus/download`: same pipeline → returns CSV file

Key detail: reads CSVs with `pd.read_csv(io.StringIO(...))` and strips column whitespace. This is the canonical CSV-reading pattern used across all endpoints.

#### `api/ldap.py`
Two endpoints:
- `/ldap/export`: returns JSON preview (sanitizes NaN → None)
- `/ldap/download`: returns file (ZIP or CSV)

Supports `.xlsx` baseline files (detected by extension). Calls `preprocess_quercus()` then `generate_ldap_comparison_exports()`.

#### `api/canvas.py`, `api/google.py`, `api/athens.py`
Identical pattern to ldap.py — read baseline + quercus → preprocess → call service. Each returns a ZIP.

#### `api/library.py`
Different: accepts multiple files (no baseline), calls `clean_library_data()` + `build_library_template()`. Returns ZIP with debug CSV.

#### `api/export.py`
Legacy endpoints. Uses `quercus_transform.py` (different preprocessing logic — filters on "Recommended" not "Recommend", uses "Normalized ID" dedup not "Term Email"). Do NOT use for new work.

#### `services/quercus_preprocess.py` (SOURCE OF TRUTH)
The one preprocessing pipeline used by all 5 downstream services. Key functions:
- `clean_id_number()` — zero-pads to 8 digits, strips `.0` floats
- `merge_quercus_files()` — concat in order, strip column names
- `extract_course_number()` — regex: letters→digits for course code
- `preprocess_quercus()` — the full 6-step pipeline (see data flow above)

Important: `preprocess_quercus()` writes audit counters to `df.attrs` (filtered_out_status_count, external_students_removed_count, duplicate_rows_detected). These are read by LDAP/Canvas/Google/Athens services for the audit_info response.

#### `services/ldap_export.py`
13-column LDAP schema. Key functions:
- `normalize_email_identity()` — resolves "Email_address" or "Term Email"
- `normalize_baseline_schema()` — case-insensitive column rename + fill missing
- `map_quercus_to_ldap()` — renames Quercus columns → LDAP columns
- `detect_new_students()` — email set diff
- `assign_passcodes()` — calls `generate_passcode()` from utils
- `update_baseline_state()` — concat + deduplicate
- `generate_ldap_comparison_exports()` — orchestrates all of the above
- `_format_dob_series()` — multi-format DOB parser (dd/mm/yy, dd-Mon-yy, ISO, Excel serial fallback)

The DOB parser is notable: 3 regex patterns + Excel serial date fallback, with two-digit year expansion (rolling cutoff based on current year).

#### `services/canvas_service.py`
11-column Canvas schema. Functions mirror ldap_export.py (normalize, detect_new_users, update_baseline_state). Also has legacy `generate_canvas_export()`.

Key detail: Canvas mapping creates `full_name` (First + Last) and `sortable_name` (Last,First). Status is hardcoded to "active".

#### `services/google_service.py`
24-column upload schema + 7-column reactivation schema. Unique features:
- `diff_reactivation_candidates()` — finds suspended baseline users who are back in Quercus
- `generate_password()` — UUID4-based passwords
- Org Unit mapping via `/UG`, `/PG`, `/CEAD` paths

#### `services/athens_service.py`
21-column upload template. Constants hardcoded per NCAD SOP: `ncad_students`, `pending`, `2026-09-23`, `cad#0001`, `TRUE`.

#### `services/library_service.py`
Two-stage pipeline:
1. `clean_library_data()` — reuses `preprocess_quercus()`, adds `borrowerCategory` (CEAD/FTUG/FTPG by course number)
2. `build_library_template()` — pure 46-column mapping with constants (institutionId=46722, homeBranch=266006)

Gender validation: blanks → UNKNOWN, Male/Female → MALE/FEMALE.

#### `services/quercus_transform.py` (LEGACY)
Used only by `/export/all` and `/export/bundle`. Different from `quercus_preprocess.py`:
- Filters on "Recommended" (not "Recommend")
- Creates "Normalized ID" intermediate column
- Deduplicates by "Normalized ID" (not "Term Email")
- Drops the intermediate column before returning

#### `utils/passcode_generator.py`
Generates Word+Word+Word+Word+Number passcodes (e.g. "RiverForestCrystalStorm7"). Word list of 56 safe, non-offensive words.

---

### Frontend

#### `lib/pipeline-context.tsx`
React Context that stores the cleaned Quercus File object so downstream cards (LDAP, Canvas, Google, Athens) can send it with their baseline uploads. Mounted in root layout, persists across page navigation.

State: `cleanedQuercusFile`, `auditInfo`, `sampleRows`, `step1Done`.

#### `lib/api.ts`
Fetch wrappers for every backend endpoint. Each function constructs FormData, calls the endpoint, and returns the response (JSON, Blob, or typed result). Key functions:
- `uploadQuercus()` — uploads → downloads cleaned file in one flow
- `downloadLdapExport()`, `downloadGoogleExport()`, etc. — single-call export

#### `app/quercus/page.tsx`
The main pipeline page. Shows:
1. Quercus upload card (always visible)
2. 4 downstream cards (LDAP, Canvas, Google, Athens) — visible only after step1 is done

Grid: `md:grid-cols-2` (2×2 layout on desktop).

#### `app/library/page.tsx`
Standalone page. No dependency on PipelineContext. Calls `POST /library/export` directly.

#### `components/*-step.tsx`
Each pipeline step is a self-contained component that:
1. Shows a file upload dropzone for the baseline CSV
2. On upload, calls the corresponding API
3. Shows a ProcessingProgress animation during the fetch
4. Triggers browser download of the returned blob

---

## Filename Convention

All output files follow: `YYYYMMDD_<system>[_<description>].csv`

Examples:
- `20260630_quercus.csv`
- `20260630_ldap_new_students.csv`
- `20260630_ldap_updated_baseline.csv`
- `20260630_canvas.csv`
- `20260630_canvas_all_pre.csv`
- `20260630_google_upload.csv`
- `20260630_google_reactivate.csv`
- `20260630_athens_new_users.csv`
- `20260630_athens.csv`
- `20260630_library_cleaned.csv`
- `20260630_library.csv`

ZIP files follow: `YYYYMMDD_<system>_export.zip`

The date suffix is generated once per request: `datetime.now().strftime("%Y%m%d")`.

---

## Key Design Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Email-based identity** | `Term Email` (`${studentId}@student.ncad.ie`) is the canonical key across all systems. Consistent email formatting eliminates matching errors. |
| 2 | **Deduplication keeps first** | Files merged in chronological order (oldest → newest). `drop_duplicates(keep="first")` preserves historic records. |
| 3 | **Status filter before dedup** | A student may appear as Withdrawn and Registered. Filtering status first ensures the valid record is kept, not suppressed by an earlier invalid entry. |
| 4 | **Library is standalone** | Library has no baseline file — no diff needed. Separate route avoids confusion with the 4-pipeline flow. |
| 5 | **Library reuses preprocess_quercus()** | Not a separate cleaning implementation. `clean_library_data()` calls the same preprocessing as all other pipelines. |
| 6 | **Library barcode = student ID** | Zero-padded 8-digit student ID (same as `idAtSource`). Previously was a constant placeholder. |
| 7 | **Gender → MALE/FEMALE/UNKNOWN** | Blanks or unknown values are explicitly set to UNKNOWN to avoid validation errors in the Library system. |
| 8 | **DOB: explicit strptime per pattern** | No pandas `to_datetime(format="mixed")` — too many format ambiguities. 3 explicit regex patterns + Excel serial fallback. |
| 9 | **Baseline supports .xlsx** | Detected by file extension. Uses `pd.read_excel(engine="openpyxl")`. All 4 baseline-accepting endpoints support it. |
| 10 | **Google: reactivation detection** | Suspended accounts who reappear in Quercus are flagged for reactivation instead of being re-created. |
| 11 | **Canvas: 11-column SIS format** | Matches Canvas SIS import requirements. `full_name` and `sortable_name` derived from first/last. |
| 12 | **Athens: 21-column template** | Matches OpenAthens bulk upload schema. Constants reflect NCAD's current configuration. |
| 13 | **Frontend uses PipelineContext** | Avoids re-uploading Quercus for each downstream pipeline. The cleaned File object is stored once and reused. |

---

## How to Add a New Pipeline

1. **Create the service** in `backend/app/services/`: implement normalize_baseline_schema, normalize_email_identity, detect_new_users, generate_upload_export functions.
2. **Create the API file** in `backend/app/api/`: follow the pattern in `athens.py` or `canvas.py` — read baseline + quercus, preprocess, call your service, return ZIP.
3. **Register the router** in `backend/app/api/routes.py`.
4. **Add the fetch wrapper** in `frontend/lib/api.ts`.
5. **Create the step component** in `frontend/components/`: copy pattern from `athens-step.tsx`.
6. **Import the component** in `frontend/app/quercus/page.tsx` and add a `<Card>`.

---

## Tests

There is no automated test suite yet. The existing `test_ldap.py` in `backend/app/services/` is a manual script — not integrated with pytest.

To run a manual test:
```bash
cd backend
.venv\Scripts\activate
python -c "from app.services.ldap_export import _format_dob_series; import pandas as pd; print(_format_dob_series(pd.Series(['24/08/72', '24-Aug-72', '1972-08-24', ''])))"
```

When writing tests, test each service's functions in isolation (normalize, detect_new_users, generate_upload_export). Use `pytest` with CSV fixture files in `tests/`.

---

## Common Gotchas

- **preprocess_quercus vs transform_quercus**: These are NOT the same. The former is the source of truth (used by all current pipelines). The latter is legacy (used only by `/export/all`). Do not mix them up.
- **"Recommend" vs "Recommended"**: `preprocess_quercus()` checks for `startswith("Recommend")`. `transform_quercus()` checks for `startswith("Recommended")`. This difference matters if your data uses one form.
- **df.attrs**: Audit metadata is stored in DataFrame attrs. These are lost after pandas operations like `concat` or `copy(deep=True)`. Read them immediately after preprocessing.
- **XLSX baseline**: Requires `openpyxl` in the virtual environment. If you get "Missing optional dependency 'openpyxl'", run `pip install openpyxl`.
- **File encoding**: All CSVs are assumed UTF-8. The `io.StringIO(contents.decode("utf-8"))` pattern will fail on non-UTF-8 files.
