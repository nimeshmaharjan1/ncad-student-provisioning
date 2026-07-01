# NCAD Student Provisioning Automation System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Automates student account creation and updates across **5 institutional systems** (LDAP, Canvas, Google Workspace, OpenAthens, Library) from Quercus CSV exports. Replaces manual Excel-based processes.

**API:** `http://localhost:8000` · **UI:** `http://localhost:3000`

---

## Quick Start

### One-click launcher (no manual steps)

Double-click the launcher for your OS — it installs dependencies, starts both servers, and opens the browser:

- **Windows:** double-click `start.bat`
- **macOS/Linux:** run `./start.sh`

### Manual setup

```bash
# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r ../requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## System Architecture

```
Quercus CSV(s)
    │
    ▼
preprocess_quercus() — merge, clean, deduplicate, assign Type
    │
    ├──→ LDAP     (baseline diff → new students + passcodes)
    ├──→ Canvas   (baseline diff → 11-col SIS import)
    ├──→ Google   (baseline diff → upload + reactivation)
    ├──→ Athens   (baseline diff → 21-col template)
    └──→ Library  (direct mapping → 46-col template)
```

All pipelines (except Library) compare Quercus data against a system-specific baseline snapshot to detect new users.

---

## Entry Points

| Path | What | Inputs |
|------|------|--------|
| `POST /quercus/upload` | Preview + audit | 1+ Quercus CSVs |
| `POST /quercus/download` | Cleaned CSV | 1+ Quercus CSVs |
| `POST /ldap/download` | ZIP (new + baseline) | baseline + quercus |
| `POST /canvas/export` | ZIP | baseline + quercus |
| `POST /google/export` | ZIP (upload + reactivate) | baseline + quercus |
| `POST /athens/export` | ZIP | baseline + quercus |
| `POST /library/export` | ZIP (cleaned + template) | 1+ Quercus CSVs |

---

## Documentation

**[→ Full Developer Onboarding Guide](docs/ONBOARDING.md)**

Covers: setup, every file in the codebase, pipeline architecture, API details with input/output schemas, 13 key design decisions, how to add a new pipeline, common gotchas.

Additional docs:
- [`docs/architecture.md`](docs/architecture.md) — original design document
- [`backend/README.md`](backend/README.md) — backend specifics
- [`frontend/README.md`](frontend/README.md) — frontend specifics

---

## Filename Convention

All outputs use `YYYYMMDD_<system>[_<description>].csv`. ZIP files use `YYYYMMDD_<system>_export.zip`.

---

## Key Design Decisions

- **Email-based identity**: `Term Email` (`${studentId}@student.ncad.ie`) is the canonical key across all systems.
- **Deduplication keeps first**: Files merged in chronological order (oldest → newest), `keep="first"`.
- **Status filter before dedup**: A student may appear as Withdrawn AND Registered — filter status first.
- **Library is standalone**: No baseline, no diff. Separate page. Reuses the same `preprocess_quercus()`.
- **Baseline supports .xlsx**: Detected by file extension, read with `openpyxl`.

See [ONBOARDING.md](docs/ONBOARDING.md) for the full list with rationale.

---

## Purpose

Internal NCAD IT provisioning tool. Designed for long-term maintainability and handover.