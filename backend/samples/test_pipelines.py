import sys, os
# Make paths relative to script location, not CWD
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))  # backend/ for app imports

import pandas as pd
from app.services.quercus_preprocess import preprocess_quercus
from app.services.ldap_export import generate_ldap_comparison_exports, TO_EMAIL_1_2_COLUMNS
from app.services.canvas_service import generate_canvas_comparison_exports
from app.services.google_service import run_google_pipeline, TO_EMAIL_3_COLUMNS
from app.services.athens_service import run_athens_pipeline

SAMPLES = os.path.join(PROJECT_ROOT, "samples")

def load(name):
    return pd.read_csv(os.path.join(SAMPLES, name))

print("=" * 60)
print("FULL PIPELINE SMOKE TEST")
print("=" * 60)

# --- QUERCUS ---
raw = load("quercus_valid.csv")
cleaned = preprocess_quercus(raw)
print(f"\nQuercus: {len(raw)} raw -> {len(cleaned)} cleaned")
print(f"  filtered_out_status_count: {cleaned.attrs.get('filtered_out_status_count')}")
print(f"  external_students_removed_count: {cleaned.attrs.get('external_students_removed_count')}")
print(f"  duplicate_rows_detected: {cleaned.attrs.get('duplicate_rows_detected')}")
# 5 cleaned: Alice (CEAD), Bob (UG), Carol (PG), Dave (UG), Frank (UG - Excel DOB)
assert len(cleaned) == 5, f"Expected 5 cleaned rows; got {len(cleaned)}"
# ID Number is the source of truth: normalized to 8 digits BEFORE Term Email
# is derived from it, so every downstream ID (Canvas, LDAP, Athens, Library)
# matches the email.
assert cleaned["ID Number"].astype(str).str.len().eq(8).all(), "ID Number must be 8 digits"
assert cleaned["ID Number"].tolist() == ["00012345", "00067890", "00054321", "00098765", "00022222"], f"ID Number padding wrong: {cleaned['ID Number'].tolist()}"
assert cleaned["Term Email"].tolist() == ["00012345@student.ncad.ie", "00067890@student.ncad.ie", "00054321@student.ncad.ie", "00098765@student.ncad.ie", "00022222@student.ncad.ie"], f"Term Email must derive from padded ID: {cleaned['Term Email'].tolist()}"
assert (cleaned["LDAP ID"].astype(str) == "").all(), "empty LDAP ID must stay empty after padding"

# --- LDAP ---
baseline_ldap = load("baseline_ldap.csv")
new_ldap, to_email_1_2, updated_ldap, audit = generate_ldap_comparison_exports(baseline_ldap, cleaned)
print(f"\nLDAP: {audit['new_students_count']} new, {audit['updated_baseline_count']} baseline, {len(to_email_1_2)} to_email_1_2")
# Baseline has Alice + Carol. New: Bob, Dave, Frank = 3
assert audit['new_students_count'] == 3, f"Expected 3 new LDAP students; got {audit['new_students_count']}"
assert new_ldap["Student ID"].astype(str).str.len().eq(8).all(), "LDAP Student ID must be 8-digit padded"
assert set(new_ldap["Student ID"]) == {"00067890", "00098765", "00022222"}, f"LDAP Student ID padding wrong: {set(new_ldap['Student ID'])}"
# Email 1 recipient file is now delivered by the LDAP step — one row per LDAP-new
# student, password straight from the same export (no lookup, always matches AD).
assert list(to_email_1_2.columns) == TO_EMAIL_1_2_COLUMNS, "to_email_1_2 columns mismatch"
assert len(to_email_1_2) == 3, f"to_email_1_2 must cover every LDAP-new student; got {len(to_email_1_2)}"
assert to_email_1_2["email"].tolist() == new_ldap["Email_address"].tolist(), "to_email_1_2 email must be the LDAP Email_address"
assert to_email_1_2["password"].tolist() == new_ldap["Passcode"].tolist(), "to_email_1_2 password must match the LDAP Passcode"
assert to_email_1_2["password"].astype(str).str.len().gt(0).all(), "to_email_1_2 passwords must not be blank"

# --- CANVAS ---
baseline_canvas = load("baseline_canvas.csv")
new_canvas, updated_canvas, audit_c = generate_canvas_comparison_exports(baseline_canvas, cleaned)
print(f"Canvas: {audit_c['new_users_count']} new, {audit_c['updated_baseline_count']} baseline")
assert audit_c['new_users_count'] == 3, f"Expected 3 new Canvas users; got {audit_c['new_users_count']}"
assert new_canvas["user_id"].astype(str).str.len().eq(8).all(), "Canvas user_id must be 8-digit padded"
assert set(new_canvas["user_id"]) == {"00067890", "00098765", "00022222"}, f"Canvas user_id padding wrong: {set(new_canvas['user_id'])}"

# --- GOOGLE ---
baseline_google = load("baseline_google.csv")
upload_google, reactivate_google, to_email_3, audit_g = run_google_pipeline(baseline_google, cleaned)
print(f"Google: {audit_g['total_upload_count']} upload, {audit_g['reactivation_count']} reactivate")
# Carol is suspended in baseline and appears in Quercus -> reactivate (1)
# Bob, Dave, Frank not in baseline -> upload (3)
assert audit_g['total_upload_count'] == 3, f"Expected 3 upload; got {audit_g['total_upload_count']}"
assert audit_g['reactivation_count'] == 1, f"Expected 1 reactivation; got {audit_g['reactivation_count']}"
# to_email_3 is the only Mail Merge file left in the Google step (Email 1
# is now delivered by the LDAP step). It covers every Google-new student.
assert len(to_email_3) == 3, "to_email_3 must cover every Google-new student"
assert list(to_email_3.columns) == TO_EMAIL_3_COLUMNS, "to_email_3 columns mismatch"
# 3: recipient = Home Email (blank for students with none); username/newemail = Term Email;
#    password = same Google temp password as the upload.
assert (to_email_3["password"].tolist() == upload_google["Password [Required]"].tolist()), "to_email_3 password must match Google upload password"
assert (to_email_3["username"].tolist() == to_email_3["newemail"].tolist()), "username must equal newemail"
assert (to_email_3["username"].tolist() == upload_google["Email Address [Required]"].tolist()), "to_email_3 username/newemail must be the student email"
assert to_email_3["email"].tolist() == ["bob.johnson@example.com", "dave.brown@example.com", ""], f"to_email_3 home emails wrong: {to_email_3['email'].tolist()}"
assert audit_g["no_home_email_students"] == ["Frank Wilson"], f"no-home-email warning wrong: {audit_g['no_home_email_students']}"
print(f"Google email file: {len(to_email_3)} to_email_3 (shared passwords; no-home-email warning: {audit_g['no_home_email_students']})")

# --- ATHENS ---
baseline_athens = load("baseline_athens.csv")
new_athens, upload_athens = run_athens_pipeline(baseline_athens, cleaned)
print(f"Athens: {len(new_athens)} new, {len(upload_athens)} upload")
assert new_athens["ID Number"].astype(str).str.len().eq(8).all(), "Athens new-user ID Number must be 8-digit padded"
# Baseline has Alice + Carol. New: Bob, Dave, Frank = 3
assert len(new_athens) == 3, f"Expected 3 new Athens users; got {len(new_athens)}"

# --- VERIFY FULL BASELINE RERUN ---
# LDAP rerun: use updated_ldap as new baseline + same cleaned Quercus
new_ldap2, _, _, audit2 = generate_ldap_comparison_exports(updated_ldap, cleaned)
print(f"\nRerun test (LDAP): {audit2['new_students_count']} new -> should be 0")
assert audit2['new_students_count'] == 0, f"Rerun should produce 0 new students; got {audit2['new_students_count']}"

# --- CANVAS STAFF ---
from app.services.canvas_staff_service import build_canvas_staff_rows
staff, staff_warnings = build_canvas_staff_rows(["Cian Delaney Byrne", "Roisin Quigley"])
print(f"\nCanvas staff: {len(staff)} rows")
assert len(staff) == 2, f"Expected 2 staff rows; got {len(staff)}"
assert staff_warnings == [], f"Expected no warnings for full names; got {staff_warnings}"
assert staff.iloc[0]["login_id"] == "delaneybyrnec@staff.ncad.ie", f"Expected delaneybyrnec@staff.ncad.ie; got {staff.iloc[0]['login_id']}"
assert staff.iloc[0]["user_id"] == "delaneybyrnec"
assert staff.iloc[0]["first_name"] == "Cian"
assert staff.iloc[0]["last_name"] == "Delaney Byrne"
assert staff.iloc[0]["full_name"] == "Cian Delaney Byrne"
assert staff.iloc[0]["sortable_name"] == "Delaney Byrne, Cian"
assert staff.iloc[0]["email"] == "delaneybyrnec@staff.ncad.ie"
assert staff.iloc[0]["status"] == "active"
assert staff.iloc[1]["login_id"] == "quigleyr@staff.ncad.ie", f"Expected quigleyr@staff.ncad.ie; got {staff.iloc[1]['login_id']}"
assert staff.iloc[1]["first_name"] == "Roisin"
assert staff.iloc[1]["last_name"] == "Quigley"

# Single-word name: accepted with a warning, login = the name itself
staff1, staff_warnings1 = build_canvas_staff_rows(["Cian"])
print(f"Canvas staff (single word): {len(staff1)} row, {len(staff_warnings1)} warning")
assert len(staff1) == 1
assert len(staff_warnings1) == 1, f"Expected 1 warning for single-word name; got {staff_warnings1}"
assert staff1.iloc[0]["first_name"] == "Cian"
assert staff1.iloc[0]["last_name"] == ""
assert staff1.iloc[0]["login_id"] == "cian@staff.ncad.ie", f"Expected cian@staff.ncad.ie; got {staff1.iloc[0]['login_id']}"
assert staff1.iloc[0]["sortable_name"] == "Cian"

# --- LIBRARY STAFF ---
from app.services.library_staff_service import build_library_staff_rows
from app.services.library_service import LIBRARY_OUTPUT_COLUMNS
people = [
    ("Cian Delaney Byrne", "12345678", "Male", "2026-08-05", "2028-08-05"),
    ("Roisin Quigley", "", "", "2026-09-01", "2027-01-30"),
    ("Liam", "12345678", "", "", ""),
]
lib_staff, lib_warnings = build_library_staff_rows(people)
print(f"\nLibrary staff: {len(lib_staff)} rows, {len(lib_warnings)} warnings")
assert len(lib_staff) == 3, f"Expected 3 library staff rows; got {len(lib_staff)}"
assert list(lib_staff.columns) == LIBRARY_OUTPUT_COLUMNS, "Library staff columns must match LIBRARY_OUTPUT_COLUMNS"
assert lib_staff.iloc[0]["givenName"] == "Cian"
assert lib_staff.iloc[0]["familyName"] == "Delaney Byrne"
assert lib_staff.iloc[0]["gender"] == "Male"
assert lib_staff.iloc[0]["institutionId"] == "46722"
assert lib_staff.iloc[0]["barcode"] == "12345678"
assert lib_staff.iloc[0]["idAtSource"] == "delaneybyrnec"
assert lib_staff.iloc[0]["sourceSystem"] == "https://idp.ncad.ie/idp/shibboleth"
assert lib_staff.iloc[0]["borrowerCategory"] == "FTS"
assert lib_staff.iloc[0]["circRegistrationDate"] == "2026-08-05"
assert lib_staff.iloc[0]["oclcExpirationDate"] == "2028-08-05"
assert lib_staff.iloc[0]["homeBranch"] == "266006"
assert lib_staff.iloc[0]["emailAddress"] == "delaneybyrnec@staff.ncad.ie"
assert lib_staff.iloc[0]["username"] == ""
# Per-person dates: Roisin has her own reg + expiry, no barcode -> warning
assert lib_staff.iloc[1]["gender"] == "UNKNOWN", "Blank gender must become UNKNOWN"
assert lib_staff.iloc[1]["circRegistrationDate"] == "2026-09-01"
assert lib_staff.iloc[1]["oclcExpirationDate"] == "2027-01-30"
assert lib_staff.iloc[1]["emailAddress"] == "quigleyr@staff.ncad.ie"
# Single-word name + missing registration date -> warnings; no-surname login
assert len(lib_warnings) == 3, f"Expected 3 warnings (no barcode + no last name + no reg date); got {lib_warnings}"
assert lib_staff.iloc[2]["emailAddress"] == "liam@staff.ncad.ie"
assert lib_staff.iloc[2]["circRegistrationDate"] == "", "Missing registration date must leave the column blank"
assert lib_staff.iloc[2]["barcode"] == "12345678"

# Bad date -> rejected
try:
    build_library_staff_rows([("Cian Delaney Byrne", "12345678", "", "05-08-2026", "")])
    raise AssertionError("Expected ValueError for non-YYYY-MM-DD registration date")
except ValueError:
    pass

# --- LIBRARY regression: gapped index + missing optional column ---
# Repro for the "array length N does not match index length M" crash when a
# filtered (non-contiguous) index meets a template column the file no longer
# has (e.g. Gender dropped from the new Quercus export format).
from app.services.library_service import clean_library_data, build_library_template
from app.services.quercus_preprocess import merge_quercus_files

_lib_cols = [
    "Status", "ID Number", "Course Code", "Course Description",
    "Course Instance Course Year", "Course Instance Course Stream",
    "First Name", "Last Name", "Term Email", "LDAP ID", "Student Category",
    "Home Email", "Course Instance End Date", "Course Instance Start Date",
]

def _mk_quercus(ids, statuses):
    df = pd.DataFrame({c: "x" for c in _lib_cols}, index=range(len(ids)))
    df["ID Number"] = ids
    df["Status"] = statuses
    df["First Name"] = "F"
    df["Last Name"] = "L"
    df["Course Code"] = "AD401"
    df["Term Email"] = [f"{i}@student.ncad.ie" for i in ids]
    df["Course Instance Start Date"] = "01-Sep-26"
    df["Course Instance End Date"] = "31-Aug-27"
    return df

_ids = list(range(10000000, 10000000 + 2178))
_f1 = _mk_quercus(_ids, ["Registered" if i % 5 else "Withdrawn" for i in range(2178)])
_f2 = _mk_quercus(_ids, ["Withdrawn" if i % 5 else "Registered" for i in range(2178)])
_lib_cleaned = clean_library_data(_f1, _f2)
assert "Gender" not in _lib_cleaned.columns, "Test setup: Gender must be absent"
assert _lib_cleaned.index.equals(pd.RangeIndex(len(_lib_cleaned))), "Index must be contiguous after preprocessing"
assert len(_lib_cleaned) > 0
_lib_final = build_library_template(_lib_cleaned)
assert _lib_final.shape == (len(_lib_cleaned), len(LIBRARY_OUTPUT_COLUMNS)), f"Library template shape wrong: {_lib_final.shape}"
assert _lib_final.iloc[0]["gender"] == "UNKNOWN", "Missing Gender must export as UNKNOWN"
assert _lib_final.iloc[0]["circRegistrationDate"] == "2026-09-01", "circRegistrationDate must be yyyy-mm-dd"
assert _lib_final.iloc[0]["oclcExpirationDate"] == "2027-08-31", "oclcExpirationDate must be yyyy-mm-dd"

_lib_txt = _lib_final.to_csv(sep="\t", index=False)
_lib_txt_lines = _lib_txt.strip().splitlines()
assert "\t" in _lib_txt_lines[0] and len(_lib_txt_lines[0].split("\t")) == len(LIBRARY_OUTPUT_COLUMNS), "TXT must be tab-delimited with all 46 columns"
assert "2026-09-01" in _lib_txt and "2027-08-31" in _lib_txt, "TXT must keep yyyy-mm-dd dates untouched"
assert "\t" in _lib_txt_lines[1], "data rows must be tab-separated"

_lib_with_gender = _lib_cleaned.copy()
_lib_with_gender["Gender"] = ["male", "F"] + ["Other"] * (len(_lib_with_gender) - 2)
_t_g = build_library_template(_lib_with_gender)
assert _t_g.iloc[0]["gender"] == "MALE", "Gender must be uppercased passthrough"
assert _t_g.iloc[1]["gender"] == "F", "Non-whitelist value must pass through, not become UNKNOWN"
print(f"Library regression: {len(_lib_cleaned)} rows -> {_lib_final.shape} (no index-length crash, TXT tab-delimited + yyyy-mm-dd)")

print("\n" + "=" * 60)
print("ALL PIPELINE SMOKE TESTS PASSED")
print("=" * 60)
