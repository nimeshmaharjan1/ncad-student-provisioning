# NCAD Student Provisioning Automation System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Automates student account creation and updates across **5 institutional systems** (LDAP, Canvas, Google Workspace, OpenAthens, Library) from Quercus CSV exports. Replaces manual Excel-based processes.

**API:** `http://localhost:8000` · **UI:** `http://localhost:3000`

---

> ## IMPORTANT — this is the NCAD shared-drive master copy
> **Never run `start.bat` / `start.sh` from this shared folder.** Network
> drives are too slow for the dependency install/build and break with
> concurrent use.
>
> 1. Copy this whole folder to your own machine (Desktop, Documents, …).
> 2. Run the launcher there — it installs everything and starts the servers.
> 3. On macOS, if you see `Permission denied`: `chmod +x start.sh` (or `bash start.sh`).

---

## Quick Start

### One-click launcher (no manual steps)

Double-click the launcher for your OS — it installs dependencies, starts both servers, and opens the browser:

- **Windows:** double-click `start.bat`
- **macOS/Linux:** run `bash start.sh` (no permissions needed) or `./start.sh` after a one-time `chmod +x start.sh`. If you ever see `Permission denied`, the file lost its executable bit — run `chmod +x start.sh` once (a fresh clone already has it set).

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
| `GET/PUT /admin/settings` | Per-system validation modes (warn/block) | JSON body on PUT |
| `POST /quercus/upload` | Preview + audit | 1+ Quercus CSVs |
| `POST /quercus/download` | Cleaned CSV | 1+ Quercus CSVs |
| `POST /ldap/download` | ZIP (new + baseline) | baseline + quercus |
| `POST /canvas/export` | ZIP | baseline + quercus |
| `POST /google/export` | ZIP (upload + reactivate) | baseline + quercus |
| `POST /athens/export` | ZIP | baseline + quercus |
| `POST /library/export` | ZIP (cleaned + template) | 1+ Quercus CSVs |
| `POST /staff/canvas/*` | Staff Canvas generation/export | JSON names |
| `POST /staff/library/*` | Staff Library generation/export | JSON people |

---

## Documentation

### Where to go next

Start with the one that matches who you are:

| You're… | Start with… |
|---|---|
| Using it week-to-week (non-IT) | [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) — step-by-step operation |
| Developer / maintainer | [`docs/ONBOARDING.md`](docs/ONBOARDING.md) — every file, APIs, design decisions |
| Testing a change | [`docs/MANUAL_TESTING.md`](docs/MANUAL_TESTING.md) — test scenarios |
| Planning the automation end-goal | [`docs/AUTOMATION_ROADMAP.md`](docs/AUTOMATION_ROADMAP.md) — the manager-facing vision |

Short version: read this README → run it via the launcher → then pick a guide
by your role above.

**[→ Full Developer Onboarding Guide](docs/ONBOARDING.md)**

Covers: setup, every file in the codebase, pipeline architecture, API details with input/output schemas, 13 key design decisions, how to add a new pipeline, common gotchas.

Additional docs:
- [`docs/AUTOMATION_ROADMAP.md`](docs/AUTOMATION_ROADMAP.md) — **project document**: end goal (weekly zero-touch automation), scheduler concept, harsh realities/blockers, phased plan, and the Ask-John sheet (who to ask, where to get credentials, fallbacks)
- [`docs/architecture.md`](docs/architecture.md) — original design document
- [`docs/MANUAL_PROCESS.md`](docs/MANUAL_PROCESS.md) — the legacy manual process this system replaces
- [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) — step-by-step tutorial for non-IT staff using the system
- [`docs/AUTOMATION_STRATEGY.md`](docs/AUTOMATION_STRATEGY.md) — what else can be automated and in what order
- [`docs/MANUAL_TESTING.md`](docs/MANUAL_TESTING.md) — step-by-step manual test guide with input-file scenarios
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
- **Per-system validation modes**: missing required columns warn-and-proceed with the columns auto-added blank (with an `X-Missing-Required` response header) unless a system is set to strict/block — configurable via `GET/PUT /admin/settings` and the `/settings` UI, with `VALIDATION_MODE_<SYSTEM>` env vars taking precedence. All systems default to warn; `Date of Birth` (LDAP) never blocks in any mode — the Discoverer report no longer exports it (GDPR) and the LDAP admin allows empty values.

See [ONBOARDING.md](docs/ONBOARDING.md) for the full list with rationale.

---

## Purpose

Internal NCAD IT provisioning tool. Designed for long-term maintainability and handover.