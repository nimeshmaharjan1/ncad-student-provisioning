from fastapi import HTTPException
import pandas as pd
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import io
import logging
from app.services.quercus_preprocess import preprocess_quercus, merge_quercus_files
from app.core.quercus_schema import check_source_columns
from app.utils.date_utils import date_suffix
from app.utils.df_utils import sanitize_records

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload")
async def upload_quercus(files: list[UploadFile] = File(...)):
    dfs = []
    total_rows = 0
    missing_by_file = []
    for f in files:
        contents = await f.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        df.columns = df.columns.str.strip()
        total_rows += len(df)
        dfs.append(df)

        # WARN-mode column check — never blocks processing. The response tells
        # the frontend which columns are missing so the user can recheck their
        # Quercus export settings before running downstream exports.
        missing = check_source_columns(df.columns)
        if missing:
            logger.warning(
                "Quercus upload: file '%s' is missing expected columns: %s",
                f.filename, missing,
            )
            missing_by_file.append({"filename": f.filename, "missing": missing})

    if not dfs:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    merged_df = merge_quercus_files(*dfs)
    cleaned_df = preprocess_quercus(merged_df)

    sample_rows = sanitize_records(cleaned_df.head(10))

    # Union of missing columns across all files (deduplicated, first-seen order)
    missing_union: list[str] = []
    for entry in missing_by_file:
        for col in entry["missing"]:
            if col not in missing_union:
                missing_union.append(col)

    return {
        "uploaded_files": [f.filename for f in files],
        "raw_row_count": total_rows,
        "cleaned_row_count": len(cleaned_df),
        "filtered_out_status_count": cleaned_df.attrs.get("filtered_out_status_count", 0),
        "external_students_removed_count": cleaned_df.attrs.get("external_students_removed_count", 0),
        "duplicate_rows_detected": cleaned_df.attrs.get("duplicate_rows_detected", 0),
        "sample_rows": sample_rows,
        "missing_columns": missing_union,
        "missing_columns_by_file": missing_by_file,
    }


@router.post("/download")
async def download_quercus(files: list[UploadFile] = File(...)):
    dfs = []
    for f in files:
        contents = await f.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        df.columns = df.columns.str.strip()
        dfs.append(df)

    merged_df = merge_quercus_files(*dfs)
    cleaned_df = preprocess_quercus(merged_df)

    ds = date_suffix()

    # Convert cleaned DataFrame to CSV string
    stream = io.StringIO()
    cleaned_df.to_csv(stream, index=False)
    response_content = stream.getvalue()

    # Create response with headers to force file download
    return StreamingResponse(
        io.BytesIO(response_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=\"{ds}_quercus.csv\""}
    )
