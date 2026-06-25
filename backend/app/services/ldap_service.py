import pandas as pd

def generate_ldap_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a system-specific LDAP export DataFrame from the cleaned Quercus data.
    
    Requirements:
    - Input is the cleaned Quercus dataframe.
    - Output only LDAP-required columns:
      - LDAP ID
      - First Name
      - Last Name
      - Term Email
    - Rename columns to LDAP format:
      - LDAP ID → uid
      - First Name → givenName
      - Last Name → sn
      - Term Email → mail
    - Return a new dataframe only (does not modify the original).
    """
    columns_mapping = {
        "LDAP ID": "uid",
        "First Name": "givenName",
        "Last Name": "sn",
        "Term Email": "mail"
    }

    # Verify all required columns are present
    missing_cols = [col for col in columns_mapping.keys() if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Required columns missing for LDAP export: {missing_cols}")

    # Select required columns and return the renamed copy
    return df[list(columns_mapping.keys())].rename(columns=columns_mapping)
