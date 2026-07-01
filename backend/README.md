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
| `ldap_export.py` | LDAP pipeline: baseline diff, DOB formatting, passcode generation |
| `canvas_service.py` | Canvas pipeline: baseline diff, 11-col SIS format |
| `google_service.py` | Google pipeline: diff + reactivation detection, 24-col upload |
| `athens_service.py` | OpenAthens pipeline: diff, 21-col upload template |
| `library_service.py` | Library pipeline: two-stage clean → template, 46 cols |

## Key Gotchas

- **df.attrs** — audit counters stored here are lost after many pandas operations. Read them immediately after preprocessing.
- **XLSX support** — requires `openpyxl`. Detected by `.xlsx` extension in filename.

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
