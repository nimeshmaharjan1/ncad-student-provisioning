# System Architecture — NCAD Student Provisioning

## Overview

Automates student account creation across **5 systems** from Quercus CSV exports through a centralized FastAPI + pandas pipeline with a Next.js frontend.

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, React, shadcn/ui, Tailwind CSS |
| Backend | FastAPI (Python 3.10+) |
| Data | pandas, openpyxl |
| Communication | REST over HTTP (`multipart/form-data` for file uploads) |

## Data Flow

```
                        ┌──────────────────────┐
                        │   Quercus CSV(s)     │
                        └──────────┬───────────┘
                                   │ merge, strip columns
                                   ▼
                        ┌──────────────────────┐
                        │  preprocess_quercus  │  ← source of truth
                        │  1. Create Term Email │
                        │  2. Filter Status     │
                        │  3. Remove externals  │
                        │  4. Deduplicate       │
                        │  5. Assign Type       │
                        └──────────┬───────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
            ┌───────────┐  ┌───────────┐  ┌───────────┐
            │ LDAP      │  │ Canvas    │  │ Google    │
            │ Athens    │  │           │  │           │
            └───────────┘  └───────────┘  └───────────┘
                    │              │              │
                    │  baseline    │  baseline    │  baseline
                    │  comparison  │  comparison  │  comparison
                    ▼              ▼              ▼
            ┌───────────┐  ┌───────────┐  ┌───────────┐
            │ new users  │  │ SIS import│  │ upload +  │
            │ + passcodes│  │           │  │reactivate │
            └───────────┘  └───────────┘  └───────────┘

                        ┌──────────────────────┐
                        │   Library (standalone)│
                        │   No baseline needed  │
                        │   Direct 46-col map   │
                        └──────────────────────┘
```

## Baseline Comparison Pattern

Used by LDAP, Canvas, Google, Athens:

1. **Normalize baseline schema** — case-insensitive column rename, fill missing
2. **Map Quercus to target schema** — rename/map columns
3. **Diff by email** — Quercus emails not in baseline emails → new users
4. **Generate upload file** — apply system-specific formatting/constants
5. **Update baseline** — concat + deduplicate for next run

## API Design

All endpoints are `POST` with `multipart/form-data` file uploads. Responses are either JSON (preview) or streaming file downloads (CSV/ZIP).

Each pipeline is independent — Quercus preprocessing is the only shared step. All pipelines call `preprocess_quercus()` from `services/quercus_preprocess.py`.

## Frontend Architecture

- React Context (`PipelineContext`) stores the cleaned Quercus File object for reuse
- Two top-level routes: `/quercus` (4-card pipeline) and `/library` (standalone)
- Each pipeline step is a self-contained component with upload → process → download flow

## Key Properties

- **Deterministic**: same inputs → same outputs (except randomized passcodes/UUIDs)
- **Stateless**: no database, no sessions — everything is file-in, file-out
- **Independent pipelines**: each system can be run independently of the others
- **Backward-compatible**: legacy `/export/all` and `/export/bundle` endpoints preserved

## Out of Scope

- Direct API integrations with external systems (file-based handoff only)
- Database storage or audit trail
- Real-time syncing or event-driven processing
- Role-based access control

---

**For detailed developer onboarding, see [ONBOARDING.md](ONBOARDING.md).**
