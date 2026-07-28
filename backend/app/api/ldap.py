import logging
import os
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
import io
import zipfile
from app.services.ldap_export import (
    generate_ldap_comparison_exports,
    QUERCUS_SCHEMA_REQUIRED_COLUMNS,
    QUERCUS_SCHEMA_OPTIONAL_COLUMNS,
    LDAP_SCHEMA_REQUIRED_COLUMNS,
)
from app.services.quercus_preprocess import preprocess_quercus
from app.utils.date_utils import date_suffix

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/download")
async def download_ldap(
    baseline: UploadFile = File(...),
    quercus: UploadFile = File(...),
    format: str = "zip",
    new_students_filename: str | None = Form(None),
    updated_baseline_filename: str | None = Form(None),
):
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

        # --- Schema validation with structured error response ---
        quercus_cols = set(quercus_df.columns)
        missing_required = [col for col in QUERCUS_SCHEMA_REQUIRED_COLUMNS if col not in quercus_cols]
        missing_optional = [col for col in QUERCUS_SCHEMA_OPTIONAL_COLUMNS if col not in quercus_cols]
        present_columns = sorted(quercus_cols)

        if missing_required:
            logger.warning(
                "LDAP export rejected — missing required Quercus columns: %s", missing_required
            )
            return JSONResponse(
                status_code=422,
                content={
                    "detail": f"Missing required columns: {', '.join(missing_required)}",
                    "error_code": "missing_required_columns",
                    "missing_required": missing_required,
                    "missing_optional": missing_optional,
                    "present_columns": present_columns,
                    "all_required": QUERCUS_SCHEMA_REQUIRED_COLUMNS,
                    "all_optional": QUERCUS_SCHEMA_OPTIONAL_COLUMNS,
                },
            )

        if missing_optional:
            logger.info(
                "Optional Quercus columns missing (will be left blank): %s", missing_optional
            )

        cleaned_quercus_df = preprocess_quercus(quercus_df)

        new_students_df, updated_baseline_df, _ = generate_ldap_comparison_exports(
            baseline_df, cleaned_quercus_df
        )

        ds = date_suffix()

        def _ensure_csv(name: str) -> str:
            return name if name.lower().endswith(".csv") else name + ".csv"

        new_fn = _ensure_csv(new_students_filename) if new_students_filename else f"{ds}_ldap_new_students.csv"
        upd_fn = _ensure_csv(updated_baseline_filename) if updated_baseline_filename else f"{ds}_ldap_updated_baseline.csv"

        if format == "zip":
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(new_fn, new_students_df.to_csv(index=False))
                zf.writestr(upd_fn, updated_baseline_df.to_csv(index=False))
            zip_buffer.seek(0)
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename=\"{ds}_ldap_export.zip\""},
            )

        stream = io.StringIO()
        stream.write("=== NEW STUDENTS ===\n")
        new_students_df.to_csv(stream, index=False)
        stream.write("\n")
        stream.write("=== UPDATED BASELINE ===\n")
        updated_baseline_df.to_csv(stream, index=False)
        response_content = stream.getvalue()

        return StreamingResponse(
            io.BytesIO(response_content.encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=\"{ds}_ldap.csv\""},
        )

    except ValueError as e:
        logger.exception("Value error during LDAP export")
        return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "bad_request"})
    except KeyError as e:
        logger.exception("Missing column during LDAP export")
        return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "missing_columns"})
    except Exception:
        logger.exception("Unexpected error during LDAP export")
        return JSONResponse(status_code=500, content={"detail": "Unexpected server error", "error_code": "internal_error"})