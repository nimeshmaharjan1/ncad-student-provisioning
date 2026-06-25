# System Design and MVP Architecture (Phase 0)

## System Overview
This system automates NCAD student provisioning across multiple platforms by transforming a single Quercus export into system-specific output files.

The system replaces manual Excel-based processing with a structured data pipeline.

---

## Architecture Decision
The system is built using:

- Frontend: Next.js (user upload and file download interface)
- Backend: FastAPI (Python processing engine)
- Data Processing: pandas (ETL transformations)

---

## Processing Model
All student data is converted into a canonical internal format before being transformed into system-specific outputs.

Flow:

Quercus CSV → Canonical Student Dataset → System Outputs (LDAP, Canvas, Google, Library, OpenAthens)

---

## Data Ingestion Approach (MVP)
For the initial prototype:
- Quercus CSV structure is assumed fixed
- Column mapping is hardcoded in backend
- No dynamic schema detection is used

This approach is chosen for simplicity and rapid development.

---

## System Outputs
The system generates the following outputs:

- LDAP import file (account creation + credentials)
- Canvas SIS import file (student enrollment)
- Google Workspace provisioning file (accounts + groups)
- Library system upload file (borrower + course classification)
- OpenAthens bulk upload file (access provisioning)

---

## Design Rationale
A canonical data model is used to ensure:
- consistency across all systems
- reduced duplication of logic
- easier long-term maintenance
- clear separation between raw input and system outputs

---

## Future Improvements (Out of Scope for MVP)
- Dynamic column mapping for Quercus exports
- Database-backed audit trail of uploads
- Validation dashboard for error handling
- Automated integration with institutional APIs