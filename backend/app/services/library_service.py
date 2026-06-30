import pandas as pd
from app.services.quercus_preprocess import clean_id_number, extract_course_number, merge_quercus_files

LIBRARY_OUTPUT_COLUMNS = [
    "prefix", "givenName", "middleName", "familyName", "suffix",
    "nickname", "canSelfEdit", "dateOfBirth", "gender", "institutionId",
    "barcode", "idAtSource", "sourceSystem", "borrowerCategory",
    "circRegistrationDate", "oclcExpirationDate", "homeBranch",
    "primaryStreetAddressLine1", "primaryStreetAddressLine2",
    "primaryCityOrLocality", "primaryStateOrProvince", "primaryPostalCode",
    "primaryCountry", "primaryPhone",
    "secondaryStreetAddressLine1", "secondaryStreetAddressLine2",
    "secondaryCityOrLocality", "secondaryStateOrProvince",
    "secondaryPostalCode", "secondaryCountry", "secondaryPhone",
    "emailAddress", "mobilePhone",
    "notificationEmail", "notificationTextPhone",
    "patronNotes", "photoURL",
    "customdata1", "customdata2", "customdata3", "customdata4",
    "username", "illId", "illApprovalStatus", "illPatronType", "illPickupLocation",
]


def _assign_borrower_category(course_num: int | None) -> str:
    if course_num is None:
        return "CEAD"
    if course_num < 100:
        return "CEAD"
    elif course_num <= 399:
        return "FTUG"
    return "FTPG"


def _validate_gender(val) -> str:
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().upper()
    if s in ("MALE", "FEMALE"):
        return s
    return "UNKNOWN"


def _format_date_ymd(val) -> str:
    if pd.isna(val):
        return ""
    try:
        dt = pd.to_datetime(val, errors="coerce")
        if pd.isna(dt):
            return ""
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return ""


def generate_library_export(*dfs: pd.DataFrame) -> pd.DataFrame:
    """
    Pure Quercus → Library transformation pipeline.

    Accepts one or more Quercus Library export DataFrames, merges them in order,
    and produces a Library upload CSV with the full 48-column schema.
    """
    merged = merge_quercus_files(*dfs)
    if merged.empty:
        return pd.DataFrame(columns=LIBRARY_OUTPUT_COLUMNS)

    df = merged.copy()

    # 1. Create Term Email from ID Number (8-digit zero-padded)
    cleaned_ids = df["ID Number"].apply(clean_id_number)
    df["_term_email"] = cleaned_ids.apply(
        lambda x: f"{x}@student.ncad.ie" if x else ""
    )

    # 2. Remove blank Term Emails
    df = df[df["_term_email"] != ""].copy()

    # 3. Remove duplicates by Term Email, keeping first occurrence
    df = df.drop_duplicates(subset=["_term_email"], keep="first")

    # 4. Remove external students
    if "Course Description" in df.columns:
        df = df[
            df["Course Description"].astype(str).str.strip()
            != "NCAD Elective - External Students"
        ]

    # 5. Borrower category from Course Code
    if "Course Code" in df.columns:
        course_nums = df["Course Code"].apply(extract_course_number)
    else:
        course_nums = pd.Series([None] * len(df))
    borrower_categories = course_nums.apply(_assign_borrower_category)

    # 6. Gender validation
    gender_col = df.get("Gender", pd.Series([None] * len(df)))
    genders = gender_col.apply(_validate_gender)

    # 7. Date formatting (yyyy-mm-dd)
    start_col = df.get("Course Instance Start Date", pd.Series([None] * len(df)))
    circ_dates = start_col.apply(_format_date_ymd)

    end_col = df.get("Course Instance End Date", pd.Series([None] * len(df)))
    oclc_dates = end_col.apply(_format_date_ymd)

    # Re-derive cleaned IDs after row filtering
    final_ids = df["ID Number"].apply(clean_id_number)
    first_names = df.get("First Name", pd.Series([""] * len(df))).fillna("").astype(str).str.strip()
    last_names = df.get("Last Name", pd.Series([""] * len(df))).fillna("").astype(str).str.strip()
    emails = df["_term_email"]

    # 8. Build output DataFrame
    blank = [""] * len(df)
    data = {
        "prefix": blank,
        "givenName": first_names,
        "middleName": blank,
        "familyName": last_names,
        "suffix": blank,
        "nickname": blank,
        "canSelfEdit": blank,
        "dateOfBirth": blank,
        "gender": genders,
        "institutionId": final_ids,
        "barcode": final_ids,
        "idAtSource": final_ids,
        "sourceSystem": ["https://idp.ncad.ie/idp/shibboleth"] * len(df),
        "borrowerCategory": borrower_categories,
        "circRegistrationDate": circ_dates,
        "oclcExpirationDate": oclc_dates,
        "homeBranch": ["266006"] * len(df),
        "primaryStreetAddressLine1": blank,
        "primaryStreetAddressLine2": blank,
        "primaryCityOrLocality": blank,
        "primaryStateOrProvince": blank,
        "primaryPostalCode": blank,
        "primaryCountry": blank,
        "primaryPhone": blank,
        "secondaryStreetAddressLine1": blank,
        "secondaryStreetAddressLine2": blank,
        "secondaryCityOrLocality": blank,
        "secondaryStateOrProvince": blank,
        "secondaryPostalCode": blank,
        "secondaryCountry": blank,
        "secondaryPhone": blank,
        "emailAddress": emails,
        "mobilePhone": blank,
        "notificationEmail": blank,
        "notificationTextPhone": blank,
        "patronNotes": blank,
        "photoURL": blank,
        "customdata1": blank,
        "customdata2": blank,
        "customdata3": blank,
        "customdata4": blank,
        "username": final_ids,
        "illId": blank,
        "illApprovalStatus": blank,
        "illPatronType": blank,
        "illPickupLocation": blank,
    }

    return pd.DataFrame(data, columns=LIBRARY_OUTPUT_COLUMNS)
