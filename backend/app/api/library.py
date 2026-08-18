import logging
import zipfile
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
import io
from app.services.library_service import clean_library_data, build_library_template
from app.core.quercus_schema import (
    check_columns,
    missing_required_response,
    blocking_missing_required,
)
from app.core.settings import get_validation_mode
from app.utils.date_utils import date_suffix
from app.utils.df_utils import backfill_missing_columns

logger = logging.getLogger(__name__)
router = APIRouter()


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
        missing_required_header = None
        if dfs:
            check = check_columns("library", dfs[0].columns)
            if check["missing_required"]:
                blocking = blocking_missing_required("library", check)
                if blocking and get_validation_mode("library") == "strict":
                    logger.warning("Library export rejected — missing required columns: %s", blocking)
                    return missing_required_response("library", {**check, "missing_required": blocking})
                logger.warning(
                    "Library export proceeding — missing required columns auto-added as blank: %s",
                    check["missing_required"],
                )
                dfs = [backfill_missing_columns(df, check["missing_required"]) for df in dfs]
                missing_required_header = ", ".join(check["missing_required"])

            if check["missing_optional"]:
                logger.info("Optional columns missing (will be left blank): %s", check["missing_optional"])

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

        headers = {
            "Content-Disposition": f"attachment; filename=\"{ds}_library_export.zip\"",
        }
        if missing_required_header:
            headers["X-Missing-Required"] = missing_required_header

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers=headers,
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
