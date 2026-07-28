# Backend — NCAD Student Provisioning

FastAPI + pandas processing engine.

## Entry Point

`app/main.py` — creates the FastAPI app, includes the central router, and registers a global exception handler that logs all unhandled exceptions.

### Global Exception Handler

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
```

All route handlers also have per-endpoint try/except blocks (see below). The global handler is a safety net for anything that slips through.

## Router Registration

`app/api/routes.py` — every endpoint is registered here under a prefix:
- `/quercus` → `api/quercus.py`
- `/ldap` → `api/ldap.py`
- `/canvas` → `api/canvas.py`
- `/google` → `api/google.py`
- `/athens` → `api/athens.py`
- `/library` → `api/library.py`

Add a new pipeline: create the API file → register it here.

## Architecture

```
api/*.py          → HTTP layer (file I/O, validation, response)
    │
    ▼
services/*.py     → Business logic (diff, mapping, code generation)
    │
    ▼
utils/*.py        → Shared utilities (passcode generator, date utils, DataFrame helpers)
```

## Error Handling Pattern (all endpoints)

Every export endpoint follows the same pattern:

### 1. Schema Validation (before processing)

Each endpoint defines required and optional Quercus column lists. Before any processing, the route handler checks the uploaded CSV columns:

```python
quercus_cols = set(quercus_df.columns)
missing_required = [col for col in REQUIRED_COLS if col not in quercus_cols]
missing_optional = [col for col in OPTIONAL_COLS if col not in quercus_cols]

if missing_required:
    return JSONResponse(
        status_code=422,
        content={
            "detail": f"Missing required columns: {', '.join(missing_required)}",
            "error_code": "missing_required_columns",
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "present_columns": sorted(quercus_cols),
            "all_required": REQUIRED_COLS,
            "all_optional": OPTIONAL_COLS,
        },
    )
```

If required columns are missing → **422** with structured JSON listing exactly what's needed.

If only optional columns are missing → logs a warning, proceeds with processing (columns are left blank).

### 2. Try/Except Blocks

```python
try:
    # ... processing ...
except ValueError as e:
    logger.exception("Error description")
    return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "bad_request"})
except KeyError as e:
    logger.exception("Missing column")
    return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "missing_columns"})
except Exception:
    logger.exception("Unexpected error")
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error", "error_code": "internal_error"})
```

| HTTP Code | When | Frontend shows |
|-----------|------|----------------|
| **422** | Missing required columns | Rich error card with column lists |
| **400** | Bad request / missing column in service | Error message from the backend |
| **500** | Unexpected error | "Unexpected server error" + terminal traceback |

### 3. Logging

Every module uses `logger = logging.getLogger(__name__)`. Logging is configured in `main.py`:
```python
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
```

- `logger.warning()` — for schema validation failures (missing required columns)
- `logger.exception()` — in except blocks (logs traceback automatically)
- `logger.info()` — for missing optional columns

## Required / Optional Columns per System

### LDAP (`api/ldap.py`, `services/ldap_export.py`)

| Type | Columns |
|------|---------|
| Required | `ID Number`, `Course Code`, `Course Description`, `Course Instance Course Year`, `Type`, `First Name`, `Last Name`, `Date of Birth`, `Term Email`, `LDAP ID` |
| Optional | `Home Mobile Phone` |

### Canvas (`api/canvas.py`, `services/canvas_service.py`)

| Type | Columns |
|------|---------|
| Required | `ID Number`, `First Name`, `Last Name`, `Term Email` |
| Optional | (none) |

### Google Workspace (`api/google.py`, `services/google_service.py`)

| Type | Columns |
|------|---------|
| Required | `ID Number`, `First Name`, `Last Name` |
| Optional | (none) |

### OpenAthens (`api/athens.py`, `services/athens_service.py`)

| Type | Columns |
|------|---------|
| Required | `ID Number`, `First Name`, `Last Name` |
| Optional | (none) |

### Library (`api/library.py`, `services/library_service.py`)

| Type | Columns |
|------|---------|
| Required | `ID Number` |
| Optional | `First Name`, `Last Name`, `Gender`, `Course Code`, `Course Instance Start Date`, `Course Instance End Date` |

## Service Files (what each does)

| File | Purpose |
|------|---------|
| `quercus_preprocess.py` | **Source of truth** — merge, clean, deduplicate, assign Type |
| `ldap_export.py` | LDAP pipeline: baseline diff, DOB formatting, passcode generation |
| `canvas_service.py` | Canvas pipeline: baseline diff, 11-col SIS format |
| `google_service.py` | Google pipeline: diff + reactivation detection, 24-col upload |
| `athens_service.py` | OpenAthens pipeline: diff, 21-col upload template |
| `library_service.py` | Library pipeline: two-stage clean → template, 46 cols |

## Key Gotchas

- **df.attrs** — audit counters stored here are lost after many pandas operations. Read them immediately after preprocessing.
- **XLSX support** — requires `openpyxl`. Detected by `.xlsx` extension in filename.
- **Column name normalization** — `normalize_baseline_schema()` in `df_utils.py` does case-insensitive column matching. Add Google-specific `alias_map` for renames like "Status [READ ONLY]" → "Status".
- **Identity key** — `Term Email` (`${studentId}@student.ncad.ie`) is the canonical key across all systems. All baseline comparisons use this.

## Run

```bash
cd backend
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Dependencies

See `../requirements.txt`. Key packages: `fastapi`, `pandas`, `openpyxl`, `uvicorn`.

For full developer onboarding, see [`../docs/ONBOARDING.md`](../docs/ONBOARDING.md).
