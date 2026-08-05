"""
Canvas Staff export — one Canvas-ready row per staff name typed in.

Given a full name ("Cian Delaney Byrne"), derive the Canvas SIS columns:

    first_name  = first word            -> "Cian"
    last_name   = everything after      -> "Delaney Byrne"
    login_id    = surname(s) + first initial, letters only, lowercase
                                        -> "delaneybyrnec"
    email       = login + "@staff.ncad.ie"
    user_id     = login
    full_name   = name as typed
    sortable_name = "Delaney Byrne, Cian"

A single-word name (no last name) is accepted with a warning: the row is
generated with a blank last name and login = first name lowercased (e.g.
"Cian" -> "cian@staff.ncad.ie"). The warning is returned alongside the rows
so the UI can flag it — Canvas imports expect first and last names.

The output schema is the same 11-column Canvas baseline schema used by the
student pipeline (app/services/canvas_service.py).
"""

import re
import pandas as pd
from app.services.canvas_service import CANVAS_BASELINE_COLUMNS

STAFF_EMAIL_DOMAIN = "staff.ncad.ie"


def parse_name(name: str) -> tuple[str, str]:
    """Split a full name into (first_name, last_name).

    Whitespace is collapsed and trimmed first. The first word is the first
    name; everything after it is the last name. A single word yields an empty
    last name (handled with a warning by build_canvas_staff_rows).
    """
    stripped = name.strip()
    if not stripped:
        raise ValueError("Staff name cannot be empty.")
    parts = re.sub(r"\s+", " ", stripped).split(" ")
    return parts[0], " ".join(parts[1:])


def staff_login(first_name: str, last_name: str) -> str:
    """login = surname(s) concatenated + first initial, letters only, lowercase.

    "Cian Delaney Byrne" -> "delaneybyrnec"; "Roisin Quigley" -> "quigleyr".
    With no last name the first name alone is used: "Cian" -> "cian".
    """
    if last_name:
        login = re.sub(r"[^a-z]", "", (last_name + first_name[0]).lower())
    else:
        login = re.sub(r"[^a-z]", "", first_name.lower())
    if not login:
        raise ValueError("Staff name must contain at least one letter.")
    return login


def build_canvas_staff_rows(names: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """Build the Canvas staff DataFrame from a list of full names.

    Returns (rows, warnings). Blank lines are skipped. Single-word names are
    accepted with a warning (the row has a blank last name).
    """
    rows = []
    warnings = []
    for name in names:
        stripped = name.strip()
        if not stripped:
            continue
        first, last = parse_name(stripped)
        if not last:
            warnings.append(
                f"'{stripped}' has no last name — the row was generated with a "
                "blank last name. Enter a full name where possible, as Canvas "
                "imports expect first and last names."
            )
        login = staff_login(first, last)
        email = f"{login}@{STAFF_EMAIL_DOMAIN}"
        rows.append(
            {
                "user_id": login,
                "integration_id": "",
                "login_id": email,
                "password": "",
                "first_name": first,
                "last_name": last,
                "full_name": stripped,
                "sortable_name": f"{last}, {first}" if last else first,
                "short_name": "",
                "email": email,
                "status": "active",
            }
        )
    return pd.DataFrame(rows, columns=CANVAS_BASELINE_COLUMNS), warnings