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

All required/optional column lists live in ONE place: `app/core/quercus_schema.py`
(the **Quercus Schema Registry**). Endpoints call `check_columns()` and only decide
what to do with the result:

```python
from app.core.quercus_schema import check_columns, missing_required_response

check = check_columns("ldap", quercus_df.columns)   # system key, see SCHEMAS
if check["missing_required"]:
    return missing_required_response("ldap", check)  # structured 422
if check["missing_optional"]:
    logger.info("Optional columns missing (will be left blank): %s", check["missing_optional"])
```

If required columns are missing → **422** with structured JSON listing exactly what's needed.

If only optional columns are missing → logs a warning, proceeds with processing (columns are left blank).

The Quercus upload step (`api/quercus.py`) uses **WARN mode** instead: `check_source_columns()`
never blocks — it returns the missing columns so the frontend can show a warning card asking
the user to recheck their Quercus export settings before continuing.

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

## Quercus Schema Registry (`app/core/quercus_schema.py`)

The single source of truth for every system's Quercus column contract. Read the
module docstring — it documents the design decisions in full.

| System key | Display name | Required (Quercus) | Optional (Quercus) |
|------------|--------------|--------------------|--------------------|
| `ldap` | LDAP | `ID Number`, `Course Code`, `Course Description`, `Course Instance Course Year`, `Type`, `First Name`, `Last Name`, `Date of Birth`, `Term Email`, `LDAP ID` | `Home Mobile Phone` |
| `canvas` | Canvas | `ID Number`, `First Name`, `Last Name`, `Term Email` | (none) |
| `google` | Google Workspace | `ID Number`, `First Name`, `Last Name` | (none) |
| `athens` | OpenAthens | `ID Number`, `First Name`, `Last Name` | (none) |
| `library` | Library | `ID Number` | `First Name`, `Last Name`, `Gender`, `Course Code`, `Course Instance Start Date`, `Course Instance End Date` |

### Two validation modes

- **STRICT** (export endpoints): `check_columns(system_key, columns)` + `missing_required_response(system_key, check)` → missing required columns return a structured 422.
- **WARN** (Quercus upload step): `check_source_columns(columns)` → never blocks, returns missing columns for the frontend warning card. The warn list is computed automatically from the union of all `required` lists minus columns `preprocess_quercus()` generates (`Term Email`, `Type`), plus `EXTRA_SOURCE_WARN_COLUMNS` (`Status` — silently skipped filtering otherwise).

### How to add a new system (e.g. Moodle)

1. Add one `SystemSchema` entry to `SCHEMAS` in `app/core/quercus_schema.py`.
2. In the new API endpoint, replace inline validation with `check_columns("moodle", ...)` / `missing_required_response("moodle", check)`.
3. Done — the Quercus upload warning list picks up the new system's required columns automatically.

### How to change existing columns

Edit the relevant `SCHEMAS` entry. Every endpoint and the upload warning read from this module, so the change applies everywhere. If you remove a column from a `required` tuple, also review `EXTRA_SOURCE_WARN_COLUMNS` to decide whether upload should still warn about it.

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
