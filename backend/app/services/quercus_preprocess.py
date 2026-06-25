import re
import pandas as pd

def clean_id_number(val) -> str:
    """
    Cleans the ID Number value.
    - If null/NaN/empty, returns empty string.
    - Strips whitespace.
    - Handles float representations (e.g. 12345.0) by removing the trailing '.0'.
    - Returns a zero-padded string of length 8.
    """
    if pd.isna(val):
        return ""
    
    val_str = str(val).strip()
    if not val_str or val_str.lower() == 'nan':
        return ""
    
    # Remove float decimal point if present
    if val_str.endswith('.0'):
        val_str = val_str[:-2]
        
    val_str = val_str.strip()
    if not val_str:
        return ""
    return val_str.zfill(8)

def merge_quercus_files(*dfs: pd.DataFrame) -> pd.DataFrame:
    """
    Accepts multiple DataFrames, concatenates them, and strips column name whitespace.

    IMPORTANT:
    The order of DataFrames passed to this function matters.

    Pass older files first and newer files last.

    Example:
    merge_quercus_files(df_2025, df_2026)

    Duplicate removal later in the pipeline keeps the first occurrence and relies on this ordering.
    """
    if not dfs:
        return pd.DataFrame()
    merged = pd.concat(dfs, ignore_index=True)
    merged.columns = merged.columns.str.strip()
    return merged

def extract_course_number(course_code) -> int | None:
    """
    Extracts the numeric part from the course code string.
    Returns the integer value, or None if no digits are found.
    """
    if pd.isna(course_code):
        return None
    code_str = str(course_code).strip()
    match = re.search(r'\d+', code_str)
    if match:
        return int(match.group())
    return None

def preprocess_quercus(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocesses a Quercus DataFrame.
    
    Processing Order:
    1. Create Term Email
    2. Remove blank Term Emails
    3. Remove duplicates using Term Email (keeping first occurrence)
    4. Filter Registered / Recommend* Status
    5. Remove External Students (using Course Description)
    6. Create Type column using course number
    """
    if df.empty:
        df_copy = df.copy()
        df_copy["Term Email"] = pd.Series(dtype=str)
        df_copy["Type"] = pd.Series(dtype=str)
        return df_copy

    df_copy = df.copy()

    # Verify ID Number is present
    if "ID Number" not in df_copy.columns:
        raise KeyError("Required column 'ID Number' not found in DataFrame.")

    # 1. Create Term Email
    cleaned_ids = df_copy["ID Number"].apply(clean_id_number)
    df_copy["Term Email"] = cleaned_ids.apply(
        lambda x: f"{x}@student.ncad.ie" if x else ""
    )

    # 2. Remove blank Term Emails
    df_copy = df_copy[df_copy["Term Email"] != ""]

    # IMPORTANT:
    # Duplicate removal keeps the FIRST occurrence.
    # Files must be merged in chronological order:
    # oldest file first, newest file last.
    # Example:
    # merge_quercus_files(df_2025, df_2026)
    # This preserves the same behaviour as the existing NCAD Excel workflow.
    df_copy = df_copy.drop_duplicates(subset=["Term Email"], keep="first")

    # 4. Filter Registered / Recommend*
    if "Status" in df_copy.columns:
        status_series = df_copy["Status"].fillna("").astype(str)
        mask = (status_series == "Registered") | (status_series.str.startswith("Recommend"))
        df_copy = df_copy[mask]

    # 5. Remove External Students
    if "Course Description" in df_copy.columns:
        df_copy = df_copy[df_copy["Course Description"].astype(str).str.strip() != "NCAD Elective - External Students"]

    # 6. Create Type column using course number
    if "Course Code" in df_copy.columns:
        course_nums = df_copy["Course Code"].apply(extract_course_number)
        
        def assign_type(num):
            if pd.isna(num):
                return None
            if num <= 100:
                return "CEAD"
            elif 101 <= num <= 400:
                return "UG"
            else:
                return "PG"
                
        df_copy["Type"] = course_nums.apply(assign_type)
    else:
        df_copy["Type"] = None

    return df_copy

