"""
Quercus Schema Registry — the single source of truth for Quercus column schemas.

WHY THIS MODULE EXISTS
----------------------
Every downstream system (LDAP, Canvas, Google, OpenAthens, Library) needs
specific columns from a Quercus export. Previously each API endpoint defined
its own copy of the required/optional column lists and its own validation
block, so adding a column or a new system meant editing 5+ files and could
easily drift out of sync.

This registry centralises:
  1. The per-system column lists (``SCHEMAS``).
  2. The two validation modes every endpoint uses:
       - STRICT mode (export endpoints): missing required columns -> 422 error.
       - WARN mode (Quercus upload step): missing source columns -> warning
         only, processing continues. Users are told to recheck their files
         before running downstream exports, but are never blocked.
  3. The structured response shape consumed by the frontend error/warning UI.

HOW TO ADD A NEW SYSTEM (e.g. "Moodle")
---------------------------------------
  1. Add one ``SystemSchema`` entry to ``SCHEMAS`` below, e.g.::

         "moodle": SystemSchema(
             key="moodle",
             display_name="Moodle",
             required=("ID Number", "First Name", "Last Name", "Term Email"),
             optional=(),
         ),

  2. In the new API endpoint, replace inline validation with::

         from app.core.quercus_schema import check_columns, missing_required_response
         check = check_columns("moodle", quercus_df.columns)
         if check["missing_required"]:
             return missing_required_response("moodle", check)

  3. That's it. The Quercus upload warning list is computed automatically
     from the union of all ``required`` lists (see ``SOURCE_WARN_COLUMNS``),
     so the upload step will start warning about missing columns for the new
     system with no further changes.

HOW TO CHANGE EXISTING COLUMNS
------------------------------
Edit the relevant ``SystemSchema`` entry here. Every endpoint reads from this
module, so the change applies everywhere automatically. If you remove a column
from a ``required`` tuple, also check ``EXTRA_SOURCE_WARN_COLUMNS`` below to
decide whether the upload step should still warn about it.
"""

from dataclasses import dataclass

from fastapi.responses import JSONResponse


@dataclass(frozen=True)
class SystemSchema:
    """Column contract for one downstream system.

    ``required`` columns are validated in STRICT mode: if any are missing from
    the uploaded Quercus file, the export endpoint rejects the request with a
    structured 422 response and the frontend shows a rich error card.

    ``optional`` columns never block an export — they are logged and simply
    left blank in the output.
    """

    key: str
    display_name: str
    required: tuple[str, ...]
    optional: tuple[str, ...]


SCHEMAS: dict[str, SystemSchema] = {
    "ldap": SystemSchema(
        key="ldap",
        display_name="LDAP",
        required=(
            "ID Number", "Course Code", "Course Description",
            "Course Instance Course Year", "Type", "First Name",
            "Last Name", "Date of Birth",
            "Term Email", "LDAP ID",
        ),
        # Home Mobile Phone is NOT required — if missing it is left blank.
        optional=("Home Mobile Phone",),
    ),
    "canvas": SystemSchema(
        key="canvas",
        display_name="Canvas",
        required=("ID Number", "First Name", "Last Name", "Term Email"),
        optional=(),
    ),
    "google": SystemSchema(
        key="google",
        display_name="Google Workspace",
        required=("ID Number", "First Name", "Last Name"),
        optional=(),
    ),
    "athens": SystemSchema(
        key="athens",
        display_name="OpenAthens",
        required=("ID Number", "First Name", "Last Name"),
        optional=(),
    ),
    "library": SystemSchema(
        key="library",
        display_name="Library",
        required=("ID Number",),
        optional=(
            "First Name", "Last Name", "Gender", "Course Code",
            "Course Instance Start Date", "Course Instance End Date",
        ),
    ),
}

# Columns that ``preprocess_quercus()`` creates on the fly (Term Email is
# derived from ID Number, Type from Course Code). They must NOT be expected in
# the raw Quercus upload, so they are excluded from the upload warning list.
PREPROCESS_GENERATED_COLUMNS = ("Term Email", "Type")

# Extra columns worth warning about at upload time even though no downstream
# system lists them as strictly required:
#   - Status: preprocess_quercus() filters students by Status (Registered /
#     Recommend*) — if the column is absent the filter is silently skipped and
#     withdrawn students could be exported. Warning is better than silent.
EXTRA_SOURCE_WARN_COLUMNS = ("Status",)

# Required columns that must NEVER reject an export when missing, even in
# strict (Block) mode. The output file still contains the column — it is
# auto-added with empty values and the response carries the X-Missing-Required
# header so the frontend can show exactly what was blanked.
#
# ldap -> Date of Birth: the Quercus Discoverer report no longer exports DOB
# (GDPR, August 2026) and the LDAP admin requires the DOB column to stay in
# the LDAP file with empty values allowed (email from John O Donnell,
# 2026-08-13: "leave the DOB column in place but we can leave it empty of
# data"). A DOB column present with empty cells never blocks either — no
# row-level validation exists.
NON_BLOCKING_REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "ldap": ("Date of Birth",),
}

# Columns the raw Quercus source files are expected to contain. Computed as
# the union of every system's required columns, minus columns that
# preprocessing generates, plus EXTRA_SOURCE_WARN_COLUMNS. Kept in a stable
# order (first-seen) so error messages don't jump around.
_SOURCE_WARN_UNION: tuple[str, ...] = ()
for _schema in SCHEMAS.values():
    for _col in _schema.required:
        if _col not in _SOURCE_WARN_UNION:
            _SOURCE_WARN_UNION += (_col,)

SOURCE_WARN_COLUMNS: tuple[str, ...] = tuple(
    col
    for col in _SOURCE_WARN_UNION
    if col not in PREPROCESS_GENERATED_COLUMNS
) + tuple(col for col in EXTRA_SOURCE_WARN_COLUMNS if col not in _SOURCE_WARN_UNION)


def check_columns(system_key: str, df_columns) -> dict:
    """STRICT-mode check used by export endpoints.

    Returns the same structured shape the frontend error card expects:

        {
            "missing_required": [...],
            "missing_optional": [...],
            "present_columns": [...],
            "all_required": [...],
            "all_optional": [...],
        }

    The endpoint decides what to do with it — normally: if
    ``missing_required`` is non-empty, return ``missing_required_response()``,
    unless ``blocking_missing_required()`` filters it down to the columns that
    actually block (see NON_BLOCKING_REQUIRED_COLUMNS).
    """
    schema = SCHEMAS[system_key]
    cols = {str(c) for c in df_columns}
    return {
        "missing_required": [c for c in schema.required if c not in cols],
        "missing_optional": [c for c in schema.optional if c not in cols],
        "present_columns": sorted(cols),
        "all_required": list(schema.required),
        "all_optional": list(schema.optional),
    }


def blocking_missing_required(system_key: str, check: dict) -> list[str]:
    """Missing required columns that actually block an export in strict mode.

    Columns in NON_BLOCKING_REQUIRED_COLUMNS are excluded: they stay required
    (the output file keeps the column), but a missing one is auto-added as an
    empty column instead of rejecting the export — see the rationale above.
    """
    non_blocking = set(NON_BLOCKING_REQUIRED_COLUMNS.get(system_key, ()))
    return [c for c in check["missing_required"] if c not in non_blocking]


def missing_required_response(system_key: str, check: dict) -> JSONResponse:
    """Builds the structured 422 response for a STRICT-mode failure."""
    schema = SCHEMAS[system_key]
    return JSONResponse(
        status_code=422,
        content={
            "detail": f"Missing required columns: {', '.join(check['missing_required'])}",
            "error_code": "missing_required_columns",
            **check,
        },
        headers={"X-System": schema.display_name},
    )


def check_source_columns(df_columns) -> list[str]:
    """WARN-mode check used by the Quercus upload step.

    Returns the list of expected source columns that are missing from a raw
    Quercus file. Processing is NEVER blocked by this check — the result is
    surfaced as a warning so the user can recheck their export settings
    before running downstream exports.

    Columns in NON_BLOCKING_REQUIRED_COLUMNS (e.g. LDAP's ``Date of Birth``)
    are excluded: they are expected to be absent (the Discoverer report no
    longer exports DOB, GDPR) and are auto-added with empty values downstream,
    so their absence is not something to warn about.
    """
    cols = {str(c) for c in df_columns}
    non_blocking = {c for t in NON_BLOCKING_REQUIRED_COLUMNS.values() for c in t}
    return [col for col in SOURCE_WARN_COLUMNS if col not in cols and col not in non_blocking]
