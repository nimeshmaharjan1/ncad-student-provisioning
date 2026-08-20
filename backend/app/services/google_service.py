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

# Recipient source for the Thunderbird Mail Merge "Student Email Account Details"
# campaign (the generated replacement for the manually-maintained `to_mail`
# file in Email_2025/). Carries both the NCAD address (Email Address) and the
# personal address (Home Email); the mail-merge operator picks the recipient
# column. `Temp` holds the same temporary password assigned to the Google
# account so the emailed credentials match.
EMAIL_NEW_STUDENTS_COLUMNS = [
    "First Name [Required]",
    "Last Name [Required]",
    "Email Address [Required]",
    "Status",
    "Home Email",
    "Temp",
]

DATE_TO_EMAIL_COLUMNS = [
    "email",
    "firstname",
    "username",
    "password",
    "newemail",
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


def generate_upload_export(new_users_df: pd.DataFrame, passwords: list[str]) -> pd.DataFrame:
    records = []
    for (_, row), password in zip(new_users_df.iterrows(), passwords):
        records.append({
            "First Name [Required]": row.get("First Name", row.get("First Name [Required]", "")),
            "Last Name [Required]": row.get("Last Name", row.get("Last Name [Required]", "")),
            "Email Address [Required]": row.get("Term Email", row.get("Email Address [Required]", "")),
            "Password [Required]": password,
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


def generate_email_new_students_export(new_users_df: pd.DataFrame, passwords: list[str]) -> pd.DataFrame:
    """Build the `to_mail`-style recipient file for the Student Email Details campaign."""
    records = []
    for (_, row), password in zip(new_users_df.iterrows(), passwords):
        records.append({
            "First Name [Required]": row.get("First Name", row.get("First Name [Required]", "")),
            "Last Name [Required]": row.get("Last Name", row.get("Last Name [Required]", "")),
            "Email Address [Required]": row.get("Term Email", row.get("Email Address [Required]", "")),
            "Status": str(row.get("Type", "")).strip(),
            "Home Email": row.get("Home Email", ""),
            "Temp": password,
        })

    return pd.DataFrame(records, columns=EMAIL_NEW_STUDENTS_COLUMNS)


def generate_date_to_email_export(new_users_df: pd.DataFrame, passwords: list[str]) -> pd.DataFrame:
    """Build the credentials-to-email file (recipient, username, password, new email)."""
    records = []
    for (_, row), password in zip(new_users_df.iterrows(), passwords):
        username = row.get("Term Email", row.get("Email Address [Required]", ""))
        records.append({
            "email": username,
            "firstname": row.get("First Name", row.get("First Name [Required]", "")),
            "username": username,
            "password": password,
            "newemail": username,
        })

    return pd.DataFrame(records, columns=DATE_TO_EMAIL_COLUMNS)


def run_google_pipeline(baseline_df: pd.DataFrame, quercus_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    baseline_normalized = normalize_baseline_schema(baseline_df, GOOGLE_BASELINE_COLUMNS, GOOGLE_ALIAS_MAP)

    new_users_raw = detect_new_users(baseline_normalized, quercus_df, GOOGLE_EMAIL_PRIORITY)
    reactivation_candidates_raw = diff_reactivation_candidates(baseline_normalized, quercus_df)

    # One temporary password per new student, shared across the Google upload
    # and the email exports so the emailed credentials match the account.
    passwords = [generate_password() for _ in range(len(new_users_raw))]

    # Enrich reactivation candidates with Type from Quercus data
    if not reactivation_candidates_raw.empty:
        quercus_emails = normalize_email_identity(quercus_df, GOOGLE_EMAIL_PRIORITY)
        reactivation_emails = normalize_email_identity(reactivation_candidates_raw, GOOGLE_EMAIL_PRIORITY)
        type_lookup = quercus_df[["Type"]].copy()
        type_lookup["_email"] = quercus_emails
        type_map = type_lookup.drop_duplicates(subset="_email").set_index("_email")["Type"]
        reactivation_candidates_raw["Type"] = reactivation_emails.map(type_map).fillna("")

    reactivation_df = generate_reactivation_export(reactivation_candidates_raw)
    upload_df = generate_upload_export(new_users_raw, passwords)
    email_new_students_df = generate_email_new_students_export(new_users_raw, passwords)
    date_to_email_df = generate_date_to_email_export(new_users_raw, passwords)

    audit_info = {
        "reactivation_count": len(reactivation_df),
        "total_upload_count": len(upload_df),
    }

    return upload_df, reactivation_df, email_new_students_df, date_to_email_df, audit_info
