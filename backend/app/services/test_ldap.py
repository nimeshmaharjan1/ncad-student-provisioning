import pandas as pd
from app.services.ldap_export import generate_ldap_comparison_exports

baseline_df = pd.read_csv("baseline.csv")
quercus_df = pd.read_csv("quercus.csv")

new_students, updated_baseline, audit = generate_ldap_comparison_exports(
    baseline_df,
    quercus_df
)

print("\n=== NEW STUDENTS ===")
print(new_students)

print("\n=== UPDATED BASELINE ===")
print(updated_baseline)

print("\n=== AUDIT ===")
print(audit)