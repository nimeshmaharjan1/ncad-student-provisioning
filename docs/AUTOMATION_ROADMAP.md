# Automation Roadmap — From Manual to Zero-Touch Provisioning

> Project document for the NCAD Student Provisioning system.
> Audience: the department head (manager), the current process owner (IT
> support), and any future developer or IT support person who inherits this
> project.

This document is the single source of truth for **where we are**, **where the
manager wants us to go**, **what stops us**, and **what we do instead**.
Nothing here is final — it is a living plan to be reviewed with the manager and
the current process owner.

---

## How to Read This Document — Every Technical Word, Explained

This document uses some technical words because the systems behind them are
technical. Nothing here requires you to understand how they work — only what
they mean well enough to make decisions. Read this section first; when you see
a word you forgot, come back here.

| Word you'll see | What it means, in plain English |
|----------------|--------------------------------|
| **Passcode** | A temporary password for a new student account (e.g. their Google Workspace password). Like a PIN: if it leaks, someone could log in as that student, which is why this document treats passcodes carefully |
| **PII** (personally identifiable information) | Student details that identify a real person: name, date of birth, email address, phone number, passcode. The law treats this data more strictly than ordinary data, so the document is careful about where it is stored and how long it is kept |
| **Baseline** | The saved list of students who are already in a system (LDAP, Canvas, Google, OpenAthens). The system compares each week's Quercus list against the baseline to find out who is new |
| **Diff** (comparison) | The act of comparing two lists to see what changed — in our case: which students are new and which accounts were suspended |
| **SFTP** | A secure way to copy files over the internet to another organisation's computer (e.g. the Library's or Triangle's). It is the same kind of thing you already do with Cyberduck, just done by the scheduler itself |
| **SMTP** | The technical name for "sending an email from a computer program". Thunderbird uses it behind the scenes; the scheduler needs its own set of sending details (the same details you use in Outlook) |
| **API** | A standard door that software uses to talk to another system. "Quercus has no API" means there is no door: the only way to get data out of it is the website's export button, which needs a person |
| **Admin token** / **service account** | A secret key that an administrator of an outside system (e.g. Canvas or Google) creates so that our program alone may use that system's door. It can be limited and revoked at any time |
| **Scheduler** (cron / Windows Task Scheduler) | An alarm clock built into the server: "every Monday at 9 a.m., run the provisioning pipeline". The alarm clock fires, the pipeline runs, nobody has to be there |
| **Drop-folder** | A special folder on the server that the system watches. You (or the Quercus export, if it can be scheduled) put the exported file in it; the system notices the new file and does everything else by itself |
| **Always-on private server** | A quiet computer, owned by NCAD, that stays switched on and is only reachable by NCAD staff. Unlike the public demo deployments (Vercel / Render) — free-tier services that switch themselves off when unused ("instances sleep") and are visible to anyone on the internet |
| **Dry-run** | A practice run: the system generates everything exactly as it would for a real week — files, emails, logs — but sends nothing. A person reviews the practice output, then clicks "send for real" |
| **Approval gate** / **click-to-confirm** / **human-in-the-loop** | A small review screen: the system prepares everything and then stops, waiting for a person to click "yes" before anything is sent. Used only for the few steps that need a human decision |
| **Encryption (at rest)** | Storing student data and passwords in scrambled form on the server's disk. Even if the disk were stolen, the data would be unreadable without the secret key |
| **Retention policy** | A rule the manager sets: how long student data may be kept, who may see it, and when it is deleted |
| **GDPR / DPIA** | GDPR is the European data-protection law. A DPIA is the formal written check of "is storing this student data allowed, and under what rules?" — a management decision, not a programming one |
| **Run log** | The system's diary of each weekly run: run number, which step, counts, and any errors. It deliberately never contains student names or passwords |
| **UI-robot** (Puppeteer / Playwright) | A program that imitates a person clicking through a website. Rejected for Quercus because websites change frequently and the robot would break silently without anyone noticing |
| **Push integration / connector** | The piece of the scheduler that delivers our generated files to one outside system (Library, Triangle, Canvas, Google, OpenAthens). Each one becomes possible when that organisation gives us access credentials |
| **Ellucian** | The company that makes Quercus. "Quercus has no API" comes from them: they do not offer a door for automatic data extraction |

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
provisioning pipeline once per week automatically. A drop-folder (see
glossary) is simply a watched inbox: the moment the Quercus export file is
put in it, the rest of the run happens by itself.

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
| 2 | **GDPR posture flips**. Automation requires storing student PII server-side (baselines, run logs). The current app explicitly promises transient processing | Storing student names/details (PII — see glossary) on a server is a data-protection decision (GDPR, DPIA — see glossary), not a code decision | Documented decision required from the manager: secure storage, access control, encryption, retention policy (all in the glossary). The public demo stays transient; the scheduler runs on a private server only |
| 3 | **Triangle Service Desk is a human gate**. Their confirmation is their business process | The confirmation step cannot be auto-approved | Auto-SFTP the LDAP files + auto-email the Service Desk, then **wait for a click-to-confirm** (see glossary: a review screen where a person clicks "yes") — human decision for this one step only |
| 4 | **APIs/credentials may not exist yet**: Canvas admin token, Google service account, OpenAthens API, SMTP details | Each push integration needs an administrator to create/issue credentials | Ship integrations **per system, in order of credential availability** (Credentials & Access Checklist, section 7). No credential → that step stays manual |
| 5 | **Hosting reality**. The Vercel + Render deployments are public demo environments — free-tier and ephemeral (instances sleep — see glossary: free hosting switches itself off when unused). They are not NCAD's production hosting and are not suitable for the scheduler | Not suitable as a scheduler host; also public by design | Dedicated always-on private server for the scheduler (Checklist #4). Demo deployments stay as they are — harmless and useful for demos, and can be taken down once the private server is running |
| 6 | **Passcodes are sensitive**. Emails carry generated credentials | Automated emails carrying student passwords need rules (who may receive them, how they are protected) — a policy decision, not just a technical one. It matters more now because automation sends them in bulk, every week | We **already** send passcodes by email today (Thunderbird mail merge) — automation keeps that practice, it does not invent a new one. The manager signs off **ONCE** per email type, e.g. "student passwords may be emailed from the automated system, to the student's personal address". After that single decision, the weekly emails send themselves — there is **no per-email approval step**. Passwords are stored scrambled (encrypted at rest) and never appear in run logs (logs record only run numbers, counts, and statuses) |
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
- Student passcode emails (one-time manager sign-off per email type — see
  Harsh Reality #6)
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

### In one paragraph

The hard work is done: the system already takes Quercus student data and
generates everything needed for LDAP, Canvas, Google Workspace, OpenAthens,
and the Library — automatically, with errors caught instead of silently
skipped. The plan is to add a weekly "clock" on a private NCAD server that
runs that same pipeline by itself: a file dropped into a watched folder, and
everything after it happens automatically — with a practice-run mode and a
review screen so nothing is ever sent without a person's say-so. Only one
manual step genuinely cannot be automated (the Quercus export itself, about
five minutes a month), and the automatic uploads to each system switch on one
by one, as IT provides access. Three decisions are needed from the manager —
the storage of student data, the automated passcode emails, and who owns the
access keys long-term — and each is explained below in plain English.

### The longer version — for the reader

**What the system already does.** Today, when a Quercus export arrives, the
system cleans the data (removes withdrawn students, duplicates, and external
students), compares it against the saved baselines of all five systems, and
works out exactly who is new. For each system it generates the correct file —
LDAP files with word passcodes, the Canvas import, Google uploads with
account reactivation, the OpenAthens template, and Library borrower records.
Errors are no longer silent: if a file is missing a required column, the
system either blocks with a clear message or warns the user in advance. All
of this is already automated and regression-tested — it works today.

**What the manager asked for.** The vision: the system should pull student
data from Quercus, check for new students, add them to all five systems by
itself, send the emails, and keep logs — running automatically every week,
with no human in the loop.

**The honest picture.** Almost all of that vision is achievable, with two
realistic corrections. First, Quercus itself has no door for software to
reach in (no API — see glossary): the export must be downloaded from the
website by hand. That is the one step a person will always do — about five
minutes a month. Second, the automatic uploads to each outside system cannot
happen until that system's administrator gives us access credentials. Those
arrive one by one, and each one turns off another manual upload the moment it
arrives. Nothing breaks in between: if a credential never arrives, that step
simply stays manual, exactly as it is today.

**What "the rails" means.** A private, always-on server (the same kind NCAD
already runs) gets an alarm clock (the scheduler): every Monday at a set
time, it watches a drop-folder — a folder you put the Quercus export into.
The moment the file is there, the pipeline runs end to end: intake → clean →
diff → generate → deliver → notify → log. Every run is recorded in a run log
(the diary: run number, step, counts, errors — never student names or
passwords). Everything is generated in **dry-run mode** first — a practice
run where nothing is sent — and a simple review screen shows what was
prepared before a person clicks "send for real". The Triangle Service Desk
confirmation keeps a human step by design: their receipt confirmation is
their business process, so the system waits for a click-to-confirm.

**The three decisions only the manager can make.**

1. **Storing student data on the server.** Automation means student details
   (names, dates of birth, emails — the baselines and run logs) live on a
   server between runs. Under GDPR that is a formal, documented decision,
   not a programming one. The proposal: storage on the private NCAD server
   only, access limited to named staff, data stored scrambled (encrypted at
   rest), and a retention policy — a rule for how long it is kept and when
   it is deleted. The public demo stays as it is: it never stores student
   data.

2. **Passcode emails.** Student passwords are already sent by email today
   (Thunderbird mail merge) — automation keeps that practice. The manager
   signs off once on each email type — for example, "student passwords may
   be emailed from the automated system to the student's personal address".
   After that single decision, the weekly emails send themselves; there is
   no per-email approval. Passwords are stored scrambled and never written
   to the run log.

3. **Credential ownership.** The access keys (Canvas token, Google service
   account, SFTP credentials, SMTP details) will outlive any one person.
   The manager names who owns them long-term and where they are kept
   (an IT password manager or a secure store on the server — never in the
   code repository).

**What could go wrong, and how it is handled.**

| If this happens | How the plan handles it |
|---|---|
| Credentials never arrive | Each step is optional; the manual path stays as it is today — the scheduler simply skips that step |
| Quercus changes its export format | The schema registry (one central list of expected columns) is already built; a changed format is detected with a clear warning instead of silent wrong data |
| A weekly run fails unnoticed | Failure alerts and a weekly summary email to IT (Phase 3); the run log shows every step's status |
| Data-protection concerns | Manager sign-off, retention policy, private server, encryption — the public demo never stores student data |
| The process owner's knowledge is lost | This document, the ONBOARDING and MANUAL_TESTING guides, and a completed Credentials & Access Checklist are the handover |
| "Just automate everything" keeps growing | This roadmap is the agreed scope; any change to it goes through this document |

**The golden rule.** Every integration in this plan is **additive and
reversible**. If a credential is unavailable, the scheduler skips that step
and today's manual path still works. Nothing the automation does can break
what already works by hand — the automation only ever replaces steps the
moment they are ready to be replaced.

---

## 9. What Happens Next — the Coming Weeks and Phases

This section is written for BOTH readers: the manager (decisions and
approvals) and the developer (what to build and verify). Every step says who
does it, what to do, and why it is better than today.

### The next seven days

| # | Who | What to do | Why it is better |
|---|-----|-----------|------------------|
| 1 | Developer | Finish the manual test pass in MANUAL_TESTING.md (happy path, warnings, gated download, Start over, privacy card) | The app is verified end to end before it is shown to anyone |
| 2 | Both | Walk through Section 7 (Credentials & Access Checklist) with the current process owner and the manager | You learn exactly which credentials exist, so the phases reorder themselves around reality |
| 3 | Manager | Make the three decisions in Section 8 (student-data storage, passcode emails, credential owner) | They unlock the automated parts; until then the manual path continues to work |
| 4 | Developer | Ask IT about an always-on server (Checklist #4) | Even a "no" is fine — Phase 1 can be built and proven on a workstation with Task Scheduler first |

### After that — phase by phase

**Phase 1 — The Rails (build first; no credentials needed)**

- Developer: scheduler skeleton (cron / Windows Task Scheduler) on the
  private server — or a workstation to start; drop-folder intake; persistent
  run log; dry-run mode. Reuse the existing backend services unchanged; test
  with the sample files in dry-run mode.
- Manager: nothing to decide in this phase — it only generates and logs;
  nothing is sent.
- Why it is better: this is the visible proof of the vision — the system
  runs itself every week, everything is generated and logged, and nothing
  goes anywhere until a person reviews it.

**Phase 2 — Push integrations (one per credential obtained)**

- Recommended order: Library SFTP first (credentials already exist with the
  current process owner) → Triangle LDAP SFTP + auto-email with
  click-to-confirm → Canvas SIS via API → Google Workspace
  auto-provisioning → OpenAthens (check the subscription includes API
  access).
- Manager / IT: obtain each credential from Section 7 and hand it over.
- Developer: build each connector so it is additive and reversible; test in
  dry-run before any real upload; nothing breaks if a credential never
  arrives.
- Why it is better: every credential switches off one manual upload,
  permanently.

**Phase 3 — Email & notifications**

- Manager: one-time sign-off per email type (Harsh Reality #6).
- Developer: SMTP setup (Checklist #1); passcode emails; failure alerts and
  weekly summary to IT; never log passcodes or student details.
- Why it is better: no more Thunderbird mail merge; a failed run is noticed
  the same day instead of the next month.

**Phase 4 — Human-in-the-loop approval UI**

- Developer: review-and-confirm screen for the Triangle confirmation and the
  final "send emails" trigger.
- Manager: names the person(s) who click "yes" each week.
- Why it is better: automation with a safety rail — the system prepares
  everything, and a person still gives the final go.

**Phase 5 — Never (documented rejection)**

- UI-robots for Quercus (fragile, breaks silently) — see
  AUTOMATION_STRATEGY.md.

### Things the developer can improve along the way (no manager needed)

- GitHub Actions CI: run the pipeline regression tests automatically on
  every push — a change can never silently break the logic again.
- Dependabot (or equivalent): automatic security alerts for the libraries in
  use — free, and better than discovering an outdated dependency later.
- Run-log dashboard: a simple screen to read past runs without digging
  through raw logs.
- More tests: extend the regression suite to cover the scheduler's dry-run
  mode.
- Security hygiene: rotate tokens when staff change; enforce the retention
  policy (auto-delete old logs); keep ONBOARDING and MANUAL_TESTING current.
- Keep the demo deployments current so the newest version is always visible
  at the demo URL.

### For the manager — why the code is on a public personal GitHub, and what stays private

The code lives on the developer's personal GitHub account, publicly. This is
a deliberate and safe arrangement, based on facts that are already true in
this repository:

- **No secrets.** Environment files (`.env`) and the passcode word list are
  excluded from the repository by design (`.gitignore`). The code reads
  exactly one setting from the environment (where the word list lives).
  Access keys and credentials never appear in the code — they live in the IT
  password manager / a secure store on the private server (Checklist #6).
- **No real student data.** The repository ignores all `*.csv` and `*.xlsx`
  files except the sanitized samples folder. Real baselines, real exports
  and run logs never enter the repository. The app itself is transient — it
  has no database and stores nothing between runs.
- **No internal names.** The documentation uses roles ("current process
  owner", "Canvas administrator"), not real staff names.
- **It costs nothing.** GitHub, Vercel and Render free tiers are all
  zero-cost.
- **It buys a lot:** a live demo URL that can be opened at any time; an
  offsite backup with full history; a handover that any future IT person can
  read; and a public example of the developer's work.
- **The license is MIT.** Anyone may use the code, including NCAD, freely,
  with attribution. This does not weaken security: the protection comes from
  the credentials and the private server, not from hiding the code.

What must NEVER go into this repository: real Quercus exports, real
baselines, run logs, and any credential. Those live only on the private
server, in the secure store, under the retention policy.

One honest consideration: the repository sits on a personal account. If the
developer ever leaves, the repository can be transferred to an NCAD
organisation account or forked in minutes — and this document, ONBOARDING.md
and MANUAL_TESTING.md are the handover that make the code understandable to
whoever inherits it.

### Guardrails

Two rules hold the whole plan together. First, everything is **additive and
reversible** — if a credential is unavailable, the scheduler skips that step
and today's manual path still works. Second, the scope is what this document
says: any new idea ("just automate everything") goes through this roadmap
before it becomes work.
