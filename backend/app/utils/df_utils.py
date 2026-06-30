"""
Shared DataFrame utility functions for the NCAD provisioning pipeline.

These functions are used across LDAP, Canvas, Google Workspace, and OpenAthens
pipelines. Each accepts system-specific column name lists (email_priority_columns,
required_columns) since column names differ per system.

Athens has its own simpler normalize_baseline_schema in athens_service.py
(no full column list enforcement). Everything else lives here.
"""

import pandas as pd


def normalize_email_identity(df: pd.DataFrame, priority_columns: list[str]) -> pd.Series:
    """
    Normalize the identity email column to a consistent Series.

    Checks df.columns for each name in priority_columns order (baseline column
    first, Quercus column second). Returns the first match as a normalized
    Series (fillna(""), str.strip, str.lower).

    Raises KeyError if none of the priority_columns are found.
    """
    for col in priority_columns:
        if col in df.columns:
            return df[col].fillna("").astype(str).str.strip().str.lower()
    raise KeyError(
        f"Identity email column not found. Expected one of: {priority_columns}"
    )


def normalize_baseline_schema(
    baseline_df: pd.DataFrame,
    required_columns: list[str],
    alias_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    Normalize a system-specific baseline DataFrame to its expected column schema.

    Steps:
    1. If empty, return an empty DataFrame with required_columns.
    2. Copy the input, strip column whitespace.
    3. Apply alias_map (Google-specific renames like "Status [READ ONLY]" → "Status").
    4. Case-insensitive rename: lowercase-match input columns to required_columns.
    5. Fill any missing required columns with empty strings.
    6. Subset to required_columns in canonical order.

    Happens once at ingestion, before any diff or mapping logic.
    """
    if baseline_df.empty:
        return pd.DataFrame(columns=required_columns)

    df_norm = baseline_df.copy()
    df_norm.columns = df_norm.columns.str.strip()

    if alias_map:
        rename = {}
        for col in df_norm.columns:
            stripped = col.strip()
            if stripped in alias_map:
                rename[col] = alias_map[stripped]
        df_norm = df_norm.rename(columns=rename)

    expected_lookup = {col.lower(): col for col in required_columns}
    rename_map = {}
    for col in df_norm.columns:
        stripped = col.strip()
        key = stripped.lower()
        if key in expected_lookup and stripped != expected_lookup[key]:
            rename_map[col] = expected_lookup[key]
    df_norm = df_norm.rename(columns=rename_map)

    for col in required_columns:
        if col not in df_norm.columns:
            df_norm[col] = ""

    return df_norm[required_columns]


def detect_new_users(
    baseline_df: pd.DataFrame,
    quercus_mapped_df: pd.DataFrame,
    email_priority_columns: list[str],
) -> pd.DataFrame:
    """
    Identity diff: find Quercus records not present in the baseline.

    INLINE DOCUMENTATION
    --------------------
    - Email is the only identity key:
      This is the canonical identity key across both baseline and Quercus
      systems to determine whether a record already exists.

    - Comparison is state-based, not overwrite-based:
      We compare the incoming data against the historical snapshot to identify
      records that do not exist in the current baseline.

    - Deduplication happens after diff detection:
      Running deduplication before diff detection could mask new user entries
      or lead to state loss. By diffing first, we ensure we evaluate all
      incoming records.
    """
    baseline_emails = set(normalize_email_identity(baseline_df, email_priority_columns))
    quercus_emails = normalize_email_identity(quercus_mapped_df, email_priority_columns)

    new_mask = (
        (quercus_emails != "")
        & (quercus_emails != "nan")
        & (~quercus_emails.isin(baseline_emails))
    )

    return quercus_mapped_df[new_mask].copy()


def update_baseline_state(
    baseline_df: pd.DataFrame,
    new_users_df: pd.DataFrame,
    email_priority_columns: list[str],
) -> pd.DataFrame:
    """
    Merge baseline and new users, then deduplicate to form the updated baseline.

    INLINE DOCUMENTATION
    --------------------
    - Baseline-first ordering matters:
      Placing baseline_df first and new_users_df second guarantees that
      drop_duplicates(keep="first") always preserves the historical state
      of existing accounts (including their original passcodes and details)
      rather than overwriting them.

    - Duplication logic is centralized to preserve state integrity:
      Deduplication happens ONLY here in this state management stage.
    """
    combined = pd.concat([baseline_df, new_users_df], ignore_index=True)

    combined["_email_clean"] = normalize_email_identity(combined, email_priority_columns)
    combined = combined[(combined["_email_clean"] != "") & (combined["_email_clean"] != "nan")]

    combined = combined.drop_duplicates(subset=["_email_clean"], keep="first")
    combined = combined.drop(columns=["_email_clean"])

    return combined


def sanitize_records(df: pd.DataFrame) -> list[dict]:
    """
    Convert a DataFrame to list-of-dicts, replacing NaN/None with Python None
    for standard JSON serialization via FastAPI.
    """
    records = df.to_dict(orient="records")
    for row in records:
        for key, val in row.items():
            if pd.isna(val):
                row[key] = None
    return records
