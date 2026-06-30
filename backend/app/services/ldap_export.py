import re
from datetime import datetime
import pandas as pd
from app.utils.passcode_generator import generate_passcode
from app.utils.df_utils import (
    normalize_email_identity,
    normalize_baseline_schema,
    detect_new_users,
    update_baseline_state,
)

# ==============================================================================
# NCAD LDAP PROVISIONING SYSTEM CONTRACT:
#
# 1. baseline_ldap is an immutable snapshot of current system state.
# 2. quercus_df is a delta input (may contain multiple files merged).
# 3. system output MUST be:
#    - new_students_df (only new identities)
#    - updated_baseline_df (new LDAP snapshot)
#
# 4. NO function is allowed to mutate input DataFrames.
# 5. Identity key is ALWAYS: Email_address (Term Email).
# ==============================================================================

LDAP_EMAIL_PRIORITY = ["Email_address", "Term Email"]

QUERCUS_SCHEMA_REQUIRED_COLUMNS = [
    "ID Number", "Course Code", "Course Description",
    "Course Instance Course Year", "Type", "First Name",
    "Last Name", "Date of Birth", "Home Mobile Phone",
    "Term Email", "LDAP ID"
]

LDAP_SCHEMA_REQUIRED_COLUMNS = [
    "Student ID", "Code", "Description", "Year", "Code (UG/PG/E)",
    "First Name", "Last Name", "Date of Birth", "Phone",
    "Email_address", "Quercus_LDAP", "Card", "Passcode"
]

def map_quercus_to_ldap(quercus_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pure mapping function: Quercus -> LDAP schema only, no business logic.
    Renames Quercus fields to match LDAP schema.
    Raises KeyError if required Quercus columns are missing.
    """
    # Validate Quercus schema first
    missing_quercus = [col for col in QUERCUS_SCHEMA_REQUIRED_COLUMNS if col not in quercus_df.columns]
    if missing_quercus:
        raise KeyError(f"Required Quercus columns missing: {missing_quercus}")

    mapping = {
        "Student ID": "ID Number",
        "Code": "Course Code",
        "Description": "Course Description",
        "Year": "Course Instance Course Year",
        "Code (UG/PG/E)": "Type",
        "First Name": "First Name",
        "Last Name": "Last Name",
        "Date of Birth": "Date of Birth",
        "Phone": "Home Mobile Phone",
        "Email_address": "Term Email",
        "Quercus_LDAP": "LDAP ID"
    }

    ldap_data = {ldap_col: quercus_df[quercus_col].copy() for ldap_col, quercus_col in mapping.items()}
    ldap_data["Card"] = ""
    ldap_data["Passcode"] = ""

    return pd.DataFrame(ldap_data)

def assign_passcodes(new_students_df: pd.DataFrame) -> pd.DataFrame:
    """
    Passcode generation concern: Stateless utility call to generate passcodes
    for new student records. Handles empty/missing passcodes safely.
    """
    df_copy = new_students_df.copy()
    if df_copy.empty:
        return df_copy

    def get_passcode(val):
        if pd.isna(val) or not str(val).strip():
            return generate_passcode()
        return val

    df_copy["Passcode"] = df_copy["Passcode"].apply(get_passcode)
    return df_copy



def _format_dob_series(series: pd.Series) -> pd.Series:
    """
    Converts any Date of Birth format to dd/mm/yyyy.
    Uses explicit strptime per pattern — no pandas date heuristics.
    Two-digit years: > current year → 1900s, ≤ current year → 2000s.
    Handles ISO, Excel serial, and mixed formats.
    Empty/invalid values become empty string.
    """
    str_series = series.fillna("").astype(str)
    current_short = datetime.now().year % 100

    def _parse_dob(val):
        s = val.strip()
        if not s:
            return ""

        # Pattern 1: dd/mm/yy or dd/mm/yyyy
        m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', s)
        if m:
            day, month, year_str = int(m.group(1)), int(m.group(2)), m.group(3)
            if len(year_str) == 2:
                yr = int(year_str)
                year = 1900 + yr if yr > current_short else 2000 + yr
            else:
                year = int(year_str)
            try:
                dt = datetime(year, month, day)
                return dt.strftime("%d/%m/%Y")
            except ValueError:
                return ""

        # Pattern 2: dd-Mon-yy or dd-Mon-yyyy (e.g. 24-Aug-72)
        m = re.match(r'^(\d{1,2})-([A-Za-z]{3})-(\d{2,4})$', s)
        if m:
            day, month_str, year_str = int(m.group(1)), m.group(2), m.group(3)
            if len(year_str) == 2:
                yr = int(year_str)
                year = 1900 + yr if yr > current_short else 2000 + yr
            else:
                year = int(year_str)
            try:
                dt = datetime.strptime(f"{day} {month_str} {year}", "%d %b %Y")
                return dt.strftime("%d/%m/%Y")
            except ValueError:
                return ""

        # Pattern 3: ISO yyyy-mm-dd
        try:
            dt = datetime.strptime(s, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            pass

        return ""

    formatted = str_series.apply(_parse_dob)

    # Fallback: Excel serial dates for values not parsed as text
    if (formatted == "").any():
        numeric = pd.to_numeric(series, errors="coerce")
        excel_dates = pd.to_datetime(numeric, unit="D", origin=pd.Timestamp("1899-12-30"), errors="coerce")
        excel_fmt = excel_dates.dt.strftime("%d/%m/%Y")
        excel_fmt[excel_dates.isna()] = ""
        formatted = formatted.mask(formatted == "", excel_fmt)

    return formatted


def generate_ldap_comparison_exports(baseline_df: pd.DataFrame, quercus_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Orchestrates the LDAP comparison pipeline.
    
    Returns:
        tuple: (new_students_df, updated_baseline_df, audit_info)
    """
    # 1. Normalize Baseline Schema at Ingestion
    baseline_normalized = normalize_baseline_schema(baseline_df, LDAP_SCHEMA_REQUIRED_COLUMNS)

    # 2. Validate Schema Contracts (after normalization so case/whitespace differences are already resolved)
    if not baseline_normalized.empty:
        missing_ldap = [col for col in LDAP_SCHEMA_REQUIRED_COLUMNS if col not in baseline_normalized.columns]
        if missing_ldap:
            raise KeyError(f"Required LDAP baseline columns missing: {missing_ldap}")

    # 3. Map Quercus to LDAP format (Pure Mapping, raises KeyError if columns are missing)
    quercus_mapped = map_quercus_to_ldap(quercus_df)

    # 4. Detect new students (BEFORE deduplication)
    new_students_raw = detect_new_users(baseline_normalized, quercus_mapped, LDAP_EMAIL_PRIORITY)

    # 5. Assign passcodes to new students (stateless utility call)
    new_students_with_passcodes = assign_passcodes(new_students_raw)

    # 6. Update baseline state (this is the single stage where deduplication occurs)
    updated_baseline = update_baseline_state(baseline_normalized, new_students_with_passcodes, LDAP_EMAIL_PRIORITY)

    # 7. Enforce dd/mm/yyyy format on Date of Birth in both outputs
    new_students_with_passcodes["Date of Birth"] = _format_dob_series(new_students_with_passcodes["Date of Birth"])
    updated_baseline["Date of Birth"] = _format_dob_series(updated_baseline["Date of Birth"])

    # 8. Audit info based on inputs
    audit_info = {
        "new_students_count": len(new_students_with_passcodes),
        "updated_baseline_count": len(updated_baseline),
        "filtered_out_status_count": quercus_df.attrs.get("filtered_out_status_count", 0),
        "external_students_removed_count": quercus_df.attrs.get("external_students_removed_count", 0),
        "duplicate_rows_detected": quercus_df.attrs.get("duplicate_rows_detected", 0)
    }

    return new_students_with_passcodes, updated_baseline, audit_info
