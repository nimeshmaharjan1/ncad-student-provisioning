import logging
import zipfile
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
import io
from app.services.library_service import clean_library_data, build_library_template
from app.utils.date_utils import date_suffix

logger = logging.getLogger(__name__)
router = APIRouter()

LIBRARY_QUERCUS_REQUIRED_COLUMNS = [
    "ID Number",
]

LIBRARY_QUERCUS_OPTIONAL_COLUMNS = [
    "First Name", "Last Name", "Gender", "Course Code",
    "Course Instance Start Date", "Course Instance End Date",
]


@router.post("/export")
async def export_library(files: list[UploadFile] = File(...)):
    try:
        dfs = []
        for f in files:
            contents = await f.read()
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
            df.columns = df.columns.str.strip()
            dfs.append(df)

        # --- Schema validation (first file is representative) ---
        if dfs:
            first_df = dfs[0]
            quercus_cols = set(first_df.columns)
            missing_required = [col for col in LIBRARY_QUERCUS_REQUIRED_COLUMNS if col not in quercus_cols]
            missing_optional = [col for col in LIBRARY_QUERCUS_OPTIONAL_COLUMNS if col not in quercus_cols]

            if missing_required:
                logger.warning("Library export rejected — missing required columns: %s", missing_required)
                return JSONResponse(
                    status_code=422,
                    content={
                        "detail": f"Missing required columns: {', '.join(missing_required)}",
                        "error_code": "missing_required_columns",
                        "missing_required": missing_required,
                        "missing_optional": missing_optional,
                        "present_columns": sorted(quercus_cols),
                        "all_required": LIBRARY_QUERCUS_REQUIRED_COLUMNS,
                        "all_optional": LIBRARY_QUERCUS_OPTIONAL_COLUMNS,
                    },
                )

            if missing_optional:
                logger.info("Optional columns missing (will be left blank): %s", missing_optional)

        cleaned = clean_library_data(*dfs)
        final = build_library_template(cleaned)

        ds = date_suffix()

        cleaned_csv = cleaned.to_csv(index=False).encode("utf-8")
        final_csv = final.to_csv(index=False).encode("utf-8")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{ds}_library_cleaned.csv", cleaned_csv)
            zf.writestr(f"{ds}_library.csv", final_csv)

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=\"{ds}_library_export.zip\""
            },
        )

    except ValueError as e:
        logger.exception("Value error during Library export")
        return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "bad_request"})
    except KeyError as e:
        logger.exception("Missing column during Library export")
        return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "missing_columns"})
    except Exception:
        logger.exception("Unexpected error during Library export")
        return JSONResponse(status_code=500, content={"detail": "Unexpected server error", "error_code": "internal_error"})
