import re
from datetime import datetime
import pandas as pd
from app.utils.passcode_generator import generate_passcode

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

def normalize_email_identity(df: pd.DataFrame) -> pd.Series:
    """
    Stateless utility function to normalize the identity email address series early.
    Raises KeyError if neither 'Email_address' nor 'Term Email' is found.
    """
    if "Email_address" in df.columns:
        email_col = "Email_address"
    elif "Term Email" in df.columns:
        email_col = "Term Email"
    else:
        raise KeyError("Identity email column ('Email_address' or 'Term Email') not found in DataFrame.")
    return df[email_col].fillna("").astype(str).str.strip().str.lower()

def normalize_baseline_schema(baseline_df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures baseline schema conforms exactly to expected LDAP columns.
    Happens once at the ingestion stage.
    """
    if baseline_df.empty:
        return pd.DataFrame(columns=LDAP_SCHEMA_REQUIRED_COLUMNS)

    df_norm = baseline_df.copy()

    # # Step 1: Normalize incoming column names (strip whitespace + case-insensitive rename)
    expected_lookup = {col.lower(): col for col in LDAP_SCHEMA_REQUIRED_COLUMNS}
    rename_map = {}
    for col in df_norm.columns:
        stripped = col.strip()
        key = stripped.lower()
        if key in expected_lookup and stripped != expected_lookup[key]:
            rename_map[col] = expected_lookup[key]
    df_norm = df_norm.rename(columns=rename_map)
    # Rename is fully complete before schema enforcement begins

    # Step 2: Fill any truly missing columns with empty strings
    for col in LDAP_SCHEMA_REQUIRED_COLUMNS:
        if col not in df_norm.columns:
            df_norm[col] = ""
    return df_norm[LDAP_SCHEMA_REQUIRED_COLUMNS]

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

def normalize_emails(df: pd.DataFrame, email_col: str) -> pd.Series:
    """
    Maintained for API backwards compatibility.
    Raises KeyError if email_col is missing.
    """
    if email_col not in df.columns:
        raise KeyError(f"Email column '{email_col}' not found in DataFrame.")
    return normalize_email_identity(df)

def detect_new_students(baseline_df: pd.DataFrame, quercus_mapped_df: pd.DataFrame) -> pd.DataFrame:
    """
    Identity diff concern: Identifies new students from Quercus data by comparing
    against the baseline dataset. Done BEFORE any deduplication.
    
    INLINE DOCUMENTATION:
    - Email_address is the only identity key:
      This is the canonical identity key across both baseline and new student systems
      to determine if a student already has an LDAP account.
    - Comparison is state-based, not overwrite-based:
      We compare the incoming data against the historical snapshot to identify records
      that do not exist in the current baseline.
    - Deduplication happens after diff detection:
      Running deduplication before diff detection could mask new student entries or lead
      to state loss. By diffing first, we ensure we evaluate all incoming records.
    """
    baseline_emails = set(normalize_email_identity(baseline_df))
    quercus_emails = normalize_email_identity(quercus_mapped_df)

    new_mask = (
        (quercus_emails != "") &
        (quercus_emails != "nan") &
        (~quercus_emails.isin(baseline_emails))
    )

    return quercus_mapped_df[new_mask].copy()

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

def update_baseline_state(baseline_df: pd.DataFrame, new_students_df: pd.DataFrame) -> pd.DataFrame:
    """
    Baseline update concern: Merges baseline and new students, applying deduplication
    ONLY in this stage to form the updated baseline state.
    
    INLINE DOCUMENTATION:
    - Baseline-first ordering matters:
      Placing baseline_df first and new_students_df second guarantees that drop_duplicates
      (with keep="first") always preserves the historical state of existing accounts
      (including their original passcodes and details) rather than overwriting them.
    """
    # Append new student rows under baseline
    combined = pd.concat([baseline_df, new_students_df], ignore_index=True)

    # Clean emails temporarily for deduplication
    combined["_email_clean"] = normalize_email_identity(combined)
    combined = combined[(combined["_email_clean"] != "") & (combined["_email_clean"] != "nan")]

    # Duplication logic is centralized to preserve state integrity.
    # Deduplication happens ONLY here in this state management stage
    combined = combined.drop_duplicates(subset=["_email_clean"], keep="first")
    combined = combined.drop(columns=["_email_clean"])

    return combined

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
    baseline_normalized = normalize_baseline_schema(baseline_df)

    # 2. Validate Schema Contracts (after normalization so case/whitespace differences are already resolved)
    if not baseline_normalized.empty:
        missing_ldap = [col for col in LDAP_SCHEMA_REQUIRED_COLUMNS if col not in baseline_normalized.columns]
        if missing_ldap:
            raise KeyError(f"Required LDAP baseline columns missing: {missing_ldap}")

    # 3. Map Quercus to LDAP format (Pure Mapping, raises KeyError if columns are missing)
    quercus_mapped = map_quercus_to_ldap(quercus_df)

    # 4. Detect new students (BEFORE deduplication)
    new_students_raw = detect_new_students(baseline_normalized, quercus_mapped)

    # 5. Assign passcodes to new students (stateless utility call)
    new_students_with_passcodes = assign_passcodes(new_students_raw)

    # 6. Update baseline state (this is the single stage where deduplication occurs)
    updated_baseline = update_baseline_state(baseline_normalized, new_students_with_passcodes)

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
