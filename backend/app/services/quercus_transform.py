import pandas as pd
from app.services.quercus_preprocess import clean_id_number

def transform_quercus(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms a Quercus data DataFrame.
    
    Rules:
    1. Normalize "ID Number" FIRST to "Normalized ID"
    2. Filter rows by Status (Registered or starts with Recommended)
    3. Remove rows where Normalized ID is empty
    4. Remove duplicates using "Normalized ID" as the unique key, keeping the first occurrence
    5. Generate Term Email from Normalized ID
    6. Drop "Normalized ID" column before returning final dataframe
    """
    if df.empty:
        df_copy = df.copy()
        df_copy["Term Email"] = pd.Series(dtype=str)
        return df_copy

    df_copy = df.copy()

    # Verify required columns exist
    if "Status" not in df_copy.columns:
        raise KeyError("Required column 'Status' not found in DataFrame.")
    if "ID Number" not in df_copy.columns:
        raise KeyError("Required column 'ID Number' not found in DataFrame.")

    # 1. Normalize "ID Number" FIRST
    df_copy["Normalized ID"] = df_copy["ID Number"].apply(clean_id_number)

    # 2. Filter rows by Status
    status_series = df_copy["Status"].fillna("").astype(str)
    mask = (status_series == "Registered") | (status_series.str.startswith("Recommended"))
    df_copy = df_copy[mask]

    # 3. Remove rows where Normalized ID is empty
    df_copy = df_copy[df_copy["Normalized ID"] != ""]

    # 4. Use "Normalized ID" for deduplication (NOT raw ID Number), keeping the first occurrence
    df_copy = df_copy.drop_duplicates(subset=["Normalized ID"], keep="first")

    # 5. Generate Term Email from Normalized ID
    df_copy["Term Email"] = df_copy["Normalized ID"].apply(lambda x: f"{x}@student.ncad.ie")

    # 6. Drop "Normalized ID" column before returning final dataframe
    df_copy = df_copy.drop(columns=["Normalized ID"])

    return df_copy

