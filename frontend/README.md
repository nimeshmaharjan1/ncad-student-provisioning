# Frontend — NCAD Student Provisioning

Next.js UI with shadcn/ui components.

## Pages

| Route | File | Purpose |
|-------|------|---------|
| `/` | `app/page.tsx` | Home — 2-card navigation (Pipeline / Library) |
| `/quercus` | `app/quercus/page.tsx` | Main pipeline: Quercus → LDAP, Canvas, Google, Athens |
| `/library` | `app/library/page.tsx` | Standalone Library export (no pipeline dependency) |

## Components

| Component | Purpose |
|-----------|---------|
| `quercus-step.tsx` | Upload Quercus CSVs → process → preview |
| `ldap-step.tsx` | Upload LDAP baseline → download ZIP |
| `canvas-step.tsx` | Upload Canvas baseline → download ZIP |
| `google-step.tsx` | Upload Google baseline → download ZIP |
| `athens-step.tsx` | Upload Athens baseline → download ZIP |
| `library-step.tsx` | Upload Library CSVs → download ZIP |
| `file-upload.tsx` | Reusable drag-and-drop file upload zone |
| `data-table.tsx` | Preview table for sample rows |
| `audit-summary.tsx` | Row count summary display |

## State Management

`lib/pipeline-context.tsx` — React Context storing the cleaned Quercus File object. Wraps the entire app (in `layout.tsx`) so state persists across page navigation. Only used by `/quercus` pages. Library page does NOT use it.

## API Layer

`lib/api.ts` — typed fetch wrappers for every backend endpoint. Each constructs `FormData`, POSTs to the endpoint, and returns the parsed response.

## Proxy Config

`next.config.ts` rewrites `/quercus/*`, `/ldap/*`, `/canvas/*`, `/google/*`, `/athens/*`, `/library/*`, `/export/*` to `http://localhost:8000`.

## Run

```bash
cd frontend
npm install
npm run dev    # → http://localhost:3000
```

## Dependencies

Next.js, React, shadcn/ui, lucide-react, tailwindcss.

For full developer onboarding, see [`../docs/ONBOARDING.md`](../docs/ONBOARDING.md).
