import pandas as pd
from app.services.quercus_preprocess import (
    clean_id_number,
    extract_course_number,
    merge_quercus_files,
    preprocess_quercus,
)

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


def clean_library_data(*dfs: pd.DataFrame) -> pd.DataFrame:
    cleaned = preprocess_quercus(merge_quercus_files(*dfs))
    if cleaned.empty:
        return cleaned

    if "Course Code" in cleaned.columns:
        course_nums = cleaned["Course Code"].apply(extract_course_number)
    else:
        course_nums = pd.Series([None] * len(cleaned))

    cleaned["borrowerCategory"] = course_nums.apply(_assign_borrower_category)
    return cleaned


def build_library_template(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=LIBRARY_OUTPUT_COLUMNS)

    n = len(df)

    final_ids = df["ID Number"].apply(clean_id_number)

    first_names = df.get("First Name", pd.Series([""] * n)).fillna("").astype(str).str.strip()
    last_names = df.get("Last Name", pd.Series([""] * n)).fillna("").astype(str).str.strip()

    gender = df.get("Gender", pd.Series([None] * n)).apply(_validate_gender)

    emails = df.get("Term Email", pd.Series([""] * n)).fillna("")

    borrower_category = df.get("borrowerCategory", pd.Series([""] * n)).fillna("").astype(str).str.strip()

    circ_dates = df.get("Course Instance Start Date", pd.Series([None] * n)).apply(_format_date_ymd)
    oclc_dates = df.get("Course Instance End Date", pd.Series([None] * n)).apply(_format_date_ymd)

    blank = [""] * n

    data = {
        "prefix": blank,
        "givenName": first_names,
        "middleName": blank,
        "familyName": last_names,
        "suffix": blank,
        "nickname": blank,
        "canSelfEdit": blank,
        "dateOfBirth": blank,
        "gender": gender,
        "institutionId": ["46722"] * n,
        "barcode": final_ids,
        "idAtSource": final_ids,
        "sourceSystem": ["https://idp.ncad.ie/idp/shibboleth"] * n,
        "borrowerCategory": borrower_category,
        "circRegistrationDate": circ_dates,
        "oclcExpirationDate": oclc_dates,
        "homeBranch": ["266006"] * n,
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
        "username": blank,
        "illId": blank,
        "illApprovalStatus": blank,
        "illPatronType": blank,
        "illPickupLocation": blank,
    }

    return pd.DataFrame(data, columns=LIBRARY_OUTPUT_COLUMNS)


def generate_library_export(*dfs: pd.DataFrame) -> pd.DataFrame:
    cleaned = clean_library_data(*dfs)
    return build_library_template(cleaned)
