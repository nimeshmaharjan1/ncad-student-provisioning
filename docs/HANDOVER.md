# Handover Brief — NCAD Student Provisioning System (Caveats & Rationale)

> Prepared for the manager handover (August 2026). Focuses on the **why** —
> the underlying caveats, where data lives, and why the public demo is safe.
> For "how to operate": `USER_GUIDE.md`. For the manual fallback:
> `MANUAL_PROCESS.md`. For the manager-facing vision: `AUTOMATION_ROADMAP.md`.

---

## 0. The mental model (one paragraph)

The system automates the **generation layer** of student provisioning across
LDAP, Canvas, Google Workspace, OpenAthens, and Library from Quercus exports.
It is a **stateless, transient-processing tool**: you upload files, it
transforms them in memory, you download the results, and everything is
discarded. There is **no database and no server-side storage of student data**.
That single invariant is what makes the public demo acceptable.

---

## 0.5 Deployment & operating model (internal tool)

This system is an **in-house tool for the NCAD IT team**, not a public
product. It is designed to run on **NCAD equipment**, with the public
Vercel/Render deployments serving only as validation and demo environments.
The team's preferred way of working is **script-driven / command-line**
operation — deterministic, repeatable, and easy to audit; the web interface
is an alternative front-end to the same pipeline, not a requirement.

Two consequences worth knowing:

- **Local-first:** the weekly flow runs on NCAD machines, so all data
  (baselines, exports) stays on NCAD equipment — the strongest form of the
  "no external storage" boundary. The public-hosting risks later in this
  document apply to the demo environments only, not to local operation.
- **Script-friendly:** the pipeline logic is fully callable from Python
  scripts (the service layer), so batch generation can be driven from the
  command line without the web server. The pipeline is currently exposed
  through the HTTP API; a dedicated CLI wrapper would be a small follow-up
  if the team wants it.

---

## 1. LDAP passcodes — where they live, why it's OK

**Format:** `WordWordWordWordWordNN` (5 title-cased words + 2-digit number),
e.g. `RiverForestCrystalStormFalcon42`. ~57 bits of entropy (1,668⁵ × 90).

**Why word-based:** LDAP has **no password-change feature** — passcodes are
**permanent** for the whole enrollment. They must be memorable enough not to
be written on a sticky note, but strong enough to resist offline cracking.
5 words not 4 (26 bits too weak), 5 not 6+ (typing errors), 2-digit not
1-digit, no separator/special characters (deliberate). All tradeoffs are
documented in `passcode_generator.py`.

**Deployment asset, not repo asset:** the 1,668-word list (`words.txt`) is
**gitignored** — it travels out-of-band, like the baselines. On any new
machine (manager's laptop, successor's), copy it to `backend/app/utils/words.txt`
or set `PASSCODE_WORD_FILE` to its absolute path (exact commands in
`ONBOARDING.md`). The launcher now **hard-stops** on a fresh machine if the
file is missing — it asks whether you have it, then prints these instructions —
so the weak 15-word fallback (~23 bits) never runs silently. Only
`PROVISION_REQUIRE_WORDS=0` opts into it (demo machines only). Transfer
channel is flexible: any NCAD route that delivers the intact file (shared
drive, USB, Teams, SFTP) — integrity matters, secrecy does not.

**Where they are stored — not on the server.** Verified by code inspection:
the only disk writes in the backend are `settings.json` (validation modes,
no PII) and *reading* `words.txt`. Passcodes are generated in-memory during a
request, put in the ZIP response, then discarded. They persist in exactly two
**client-side** places:
- the downloaded `new_students.csv`, and
- the **baseline CSV** (`updated_baseline.csv`) that the operator saves and
  re-uploads each week.

**Why that's acceptable:** it is the same place the manual process always kept
them (the LDAP file goes to Triangle with passcodes; passcodes are emailed to
students). The automation adds **no new long-term storage**. The real security
boundary is the operator's baseline files (access control on NCAD machines)
plus the gitignore rules that keep them out of the repo.

**Assignment logic:** `assign_passcodes` only fills **blank** passcodes —
existing ones are preserved, so re-running never regenerates a student's
passcode.

**Honest caveats:** uses `random`, not `secrets` (fine for offline batch; must
change if generation ever becomes on-the-fly — noted in code). 57 bits
protects against *guessing*, **not** phishing, keyloggers, or theft of the
baseline file. A permanent, non-rotating credential is a policy tradeoff
forced by LDAP.

---

## 2. Why the site can be left public (three verified layers)

1. **Transient processing invariant** — no database, no disk persistence of
   student data (grep confirms only `settings.json` writes). Data lives only
   during a request.
2. **No PII in logs** — every logger call logs column names, missing-column
   lists, counts, or exception messages. Never names, emails, or passcodes.
3. **No secrets or real data in the repo** — `words.txt`, `settings.json`,
   and all data CSVs are gitignored; only fictional examples are committed.
   Passcode security does not rely on the word list being secret
   (Kerckhoffs's principle).

---

## 3. The honest risks (be ready to explain these)

> These all apply to the **public demo environments**. In the intended
> local-first operating model they largely disappear — no public endpoint,
> no cold starts, no stale remote build — leaving only the data-handling
> items (baseline hygiene, card numbers, retention).

- **The backend is unauthenticated and internet-open.** The WAF allowlist
  guards only the Vercel **frontend**; the `onrender.com` backend accepts
  POSTs from anyone. No persistence → no data theft, but it is an open
  compute endpoint (abuse / free-tier resource use). No CORS config means
  browser cross-origin calls are blocked, but curl/scripts are not.
- **PII still exists in plaintext in transit and on the operator's machine**
  (baselines + downloads). "No server-side storage" is true, but it does not
  make the data disappear — the GDPR boundary is operator-side handling. Real
  automation (server-side baselines, a scheduler) would require a DPIA,
  encryption-at-rest, and a retention policy (see AUTOMATION_ROADMAP.md).
- **Garbage-in, garbage-out on baselines.** The app trusts whatever baseline
  and Quercus files are uploaded (schema-checked, but not content-validated).
- **`Card`/barcode is blank for new students** in the automated LDAP output
  (mapping sets `Card = ""`; only existing records carry theirs). New-student
  barcodes still need manual / Triangle handling.
- **Render runs stale code.** Render was not auto-deploying (a failed build
  pauses auto-deploy); the deployed backend was an older build. Deploy the
  latest commit manually from the Render dashboard before any demo.
- **Free tier sleeps** → ~30s cold start on the first request after idle.

---

## 4. The DOB / GDPR situation (recent change — know this cold)

- The Quercus Discoverer report **no longer exports `Date of Birth`** (GDPR),
  and the LDAP admin agreed (email from John O Donnell, 13 Aug 2026) the
  column stays **in the file but empty**.
- The system **auto-adds the DOB column with empty values** and proceeds —
  DOB **never blocks**, even in Block mode (`NON_BLOCKING_REQUIRED_COLUMNS` in
  `quercus_schema.py`). A DOB column present with empty cells never blocks
  either.
- Per-system **Warn/Block** modes on `/settings`: Warn = auto-add blank +
  amber banner; Block = structured 422 for other missing columns. Env var
  `VALIDATION_MODE_<SYSTEM>` overrides; `settings.json` is per-deployment and
  resets on redeploy.

---

## 5. Quick reference

- **Identity key for all diffs = email** (Term Email / Email_address).
  Baselines are immutable snapshots; inputs are never mutated.
- **What's still manual (transport layer):** Quercus export button, SFTP
  uploads (Cyberduck), Canvas SIS import + FileSender, Google Admin upload,
  Athens/Library delivery, passcode emails.
- **Tests:** from `backend/` with the venv —
  `python samples/test_pipelines.py` (full pipeline) and
  `python samples/test_settings.py` (26 assertions).
- **People:** John O Donnell (LDAP admin/manager), Rene (Canvas),
  Triangle Service Desk (LDAP SFTP + account confirmation).