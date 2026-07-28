import logging
import os
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
import io
import zipfile
from app.services.quercus_preprocess import preprocess_quercus
from app.services.athens_service import run_athens_pipeline
from app.utils.date_utils import date_suffix

logger = logging.getLogger(__name__)
router = APIRouter()

ATHENS_QUERCUS_REQUIRED_COLUMNS = [
    "ID Number", "First Name", "Last Name",
]

ATHENS_QUERCUS_OPTIONAL_COLUMNS: list[str] = []


@router.post("/export")
async def export_athens(baseline: UploadFile = File(...), quercus: UploadFile = File(...)):
    try:
        baseline_contents = await baseline.read()
        quercus_contents = await quercus.read()

        ext = os.path.splitext(baseline.filename or "")[1].lower()
        if ext == ".xlsx":
            baseline_df = pd.read_excel(io.BytesIO(baseline_contents), engine="openpyxl")
        else:
            baseline_df = pd.read_csv(io.StringIO(baseline_contents.decode("utf-8")))
        quercus_df = pd.read_csv(io.StringIO(quercus_contents.decode("utf-8")))

        baseline_df.columns = baseline_df.columns.str.strip()
        quercus_df.columns = quercus_df.columns.str.strip()

        # --- Schema validation ---
        quercus_cols = set(quercus_df.columns)
        missing_required = [col for col in ATHENS_QUERCUS_REQUIRED_COLUMNS if col not in quercus_cols]
        missing_optional = [col for col in ATHENS_QUERCUS_OPTIONAL_COLUMNS if col not in quercus_cols]

        if missing_required:
            logger.warning("OpenAthens export rejected — missing required Quercus columns: %s", missing_required)
            return JSONResponse(
                status_code=422,
                content={
                    "detail": f"Missing required columns: {', '.join(missing_required)}",
                    "error_code": "missing_required_columns",
                    "missing_required": missing_required,
                    "missing_optional": missing_optional,
                    "present_columns": sorted(quercus_cols),
                    "all_required": ATHENS_QUERCUS_REQUIRED_COLUMNS,
                    "all_optional": ATHENS_QUERCUS_OPTIONAL_COLUMNS,
                },
            )

        if missing_optional:
            logger.info("Optional Quercus columns missing (will be left blank): %s", missing_optional)

        cleaned_quercus_df = preprocess_quercus(quercus_df)

        new_users_df, upload_df = run_athens_pipeline(baseline_df, cleaned_quercus_df)

        ds = date_suffix()

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{ds}_athens_new_users.csv", new_users_df.to_csv(index=False))
            zf.writestr(f"{ds}_athens.csv", upload_df.to_csv(index=False))
        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=\"{ds}_athens_export.zip\""},
        )

    except ValueError as e:
        logger.exception("Value error during OpenAthens export")
        return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "bad_request"})
    except KeyError as e:
        logger.exception("Missing column during OpenAthens export")
        return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "missing_columns"})
    except Exception:
        logger.exception("Unexpected error during OpenAthens export")
        return JSONResponse(status_code=500, content={"detail": "Unexpected server error", "error_code": "internal_error"})
