# Automation Strategy

Whether we can automate a task comes down to one thing: does the target system have an API (a machine-friendly door)? If yes, a script can do the work. If no, a human must use the website.

---

## What We Cannot Automate: Quercus Export

Ellucian Quercus does not offer a public API. The only way to get data out is through its web interface — clicking through menus and downloading CSVs by hand.

We could try to automate this with a robot browser script (like Puppeteer or Playwright), but that approach is fragile. Any UI change by Ellucian would break it, and someone would need to maintain it indefinitely. For a task that takes 5 minutes once a month, it is not worth the risk.

**Verdict**: Keep Quercus export manual.

---

## What We Can Automate

| System | Method | What we need |
|---|---|---|
| **Library SFTP upload** | Python SFTP (Paramiko) | SFTP credentials (already have them) |
| **Triangle LDAP SFTP upload + email notification** | Python SFTP + SMTP | SFTP credentials + Triangle Service Desk email |
| **3 email campaigns (Thunderbird replacement)** | SMTP (smtplib, built into Python) | NCAD email SMTP details (host, port, username, password) |
| **Canvas SIS Import** | Canvas REST API | API token from Canvas Admin settings |
| **Google Workspace account creation** | Google Admin SDK Directory API | Google service account with domain-wide delegation |
| **OpenAthens bulk upload** | OpenAthens Management API (needs verification) | API credentials |
| **Notify Rene (after Canvas upload)** | SMTP — same as email system above | Rene's email address |

---

## Phased Rollout

### Phase A — This Month (no new approvals needed)

1. Library SFTP upload button
2. LDAP SFTP upload + auto-email Triangle Service Desk
3. Built-in email sending (replace Thunderbird Mail Merge)

After Phase A, the only manual steps are: download Quercus CSVs (5 min), upload to Google Admin (10 min), upload to Canvas (5 min), upload to OpenAthens (5 min).

### Phase B — Next (needs Canvas Admin token)

4. Canvas SIS Import via API — eliminates the Canvas manual upload
5. Auto-email Rene after successful Canvas upload (reuses SMTP from Phase A)

### Phase C — Later (needs Google Admin access)

6. Google Workspace auto-provisioning — eliminates the Google manual upload

### Phase D — Investigation needed

7. OpenAthens API — need to confirm the endpoint exists and get credentials

### Phase E — Not recommended

8. Quercus export automation — fragile, high maintenance, low value

---

## Summary

The current system generates the right CSV files but leaves all the uploading and emailing to you. Phase A alone would automate the two SFTP uploads and all three email campaigns — eliminating roughly 80% of what you still do by hand.
