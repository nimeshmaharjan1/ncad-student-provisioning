import pandas as pd

def generate_athens_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a system-specific Athens export DataFrame from the cleaned Quercus data.
    
    Requirements:
    - Input: cleaned Quercus dataframe
    - Output columns ONLY:
      - Term Email → email_address
      - First Name → forename
      - Last Name → surname
      - ID Number → identifier
    - Do NOT include any other columns
    - Do NOT modify original dataframe
    - Return a new dataframe only
    - If required columns are missing, raise KeyError with clear message
    """
    columns_mapping = {
        "Term Email": "email_address",
        "First Name": "forename",
        "Last Name": "surname",
        "ID Number": "identifier"
    }

    # Verify all required columns are present
    missing_cols = [col for col in columns_mapping.keys() if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Required columns missing for Athens export: {missing_cols}")

    # Select required columns and return the renamed copy
    return df[list(columns_mapping.keys())].rename(columns=columns_mapping)
