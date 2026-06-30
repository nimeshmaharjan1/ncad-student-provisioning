import uuid
import pandas as pd
from app.utils.df_utils import (
    normalize_email_identity,
    normalize_baseline_schema,
    detect_new_users,
)

GOOGLE_EMAIL_PRIORITY = ["Email Address [Required]", "Term Email"]

GOOGLE_ALIAS_MAP = {
    "Status [READ ONLY]": "Status",
    "Password [Required]": "Password",
    "Org Unit Path [Required]": "Org Unit Path",
}

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

def diff_reactivation_candidates(baseline_df: pd.DataFrame, quercus_df: pd.DataFrame) -> pd.DataFrame:
    quercus_emails = set(normalize_email_identity(quercus_df, GOOGLE_EMAIL_PRIORITY))
    baseline_emails = normalize_email_identity(baseline_df, GOOGLE_EMAIL_PRIORITY)

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
    baseline_normalized = normalize_baseline_schema(baseline_df, GOOGLE_BASELINE_COLUMNS, GOOGLE_ALIAS_MAP)

    new_users_raw = detect_new_users(baseline_normalized, quercus_df, GOOGLE_EMAIL_PRIORITY)
    reactivation_candidates_raw = diff_reactivation_candidates(baseline_normalized, quercus_df)

    # Enrich reactivation candidates with Type from Quercus data
    if not reactivation_candidates_raw.empty:
        quercus_emails = normalize_email_identity(quercus_df, GOOGLE_EMAIL_PRIORITY)
        reactivation_emails = normalize_email_identity(reactivation_candidates_raw, GOOGLE_EMAIL_PRIORITY)
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
