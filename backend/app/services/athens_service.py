import pandas as pd
from app.utils.df_utils import (
    normalize_email_identity,
    detect_new_users,
)

ATHENS_EMAIL_PRIORITY = ["attribute/emailAddress", "Term Email"]

ATHENS_UPLOAD_COLUMNS = [
    "organisationId", "username", "groups", "expiry", "status",
    "useDefaultPermissionSets?", "permissionSets", "emailUser?",
    "allowEmailLogin?", "password", "attribute/title",
    "attribute/forenames", "attribute/surname", "attribute/department",
    "attribute/position", "attribute/emailAddress", "attribute/phone",
    "attribute/fax", "attribute/identifier", "attribute/postalAddress",
    "attribute/notes",
]


def normalize_baseline_schema(baseline_df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize OpenAthens baseline columns. Mainly ensures attribute/emailAddress exists.

    NOTE: This is deliberately simpler than the shared normalize_baseline_schema
    in df_utils.py. OpenAthens does not enforce a full required-column schema —
    we only need the email column. The shared version (with required_columns and
    alias_map) would be overkill here.
    """
    if baseline_df.empty:
        return pd.DataFrame()

    df_norm = baseline_df.copy()
    df_norm.columns = df_norm.columns.str.strip()

    # Ensure the required email column is present
    if "attribute/emailAddress" not in df_norm.columns:
        # Try case-insensitive match
        for col in df_norm.columns:
            if col.lower().strip() == "attribute/emailaddress":
                df_norm = df_norm.rename(columns={col: "attribute/emailAddress"})
                break
        else:
            raise KeyError("Required column 'attribute/emailAddress' not found in OpenAthens baseline.")

    return df_norm


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows by Term Email, keeping first occurrence."""
    if df.empty:
        return df
    emails = normalize_email_identity(df, ATHENS_EMAIL_PRIORITY)
    valid = (emails != "") & (emails != "nan")
    df_valid = df[valid].copy()
    df_valid["_email_dedup"] = emails[valid]
    df_valid = df_valid.drop_duplicates(subset=["_email_dedup"], keep="first")
    df_valid = df_valid.drop(columns=["_email_dedup"])
    return df_valid


def generate_athens_upload(df: pd.DataFrame) -> pd.DataFrame:
    """Map cleaned Quercus data to the OpenAthens 21-column upload template."""
    if df.empty:
        return pd.DataFrame(columns=ATHENS_UPLOAD_COLUMNS)

    n = len(df)

    first_names = df.get("First Name", pd.Series([""] * n)).fillna("").astype(str).str.strip()
    last_names = df.get("Last Name", pd.Series([""] * n)).fillna("").astype(str).str.strip()
    emails = df.get("Term Email", pd.Series([""] * n)).fillna("")

    blank = [""] * n
    data = {
        "organisationId": blank,
        "username": blank,
        "groups": ["ncad_students"] * n,
        "expiry": ["2026-09-23"] * n,
        "status": ["pending"] * n,
        "useDefaultPermissionSets?": blank,
        "permissionSets": ["cad#0001"] * n,
        "emailUser?": ["TRUE"] * n,
        "allowEmailLogin?": ["TRUE"] * n,
        "password": blank,
        "attribute/title": blank,
        "attribute/forenames": first_names,
        "attribute/surname": last_names,
        "attribute/department": blank,
        "attribute/position": blank,
        "attribute/emailAddress": emails,
        "attribute/phone": blank,
        "attribute/fax": blank,
        "attribute/identifier": blank,
        "attribute/postalAddress": blank,
        "attribute/notes": blank,
    }

    return pd.DataFrame(data, columns=ATHENS_UPLOAD_COLUMNS)


def generate_athens_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Legacy export: simple 4-column mapper for the /export/all endpoint.
    Input: cleaned Quercus DataFrame (from transform_quercus, not preprocess_quercus).
    Output: Term Email → email_address, First Name → forename,
            Last Name → surname, ID Number → identifier.
    """
    columns_mapping = {
        "Term Email": "email_address",
        "First Name": "forename",
        "Last Name": "surname",
        "ID Number": "identifier",
    }
    missing_cols = [col for col in columns_mapping.keys() if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Required columns missing for Athens export: {missing_cols}")
    return df[list(columns_mapping.keys())].rename(columns=columns_mapping)


def run_athens_pipeline(baseline_df: pd.DataFrame, quercus_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Orchestrate the OpenAthens comparison pipeline.

    Args:
        baseline_df: OpenAthens export CSV (baseline snapshot).
        quercus_df: Cleaned Quercus dataframe (after preprocess_quercus).

    Returns:
        tuple: (new_users_df, upload_df)
            - new_users_df: new students detected after comparison (debug file).
            - upload_df: 21-column OpenAthens upload template.
    """
    baseline_normalized = normalize_baseline_schema(baseline_df)
    new_users = detect_new_users(baseline_normalized, quercus_df, ATHENS_EMAIL_PRIORITY)
    new_users_deduped = deduplicate(new_users)
    upload_df = generate_athens_upload(new_users_deduped)
    return new_users_deduped, upload_df
