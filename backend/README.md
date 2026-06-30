# Backend — NCAD Student Provisioning

FastAPI + pandas processing engine.

## Entry Point

`app/main.py` — creates the FastAPI app and includes the central router.

## Router Registration

`app/api/routes.py` — every endpoint is registered here under a prefix:
- `/quercus` → `api/quercus.py`
- `/ldap` → `api/ldap.py`
- `/canvas` → `api/canvas.py`
- `/google` → `api/google.py`
- `/athens` → `api/athens.py`
- `/library` → `api/library.py`
- `/export` → `api/export.py` (legacy)

Add a new pipeline: create the API file → register it here.

## Architecture

```
api/*.py          → HTTP layer (file I/O, validation, response)
    │
    ▼
services/*.py     → Business logic (diff, mapping, code generation)
    │
    ▼
utils/*.py        → Shared utilities (passcode generator, etc.)
```

## Service Files (what each does)

| File | Purpose |
|------|---------|
| `quercus_preprocess.py` | **Source of truth** — merge, clean, deduplicate, assign Type |
| `quercus_transform.py` | **Legacy** — different preprocessing used only by `/export/*` |
| `ldap_export.py` | LDAP pipeline: baseline diff, DOB formatting, passcode generation |
| `ldap_service.py` | Legacy 4-column LDAP mapper used by `/export/*` |
| `canvas_service.py` | Canvas pipeline: baseline diff, 11-col SIS format + legacy mapper |
| `google_service.py` | Google pipeline: diff + reactivation detection, 24-col upload |
| `athens_service.py` | OpenAthens pipeline: diff, 21-col upload template |
| `library_service.py` | Library pipeline: two-stage clean → template, 46 cols |
| `export_pipeline.py` | Legacy: runs all legacy mappers at once for `/export/*` |

## Key Gotchas

- **`preprocess_quercus` vs `transform_quercus`** — not interchangeable. All current pipelines use `preprocess_quercus`. Only `/export/all` and `/export/bundle` use `transform_quercus`.
- **`"Recommend"` vs `"Recommended"`** — `preprocess_quercus` checks `startswith("Recommend")`. `transform_quercus` checks `startswith("Recommended")`.
- **df.attrs** — audit counters stored here are lost after many pandas operations. Read them immediately after preprocessing.
- **XLSX support** — requires `openpyxl`. Detected by `.xlsx` extension in filename.

## Run

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

## Dependencies

See `../requirements.txt`. Key packages: `fastapi`, `pandas`, `openpyxl`, `uvicorn`.

For full developer onboarding, see [`../docs/ONBOARDING.md`](../docs/ONBOARDING.md).
