"""
Library Staff export — one OCLC/Sierra-ready row per staff member typed in.

Each staff member is entered by name, library card number (barcode) and an
optional gender. The output reuses the same 46-column library schema as the
student pipeline (app/services/library_service.py) with staff-specific values:

    givenName           = first word of the name
    familyName          = everything after the first word
    gender              = typed in, or UNKNOWN when left blank
    institutionId       = 46722 (fixed, same as student rows)
    barcode             = the typed-in library card number
    idAtSource          = login (surname(s) + first initial, e.g. "delaneybyrnec")
    sourceSystem        = https://idp.ncad.ie/idp/shibboleth
    borrowerCategory    = FTS (fixed for staff)
    circRegistrationDate = user-selected date (required, YYYY-MM-DD)
    oclcExpirationDate  = user-selected date (optional, blank if unset)
    homeBranch          = 266006 (fixed, same as student rows)
    emailAddress        = login@staff.ncad.ie

A single-word name (no last name) is accepted with a warning just like the
Canvas staff tool. A missing barcode is also accepted with a warning, so the
row can be finished in OCLC/Sierra manually — but the warning tells the user
the barcode must be completed before upload.
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


def _validate_date(value: str, label: str, *, required: bool = False) -> str:
    """Validate a date in YYYY-MM-DD form. Empty values become '' unless required."""
    stripped = value.strip()
    if not stripped:
        if required:
            raise ValueError(f"{label} is required (format YYYY-MM-DD).")
        return ""
    try:
        datetime.strptime(stripped, _DATE_FORMAT)
    except ValueError:
        raise ValueError(f"{label} must be in YYYY-MM-DD format; got '{stripped}'.")
    return stripped


def build_library_staff_rows(
    people: list[tuple[str, str, str]],
    registration_date: str,
    expiration_date: str = "",
) -> tuple[pd.DataFrame, list[str]]:
    """Build the library staff DataFrame from (name, barcode, gender) triples.

    Returns (rows, warnings). Blank names are skipped; blank barcodes and
    single-word names each add a warning. Dates must be YYYY-MM-DD, with the
    registration date required and the expiration date optional.
    """
    registration = _validate_date(registration_date, "Registration date", required=True)
    expiration = _validate_date(expiration_date, "Expiration date")

    rows = []
    warnings = []
    for name, barcode, gender in people:
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