import pandas as pd
from app.utils.df_utils import (
    normalize_email_identity,
    normalize_baseline_schema,
    detect_new_users,
    update_baseline_state,
)

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

CANVAS_EMAIL_PRIORITY = ["email", "Term Email"]

CANVAS_BASELINE_COLUMNS = [
    "user_id", "integration_id", "login_id", "password",
    "first_name", "last_name", "full_name", "sortable_name",
    "short_name", "email", "status",
]

CANVAS_QUERCUS_REQUIRED_COLUMNS = [
    "ID Number", "First Name", "Last Name", "Term Email",
]


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


def generate_canvas_comparison_exports(baseline_df: pd.DataFrame, quercus_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    baseline_normalized = normalize_baseline_schema(baseline_df, CANVAS_BASELINE_COLUMNS)

    if not baseline_normalized.empty:
        missing = [col for col in CANVAS_BASELINE_COLUMNS if col not in baseline_normalized.columns]
        if missing:
            raise KeyError(f"Required Canvas baseline columns missing: {missing}")

    quercus_mapped = map_quercus_to_canvas(quercus_df)

    new_users_raw = detect_new_users(baseline_normalized, quercus_mapped, CANVAS_EMAIL_PRIORITY)

    sorted_new = new_users_raw.sort_values(by="email").reset_index(drop=True)

    updated_baseline = update_baseline_state(baseline_normalized, sorted_new, CANVAS_EMAIL_PRIORITY)

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
