import sys, os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
from app.services.ldap_export import generate_ldap_comparison_exports
from app.services.quercus_preprocess import preprocess_quercus

SAMPLES = os.path.join(os.path.dirname(PROJECT_ROOT), "samples")

quercus_raw = pd.read_csv(os.path.join(SAMPLES, "quercus_valid.csv"))
cleaned = preprocess_quercus(quercus_raw)

baseline_df = pd.read_csv(os.path.join(SAMPLES, "baseline_ldap.csv"))

new_students, updated_baseline, audit = generate_ldap_comparison_exports(
    baseline_df,
    cleaned
)

print("\n=== AUDIT ===")
print(audit)

print("\n=== NEW STUDENTS ===")
print(new_students[["Student ID", "First Name", "Last Name", "Email_address"]].to_string(index=False))

print("\n=== UPDATED BASELINE ===")
print(updated_baseline[["Student ID", "First Name", "Last Name", "Email_address"]].to_string(index=False))
