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
    Extracts the actual course number from the course code string.
    
    DESIGN DECISION:
    Course codes at NCAD typically start with an alphabetic prefix representing the school
    or program (e.g. 'AD', 'CEAD') directly followed by the course number digits (e.g. '401', '050').
    To distinguish the course number from separate year prefix or suffix digits (e.g. '2026-AD401'
    or 'AD401PC2026'), we look for the first sequence of digits that immediately follows alphabetic
    characters. If no such pattern is found, we fall back to the first numeric sequence in the string.
    """
    if pd.isna(course_code):
        return None
    code_str = str(course_code).strip()
    
    # Match letters followed by optional spaces and then digits (e.g. AD 401 -> capture group 401)
    match = re.search(r'[a-zA-Z]+\s*(\d+)', code_str)
    if match:
        return int(match.group(1))
        
    # Fallback to the first numeric sequence found anywhere in the string
    fallback_match = re.search(r'\d+', code_str)
    if fallback_match:
        return int(fallback_match.group(0))
        
    return None

def preprocess_quercus(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocesses a Quercus DataFrame.
    
    Processing Order:
    1. Create Term Email
    2. Remove blank Term Emails
    3. Filter Status (Registered / Recommend*)
    4. Remove External Students (using Course Description)
    5. Remove duplicates using Term Email (keeping FIRST occurrence)
    6. Create Type column using course number
    """
    if df.empty:
        df_copy = df.copy()
        df_copy["Term Email"] = pd.Series(dtype=str)
        df_copy["Type"] = pd.Series(dtype=str)
        df_copy.attrs["filtered_out_status_count"] = 0
        df_copy.attrs["external_students_removed_count"] = 0
        df_copy.attrs["duplicate_rows_detected"] = 0
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

    # 3. Filter Registered / Recommend* Status
    filtered_out_status_count = 0
    if "Status" in df_copy.columns:
        before_status = len(df_copy)
        status_series = df_copy["Status"].fillna("").astype(str)
        mask = (status_series == "Registered") | (status_series.str.startswith("Recommend"))
        df_copy = df_copy[mask]
        filtered_out_status_count = before_status - len(df_copy)

    # 4. Remove External Students
    external_students_removed_count = 0
    if "Course Description" in df_copy.columns:
        before_external = len(df_copy)
        df_copy = df_copy[df_copy["Course Description"].astype(str).str.strip() != "NCAD Elective - External Students"]
        external_students_removed_count = before_external - len(df_copy)

    # IMPORTANT:
    # Status filtering must happen BEFORE duplicate removal.
    #
    # A student may appear multiple times in Quercus with different statuses
    # (for example Withdrawn and Registered).
    #
    # We first keep only valid student records:
    #   - Registered
    #   - Recommend*
    #
    # Then duplicate removal is applied using Term Email.
    #
    # Duplicate removal keeps the FIRST occurrence.
    # Files must be merged in chronological order:
    # oldest file first, newest file last.
    #
    # Example:
    # merge_quercus_files(df_2025, df_2026)
    #
    # This preserves the same behaviour as the existing NCAD workflow
    # while avoiding invalid statuses suppressing valid records.
    duplicate_rows_detected = 0
    before_dup = len(df_copy)
    df_copy = df_copy.drop_duplicates(subset=["Term Email"], keep="first")
    duplicate_rows_detected = before_dup - len(df_copy)

    # Store audit metadata in attributes
    df_copy.attrs["filtered_out_status_count"] = filtered_out_status_count
    df_copy.attrs["external_students_removed_count"] = external_students_removed_count
    df_copy.attrs["duplicate_rows_detected"] = duplicate_rows_detected

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

