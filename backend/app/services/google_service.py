import uuid
import pandas as pd

GOOGLE_BASELINE_COLUMNS = [
    "First Name [Required]",
    "Last Name [Required]",
    "Email Address [Required]",
    "Password",
    "Org Unit Path",
    "Change Password at Next Sign-In",
    "New Status [UPLOAD ONLY]",
    "Status",
]

GOOGLE_REACTIVATION_COLUMNS = [
    "First Name",
    "Last Name",
    "Email Address [Required]",
    "Type",
    "Current Status",
    "Reactivation Flag",
    "Suggested Org Unit Path",
]

GOOGLE_UPLOAD_COLUMNS = [
    "First Name [Required]",
    "Last Name [Required]",
    "Email Address [Required]",
    "Password [Required]",
    "Password Hash Function [UPLOAD ONLY]",
    "Org Unit Path [Required]",
    "New Primary Email [UPLOAD ONLY]",
    "Home Secondary Email",
    "Work Secondary Email",
    "Work Phone",
    "Home Phone",
    "Mobile Phone",
    "Work Address",
    "Home Address",
    "Employee ID",
    "Employee Type",
    "Employee Title",
    "Manager Email",
    "Department",
    "Cost Center",
    "Building ID",
    "Floor Name",
    "Floor Section",
    "Change Password at Next Sign-In",
]

ORG_UNIT_MAP = {
    "UG": "/UG",
    "PG": "/PG",
    "CEAD": "/CEAD",
}


def normalize_baseline_schema(baseline_df: pd.DataFrame) -> pd.DataFrame:
    if baseline_df.empty:
        return pd.DataFrame(columns=GOOGLE_BASELINE_COLUMNS)

    df_norm = baseline_df.copy()
    df_norm.columns = df_norm.columns.str.strip()

    ALIAS_MAP = {
        "Status [READ ONLY]": "Status",
        "Password [Required]": "Password",
        "Org Unit Path [Required]": "Org Unit Path",
    }

    alias_rename = {}
    for col in df_norm.columns:
        stripped = col.strip()
        if stripped in ALIAS_MAP:
            alias_rename[col] = ALIAS_MAP[stripped]
    df_norm = df_norm.rename(columns=alias_rename)

    expected_lookup = {col.lower(): col for col in GOOGLE_BASELINE_COLUMNS}
    rename_map = {}
    for col in df_norm.columns:
        stripped = col.strip()
        key = stripped.lower()
        if key in expected_lookup and stripped != expected_lookup[key]:
            rename_map[col] = expected_lookup[key]
    df_norm = df_norm.rename(columns=rename_map)

    for col in GOOGLE_BASELINE_COLUMNS:
        if col not in df_norm.columns:
            df_norm[col] = ""

    return df_norm


def normalize_email_identity(df: pd.DataFrame) -> pd.Series:
    """
    Backward-compatible identity resolver for Google + Quercus pipelines.

    Priority order:
    1. Email Address [Required] (Google baseline export)
    2. Term Email (Quercus generated email)
    """
    if "Email Address [Required]" in df.columns:
        email_col = "Email Address [Required]"
    elif "Term Email" in df.columns:
        email_col = "Term Email"
    else:
        raise KeyError(
            "Identity email column not found. Expected either "
            "'Email Address [Required]' (Google) or 'Term Email' (Quercus)."
        )

    return (
        df[email_col]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )


def diff_new_users(baseline_df: pd.DataFrame, quercus_df: pd.DataFrame) -> pd.DataFrame:
    baseline_emails = set(normalize_email_identity(baseline_df))
    quercus_emails = normalize_email_identity(quercus_df)

    new_mask = (
        (quercus_emails != "") &
        (quercus_emails != "nan") &
        (~quercus_emails.isin(baseline_emails))
    )

    return quercus_df[new_mask].copy()


def diff_reactivation_candidates(baseline_df: pd.DataFrame, quercus_df: pd.DataFrame) -> pd.DataFrame:
    quercus_emails = set(normalize_email_identity(quercus_df))
    baseline_emails = normalize_email_identity(baseline_df)

    suspended_mask = (
        (baseline_df["Status"].astype(str).str.strip().str.lower() == "suspended") |
        (baseline_df["New Status [UPLOAD ONLY]"].astype(str).str.strip().str.lower() == "suspended")
    )

    in_quercus_mask = (
        (baseline_emails != "") &
        (baseline_emails != "nan") &
        (baseline_emails.isin(quercus_emails))
    )

    return baseline_df[suspended_mask & in_quercus_mask].copy()


def map_org_unit(type_val) -> str:
    if pd.isna(type_val):
        return "/"
    type_str = str(type_val).strip()
    return ORG_UNIT_MAP.get(type_str, "/")


def generate_password() -> str:
    return str(uuid.uuid4())


def generate_reactivation_export(reactivation_df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in reactivation_df.iterrows():
        current_status = row.get("Status", row.get("New Status [UPLOAD ONLY]", "Suspended"))
        records.append({
            "First Name": row.get("First Name [Required]", ""),
            "Last Name": row.get("Last Name [Required]", ""),
            "Email Address [Required]": row.get("Email Address [Required]", ""),
            "Type": row.get("Type", ""),
            "Current Status": str(current_status).strip(),
            "Reactivation Flag": "TRUE",
            "Suggested Org Unit Path": row.get("Org Unit Path", ""),
        })

    return pd.DataFrame(records, columns=GOOGLE_REACTIVATION_COLUMNS)


def generate_upload_export(new_users_df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in new_users_df.iterrows():
        records.append({
            "First Name [Required]": row.get("First Name", row.get("First Name [Required]", "")),
            "Last Name [Required]": row.get("Last Name", row.get("Last Name [Required]", "")),
            "Email Address [Required]": row.get("Term Email", row.get("Email Address [Required]", "")),
            "Password [Required]": generate_password(),
            "Password Hash Function [UPLOAD ONLY]": "",
            "Org Unit Path [Required]": "/All_Active_Students",
            "New Primary Email [UPLOAD ONLY]": "",
            "Home Secondary Email": "",
            "Work Secondary Email": "",
            "Work Phone": "",
            "Home Phone": "",
            "Mobile Phone": "",
            "Work Address": "",
            "Home Address": "",
            "Employee ID": "",
            "Employee Type": "",
            "Employee Title": "",
            "Manager Email": "",
            "Department": "",
            "Cost Center": "",
            "Building ID": "",
            "Floor Name": "",
            "Floor Section": "",
            "Change Password at Next Sign-In": "TRUE",
        })

    return pd.DataFrame(records, columns=GOOGLE_UPLOAD_COLUMNS)


def run_google_pipeline(baseline_df: pd.DataFrame, quercus_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    baseline_normalized = normalize_baseline_schema(baseline_df)

    new_users_raw = diff_new_users(baseline_normalized, quercus_df)
    reactivation_candidates_raw = diff_reactivation_candidates(baseline_normalized, quercus_df)

    # Enrich reactivation candidates with Type from Quercus data
    if not reactivation_candidates_raw.empty:
        quercus_emails = normalize_email_identity(quercus_df)
        reactivation_emails = normalize_email_identity(reactivation_candidates_raw)
        type_lookup = quercus_df[["Type"]].copy()
        type_lookup["_email"] = quercus_emails
        type_map = type_lookup.drop_duplicates(subset="_email").set_index("_email")["Type"]
        reactivation_candidates_raw["Type"] = reactivation_emails.map(type_map).fillna("")

    reactivation_df = generate_reactivation_export(reactivation_candidates_raw)
    upload_df = generate_upload_export(new_users_raw)

    audit_info = {
        "reactivation_count": len(reactivation_df),
        "total_upload_count": len(upload_df),
    }

    return upload_df, reactivation_df, audit_info
