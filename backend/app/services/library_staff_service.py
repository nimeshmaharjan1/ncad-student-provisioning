"""
Library Staff export — one OCLC/Sierra-ready row per staff member typed in.

Each staff member is entered by name, library card number (barcode), an
optional gender, and their own registration (+ optional expiration) dates.
The output reuses the same 46-column library schema as the student pipeline
(app/services/library_service.py) with staff-specific values:

    givenName           = first word of the name
    familyName          = everything after the first word
    gender              = typed in, or UNKNOWN when left blank
    institutionId       = 46722 (fixed, same as student rows)
    barcode             = the typed-in library card number
    idAtSource          = login (surname(s) + first initial, e.g. "delaneybyrnec")
    sourceSystem        = https://idp.ncad.ie/idp/shibboleth
    borrowerCategory    = FTS (fixed for staff)
    circRegistrationDate = this person's registration date (YYYY-MM-DD)
    oclcExpirationDate  = this person's expiration date, if set
    homeBranch          = 266006 (fixed, same as student rows)
    emailAddress        = login@staff.ncad.ie

A single-word name (no last name) or a missing barcode is accepted with a
warning just like the Canvas staff tool. A missing registration date is also
accepted with a warning (the date column is left blank), so the row can be
finished in OCLC/Sierra manually — the warning tells the user what to complete
before upload.
"""

from datetime import datetime

import pandas as pd

from app.services.canvas_staff_service import parse_name, staff_login
from app.services.library_service import LIBRARY_OUTPUT_COLUMNS

STAFF_EMAIL_DOMAIN = "staff.ncad.ie"
INSTITUTION_ID = "46722"
SOURCE_SYSTEM = "https://idp.ncad.ie/idp/shibboleth"
BORROWER_CATEGORY = "FTS"
HOME_BRANCH = "266006"

_DATE_FORMAT = "%Y-%m-%d"


def _validate_date(value: str, label: str) -> str:
    """Validate a date in YYYY-MM-DD form. Empty values become ''."""
    stripped = value.strip()
    if not stripped:
        return ""
    try:
        datetime.strptime(stripped, _DATE_FORMAT)
    except ValueError:
        raise ValueError(f"{label} must be in YYYY-MM-DD format; got '{stripped}'.")
    return stripped


def build_library_staff_rows(
    people: list[tuple[str, str, str, str, str]],
) -> tuple[pd.DataFrame, list[str]]:
    """Build the library staff DataFrame from (name, barcode, gender,
    registration_date, expiration_date) tuples.

    Returns (rows, warnings). Blank names are skipped. Blank barcodes,
    single-word names and missing registration dates each add a warning.
    Dates must be YYYY-MM-DD; an expiration date is optional.
    """
    rows = []
    warnings = []
    for name, barcode, gender, registration_str, expiration_str in people:
        stripped = name.strip()
        if not stripped:
            continue
        first, last = parse_name(stripped)
        if not last:
            warnings.append(
                f"'{stripped}' has no last name — the row was generated with a "
                "blank last name. Enter a full name where possible, as the library "
                "import expects first and last names."
            )
        if not barcode.strip():
            warnings.append(
                f"'{stripped}' has no library card number — the barcode column "
                "is blank. Enter the card number for the SFTP upload."
            )
        registration = _validate_date(registration_str, "Registration date")
        if not registration:
            warnings.append(
                f"'{stripped}' has no registration date — circRegistrationDate "
                "is blank. Add the registration date for the SFTP upload."
            )
        expiration = _validate_date(expiration_str, "Expiration date")
        login = staff_login(first, last)
        email = f"{login}@{STAFF_EMAIL_DOMAIN}"
        row = {column: "" for column in LIBRARY_OUTPUT_COLUMNS}
        row.update(
            {
                "givenName": first,
                "familyName": last,
                "gender": gender.strip() or "UNKNOWN",
                "institutionId": INSTITUTION_ID,
                "barcode": barcode.strip(),
                "idAtSource": login,
                "sourceSystem": SOURCE_SYSTEM,
                "borrowerCategory": BORROWER_CATEGORY,
                "circRegistrationDate": registration,
                "oclcExpirationDate": expiration,
                "homeBranch": HOME_BRANCH,
                "emailAddress": email,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows, columns=LIBRARY_OUTPUT_COLUMNS), warnings