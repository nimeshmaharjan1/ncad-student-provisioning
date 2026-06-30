import pandas as pd

# ==============================================================================
# NCAD CANVAS PROVISIONING PIPELINE
#
# 1. canvas_baseline is an immutable snapshot of current Canvas system state.
# 2. quercus_df is a delta input (may contain multiple files merged and cleaned).
# 3. System output MUST be:
#    - new_canvas_users_df (only new identities)
#    - updated_baseline_df (new Canvas reference file)
#
# 4. Identity key is ALWAYS: email (Term Email).
# ==============================================================================

CANVAS_BASELINE_COLUMNS = [
    "user_id", "integration_id", "login_id", "password",
    "first_name", "last_name", "full_name", "sortable_name",
    "short_name", "email", "status",
]

CANVAS_QUERCUS_REQUIRED_COLUMNS = [
    "ID Number", "First Name", "Last Name", "Term Email",
]


def normalize_email_identity(df: pd.DataFrame) -> pd.Series:
    if "email" in df.columns:
        email_col = "email"
    elif "Term Email" in df.columns:
        email_col = "Term Email"
    else:
        raise KeyError("Identity email column ('email' or 'Term Email') not found in DataFrame.")
    return df[email_col].fillna("").astype(str).str.strip().str.lower()


def normalize_baseline_schema(baseline_df: pd.DataFrame) -> pd.DataFrame:
    if baseline_df.empty:
        return pd.DataFrame(columns=CANVAS_BASELINE_COLUMNS)

    df_norm = baseline_df.copy()

    expected_lookup = {col.lower(): col for col in CANVAS_BASELINE_COLUMNS}
    rename_map = {}
    for col in df_norm.columns:
        stripped = col.strip()
        key = stripped.lower()
        if key in expected_lookup and stripped != expected_lookup[key]:
            rename_map[col] = expected_lookup[key]
    df_norm = df_norm.rename(columns=rename_map)

    for col in CANVAS_BASELINE_COLUMNS:
        if col not in df_norm.columns:
            df_norm[col] = ""
    return df_norm[CANVAS_BASELINE_COLUMNS]


def map_quercus_to_canvas(quercus_df: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in CANVAS_QUERCUS_REQUIRED_COLUMNS if col not in quercus_df.columns]
    if missing:
        raise KeyError(f"Required Quercus columns missing for Canvas mapping: {missing}")

    first = quercus_df["First Name"].fillna("").astype(str).str.strip()
    last = quercus_df["Last Name"].fillna("").astype(str).str.strip()

    data = {
        "user_id": quercus_df["ID Number"].astype(str).str.strip(),
        "integration_id": "",
        "login_id": quercus_df["Term Email"].fillna("").astype(str).str.strip(),
        "password": "",
        "first_name": first,
        "last_name": last,
        "full_name": first + " " + last,
        "sortable_name": last + "," + first,
        "short_name": "",
        "email": quercus_df["Term Email"].fillna("").astype(str).str.strip(),
        "status": "active",
    }

    return pd.DataFrame(data, columns=CANVAS_BASELINE_COLUMNS)


def detect_new_users(baseline_df: pd.DataFrame, quercus_mapped_df: pd.DataFrame) -> pd.DataFrame:
    baseline_emails = set(normalize_email_identity(baseline_df))
    quercus_emails = normalize_email_identity(quercus_mapped_df)

    new_mask = (
        (quercus_emails != "") &
        (quercus_emails != "nan") &
        (~quercus_emails.isin(baseline_emails))
    )

    return quercus_mapped_df[new_mask].copy()


def update_baseline_state(baseline_df: pd.DataFrame, new_users_df: pd.DataFrame) -> pd.DataFrame:
    combined = pd.concat([baseline_df, new_users_df], ignore_index=True)

    combined["_email_clean"] = normalize_email_identity(combined)
    combined = combined[(combined["_email_clean"] != "") & (combined["_email_clean"] != "nan")]

    combined = combined.drop_duplicates(subset=["_email_clean"], keep="first")
    combined = combined.drop(columns=["_email_clean"])

    return combined


def generate_canvas_comparison_exports(baseline_df: pd.DataFrame, quercus_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    baseline_normalized = normalize_baseline_schema(baseline_df)

    if not baseline_normalized.empty:
        missing = [col for col in CANVAS_BASELINE_COLUMNS if col not in baseline_normalized.columns]
        if missing:
            raise KeyError(f"Required Canvas baseline columns missing: {missing}")

    quercus_mapped = map_quercus_to_canvas(quercus_df)

    new_users_raw = detect_new_users(baseline_normalized, quercus_mapped)

    sorted_new = new_users_raw.sort_values(by="email").reset_index(drop=True)

    updated_baseline = update_baseline_state(baseline_normalized, sorted_new)

    audit_info = {
        "new_users_count": len(sorted_new),
        "updated_baseline_count": len(updated_baseline),
        "filtered_out_status_count": quercus_df.attrs.get("filtered_out_status_count", 0),
        "external_students_removed_count": quercus_df.attrs.get("external_students_removed_count", 0),
        "duplicate_rows_detected": quercus_df.attrs.get("duplicate_rows_detected", 0),
    }

    return sorted_new, updated_baseline, audit_info


# ==============================================================================
# Legacy export — used by /export/all and /export/bundle (not the Canvas pipeline)
# ==============================================================================

def generate_canvas_export(df: pd.DataFrame) -> pd.DataFrame:
    columns_mapping = {
        "Term Email": "email",
        "First Name": "first_name",
        "Last Name": "last_name",
        "Course Code": "course_code",
        "Status": "enrollment_status"
    }

    missing_cols = [col for col in columns_mapping.keys() if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Required columns missing for Canvas export: {missing_cols}")

    return df[list(columns_mapping.keys())].rename(columns=columns_mapping)
