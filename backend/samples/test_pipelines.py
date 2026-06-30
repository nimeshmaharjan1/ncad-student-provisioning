import sys, os
# Make paths relative to script location, not CWD
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))  # backend/ for app imports

import pandas as pd
from app.services.quercus_preprocess import preprocess_quercus
from app.services.ldap_export import generate_ldap_comparison_exports
from app.services.canvas_service import generate_canvas_comparison_exports
from app.services.google_service import run_google_pipeline
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

# --- LDAP ---
baseline_ldap = load("baseline_ldap.csv")
new_ldap, updated_ldap, audit = generate_ldap_comparison_exports(baseline_ldap, cleaned)
print(f"\nLDAP: {audit['new_students_count']} new, {audit['updated_baseline_count']} baseline")
# Baseline has Alice + Carol. New: Bob, Dave, Frank = 3
assert audit['new_students_count'] == 3, f"Expected 3 new LDAP students; got {audit['new_students_count']}"

# --- CANVAS ---
baseline_canvas = load("baseline_canvas.csv")
new_canvas, updated_canvas, audit_c = generate_canvas_comparison_exports(baseline_canvas, cleaned)
print(f"Canvas: {audit_c['new_users_count']} new, {audit_c['updated_baseline_count']} baseline")
assert audit_c['new_users_count'] == 3, f"Expected 3 new Canvas users; got {audit_c['new_users_count']}"

# --- GOOGLE ---
baseline_google = load("baseline_google.csv")
upload_google, reactivate_google, audit_g = run_google_pipeline(baseline_google, cleaned)
print(f"Google: {audit_g['total_upload_count']} upload, {audit_g['reactivation_count']} reactivate")
# Carol is suspended in baseline and appears in Quercus -> reactivate (1)
# Bob, Dave, Frank not in baseline -> upload (3)
assert audit_g['total_upload_count'] == 3, f"Expected 3 upload; got {audit_g['total_upload_count']}"
assert audit_g['reactivation_count'] == 1, f"Expected 1 reactivation; got {audit_g['reactivation_count']}"

# --- ATHENS ---
baseline_athens = load("baseline_athens.csv")
new_athens, upload_athens = run_athens_pipeline(baseline_athens, cleaned)
print(f"Athens: {len(new_athens)} new, {len(upload_athens)} upload")
# Baseline has Alice + Carol. New: Bob, Dave, Frank = 3
assert len(new_athens) == 3, f"Expected 3 new Athens users; got {len(new_athens)}"

# --- VERIFY FULL BASELINE RERUN ---
# LDAP rerun: use updated_ldap as new baseline + same cleaned Quercus
new_ldap2, _, audit2 = generate_ldap_comparison_exports(updated_ldap, cleaned)
print(f"\nRerun test (LDAP): {audit2['new_students_count']} new -> should be 0")
assert audit2['new_students_count'] == 0, f"Rerun should produce 0 new students; got {audit2['new_students_count']}"

print("\n" + "=" * 60)
print("ALL PIPELINE SMOKE TESTS PASSED")
print("=" * 60)
