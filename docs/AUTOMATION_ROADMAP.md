# Automation Roadmap — From Manual to Zero-Touch Provisioning

> Project document for the NCAD Student Provisioning system.
sophos> Audience: the department head (manager), the current process owner (IT
> support), and any future developer or IT support person who inherits this
> project.

This document is the single source of truth for **where we are**, **where the
manager wants us to go**, **what stops us**, and **what we do instead**.
Nothing here is final — it is a living plan to be reviewed with the manager and
the current process owner.

---

## 1. Current State — What Is Already Automated

Before this repo, the process owner did everything by hand: merging Quercus
exports in Excel, comparing against baselines, generating system files,
uploading them one by one, emailing passcodes with Thunderbird mail merge.

This repo already automates the **entire generation layer**:

| Step | Before (manual) | Now (this repo) |
|------|----------------------|-----------------|
| Merge multiple Quercus exports | Manual Excel work | `preprocess_quercus()` — merge, dedupe, filter |
| Detect new students per system | Manual baseline comparison | Baseline diff on email identity (LDAP, Canvas, Google, Athens) |
| Generate LDAP files + passcodes | Manual, error-prone | `generate_ldap_comparison_exports()` — 13-col output with word passcodes |
| Canvas SIS import file | Manual | 11-col SIS format |
| Google upload + reactivation | Manual | 24-col upload + suspended-account reactivation detection |
| OpenAthens template | Manual | 21-col template |
| Library borrower records | Manual | 46-col template |
| Error handling | Silent failures | Structured 422 errors + schema registry + warning cards |
| Documentation | In the process owner's head | ONBOARDING.md, USER_GUIDE.md, MANUAL_TESTING.md, in-app /about |

**Key point for the manager:** the hard logic (diffing, cleaning, generating)
is done and regression-tested. What remains manual is the *transport layer*:
getting the Quercus export, uploading outputs, sending emails.

---

## 2. End Goal — The Manager's Vision

> The system should pull student data from Quercus, check for new students,
> add them to all 5 systems by itself, send the emails, and keep logs — running
> automatically (e.g. every week) on a server, with no human in the loop.

A weekly scheduled run of: **intake → diff → generate → push → notify → log.**

Everything in this roadmap is measured against that goal. Sections 4–6 are the
honest assessment of what of that vision is achievable, what is not, and how
close we can get.

---

## 3. The Weekly Scheduler — Concept

The manager's idea, fleshed out: a scheduler on an always-on server runs the
provisioning pipeline once per week automatically.

```
Weekly trigger (cron / Windows Task Scheduler)
        │
        ▼
1. INTAKE     Watch drop-folder (SFTP inbox) for new Quercus export(s)
        │     (the only manual step left — see Harsh Reality #1)
        ▼
2. PIPELINE   Run the EXISTING backend services unchanged
        │     (preprocess → per-system diff → generate files + passcodes)
        ▼
3. PUSH       Per-system delivery as credentials allow:
        │     Library SFTP · Triangle LDAP SFTP · Canvas SIS API ·
        │     Google Directory API · OpenAthens API
        ▼
4. NOTIFY     Student passcode emails · Triangle Service Desk request ·
        │     "Canvas uploaded — notify the Canvas administrator" · failure alerts to IT
        ▼
5. LOG        Persistent run log: who/what/when, per-step status, errors
```

**Why this is achievable:** every pipeline step already exists as a pure
Python service. The scheduler only adds the *rails* — a trigger, a drop-folder
reader, per-system connectors, an email sender, and a log store. It does not
re-invent any business logic.

**Why it is NOT trivial:** see Harsh Realities #1–#8.

---

## 4. Harsh Realities — What Stops Us, and What We Do Instead

Each blocker lists an external factor (things outside this repo's control)
and the pragmatic alternative. The golden rule of this roadmap:
**every integration is additive and reversible.** If a credential is
unavailable, the scheduler skips that step and today's manual path still
works.

| # | Blocker (external factor) | Why it blocks | What we do instead |
|---|--------------------------|---------------|--------------------|
| 1 | **Quercus has NO API** (Ellucian). Data only via web UI export | "Pull from Quercus automatically" is impossible without fragile UI-robots (Puppeteer/Playwright), rejected in AUTOMATION_STRATEGY.md — any Ellucian UI change breaks it | Keep the ~5-minute manual export; the scheduler **watches a drop-folder (SFTP)** — the moment a new export lands, everything else runs automatically. Also ask the Quercus admin about *saved/scheduled report delivery* (see Credentials & Access Checklist #8) |
| 2 | **GDPR posture flips**. Automation requires storing student PII server-side (baselines, run logs). The current app explicitly promises transient processing | Storage of PII = a data-protection decision (DPIA-level), not a code decision | Documented decision required from the manager: secure storage, access control, encryption, retention policy. The public demo stays transient; the scheduler runs on a private server only |
| 3 | **Triangle Service Desk is a human gate**. Their confirmation is their business process | The confirmation step cannot be auto-approved | Auto-SFTP the LDAP files + auto-email the Service Desk, then **wait for a click-to-confirm** in a simple approval screen (human-in-the-loop for this one step only) |
| 4 | **APIs/credentials may not exist yet**: Canvas admin token, Google service account, OpenAthens API, SMTP details | Each push integration needs an administrator to create/issue credentials | Ship integrations **per system, in order of credential availability** (Credentials & Access Checklist, section 7). No credential → that step stays manual |
| 5 | **Hosting reality**. Current deployments are Vercel + Render — public, ephemeral, free-tier (instances sleep) | Not suitable as a scheduler host; also public by design | Dedicated always-on private server for the scheduler (Checklist #4). Demo deployments stay as they are — harmless and useful for demos |
| 6 | **Passcodes are sensitive**. Emails carry generated credentials | Sending PII+credentials by email needs security and consent practices, not just an SMTP call | Send passcodes only where the manager approves; encrypt secrets at rest; never log passcodes or PII (logs carry run IDs, counts, statuses only) |
| 7 | **Ownership & maintenance**. No deadline ≠ no risk | After the current process owner leaves, someone must own credentials, API changes, failed runs, renewals | This repo is the handover: everything documented (this file, ONBOARDING, MANUAL_TESTING). Manager assigns an owner for credentials and monitoring |
| 8 | **Half-failed runs**. A weekly run that dies mid-way must not send 2 of 5 exports | Silent partial provisioning is worse than no automation | Per-step status + **dry-run mode** (default) + explicit approval gate before any email/SFTP push; failure alerts to IT |

---

## 5. Recommended Phases

### Phase 1 — The Rails (no new credentials needed) ✅ do first
- Scheduler skeleton (cron / Task Scheduler) on a private server
- **Drop-folder intake** — detects a new Quercus export and runs the pipeline
- **Persistent run log** — every run recorded (step, status, counts, error)
- **Dry-run mode** — full pipeline output generated, nothing sent
- Deliverable for the manager: *"the system now runs itself every week —
  everything is generated and logged; we review before anything is sent."*

### Phase 2 — Push integrations (one per credential obtained)
- Library SFTP upload
- Triangle LDAP SFTP + auto-email to Service Desk (with confirm gate)
- Canvas SIS Import via API (needs admin token) + auto-notify the Canvas administrator
- Google Workspace auto-provisioning (needs service account)

### Phase 3 — Email & notifications
- Student passcode emails (per manager approval)
- Failure alerts and weekly summary to IT

### Phase 4 — Human-in-the-loop approval UI
- Review-and-confirm screen for the steps that must stay gated (Triangle
  confirmation, final "send emails" trigger)

### Phase 5 — Never (documented rejection)
- Full auto-pull from Quercus via UI-robots — fragile, high maintenance,
  low value for a 5-minute task (see AUTOMATION_STRATEGY.md)

---

## 6. Risks

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Credentials never obtained | Medium | Phased rollout; each step is optional; manual paths stay |
| Quercus export file changes format | Medium | Schema registry + structured warnings (already built) |
| Failed weekly run goes unnoticed | Medium | Failure alerts (Phase 3), run-log dashboard |
| PII stored despite GDPR promises | High if unchecked | Manager sign-off, retention policy, private server, encryption |
| Process owner's knowledge lost at handover | High | This repo + this document + Credentials & Access Checklist completed |
| Scope creep ("just automate everything") | High | This roadmap is the agreed scope; changes go through this doc |

---

## 7. Credentials & Access Checklist — What We Need, Who to Ask, Where to Get It

> Print this. Walk through it with the current process owner and the manager.
> Tick each item off. Every item includes: why, who to ask, how/where to get
> it, and the fallback if it can't be obtained.

| # | Item (why) | Who to ask | How / where to get it | Fallback if unavailable |
|---|-----------|-----------|----------------------|------------------------|
| 1 | **SMTP / email sending details** — replaces Thunderbird mail-merge; needed for passcode emails, Triangle Service Desk, and Canvas-administrator notifications | IT Services / whoever administers NCAD's Office 365 or Exchange | Ask for SMTP host + port (typically `smtp.office365.com:587` for M365), SMTP AUTH or an app password / shared mailbox. Modern alternative: Microsoft Graph API via an app registration in the M365 admin portal | Pipeline still generates everything; emails stay manual in Outlook |
| 2 | **Canvas admin API token** — auto-run Canvas SIS Import | The Canvas LMS administrator | Admin → Settings → Integrations/API → "New Access Token". Scope it to SIS Import only (tokens can be limited and revoked) | Keep the ZIP + manual SIS upload (works today) |
| 3 | **Google Workspace admin access** — service account for the Directory API (auto-provision accounts) | Google Workspace super-admin | `admin.google.com` → Security → API controls → domain-wide delegation; create the service account in Google Cloud Console and enable the Admin SDK Directory API | Keep the CSV + manual Google upload (works today) |
| 4 | **Server to host the weekly scheduler** — always-on machine with cron / Task Scheduler | IT infrastructure / whoever hosts NCAD servers | Ask the current process owner: is there an always-on Windows/Linux server available? (NCAD already runs `idp.ncad.ie` and the current infrastructure, so it exists). Needs: always-on, scheduled tasks, outbound access to SFTP/API endpoints | Run on an IT workstation with Task Scheduler — works, less robust |
| 5 | **Library + Triangle SFTP credentials** — auto-upload output files (currently uploaded with an SFTP client) | The current process owner | Ask for host/username/port/key. Check the IT password manager or the existing SFTP connection profiles. Also get the Triangle Service Desk contact email for the confirmation step | SFTP stays manual; auto-email still possible once SMTP exists (#1) |
| 6 | **Credential ownership after handover** — who manages secrets long-term | Manager + IT | Decide a home: IT password manager or a shared secrets store on the scheduler server — **never in the repo** | None — this one must be answered |
| 7 | **OpenAthens API** — auto bulk upload of the Athens template | The OpenAthens admin login holder | Check the OpenAthens admin console for "API access" (Jisc/OpenAthens support confirms whether NCAD's subscription includes it) | Keep CSV + manual upload (works today) |
| 8 | **Quercus export delivery** — the one step with no API | The Quercus admin (Ellucian side) | Ask: do saved exports / scheduled report delivery exist inside Quercus admin? If yes, it can land in the drop-folder automatically | 5-minute manual export into the drop-folder — the scheduler detects the file and does everything else |

**How to fill it in:** for each row, write the answer next to it and mark
Done / Blocked / Deferred. The roadmap phases are ordered so that Blocked
items simply wait — nothing else stops.

---

## 8. Summary for the Manager

- **Already achieved:** the entire generation layer is automated and
  regression-tested (Quercus processing, new-student detection for all 5
  systems, file generation, error handling, documentation).
- **Achievable next:** a weekly scheduler on a private server that takes a
  Quercus export from a drop-folder, runs the whole pipeline, generates
  everything, and logs every run — with a dry-run + approval gate.
- **Only one manual step remains by necessity:** the Quercus export itself
  (Ellucian provides no API). Five minutes a month.
- **Push integrations arrive one by one** as IT provides credentials —
  each one eliminates a manual upload and nothing breaks in between.
- **Two decisions needed from the manager:** (1) approve PII storage on a
  private server (GDPR), (2) assign a credential owner for the long term.
