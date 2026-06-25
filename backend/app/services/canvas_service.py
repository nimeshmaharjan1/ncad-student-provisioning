import pandas as pd

def generate_canvas_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a system-specific Canvas export DataFrame from the cleaned Quercus data.
    
    Requirements:
    - Input: cleaned Quercus dataframe
    - Output columns ONLY:
      - Term Email → email
      - First Name → first_name
      - Last Name → last_name
      - Course Code → course_code
      - Status → enrollment_status
    - Do not modify original dataframe
    - Return new dataframe only
    - If any required column is missing, raise KeyError with clear message
    """
    columns_mapping = {
        "Term Email": "email",
        "First Name": "first_name",
        "Last Name": "last_name",
        "Course Code": "course_code",
        "Status": "enrollment_status"
    }

    # Verify all required columns are present
    missing_cols = [col for col in columns_mapping.keys() if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Required columns missing for Canvas export: {missing_cols}")

    # Select required columns and return the renamed copy
    return df[list(columns_mapping.keys())].rename(columns=columns_mapping)
