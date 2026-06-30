import sys, os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))

import pandas as pd
from app.services.ldap_export import _format_dob_series

df = pd.read_csv(os.path.join(PROJECT_ROOT, "samples", "dob_variety.csv"))
formatted = _format_dob_series(df["Date of Birth"])
for i, row in df.iterrows():
    print(f"  {str(row['Date of Birth']):20s} -> {formatted[i]:15s}  ({row['Course Description']})")
