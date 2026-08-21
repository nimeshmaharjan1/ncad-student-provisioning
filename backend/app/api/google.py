import logging
import os
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
import io
import zipfile
from app.services.quercus_preprocess import preprocess_quercus
from app.services.google_service import run_google_pipeline
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
async def export_google(
    baseline: UploadFile = File(...),
    quercus: UploadFile = File(...),
    ldap_export: UploadFile = File(...),
):
    try:
        baseline_contents = await baseline.read()
        quercus_contents = await quercus.read()
        ldap_export_contents = await ldap_export.read()

        ext = os.path.splitext(baseline.filename or "")[1].lower()
        if ext == ".xlsx":
            baseline_df = pd.read_excel(io.BytesIO(baseline_contents), engine="openpyxl")
        else:
            baseline_df = pd.read_csv(io.StringIO(baseline_contents.decode("utf-8")))
        quercus_df = pd.read_csv(io.StringIO(quercus_contents.decode("utf-8")))
        ldap_export_df = pd.read_csv(io.StringIO(ldap_export_contents.decode("utf-8")))

        baseline_df.columns = baseline_df.columns.str.strip()
        quercus_df.columns = quercus_df.columns.str.strip()
        ldap_export_df.columns = ldap_export_df.columns.str.strip()

        # --- Schema validation ---
        check = check_columns("google", quercus_df.columns)
        missing_required_header = None
        if check["missing_required"]:
            blocking = blocking_missing_required("google", check)
            if blocking and get_validation_mode("google") == "strict":
                logger.warning("Google export rejected — missing required Quercus columns: %s", blocking)
                return missing_required_response("google", {**check, "missing_required": blocking})
            logger.warning(
                "Google export proceeding — missing required columns auto-added as blank: %s",
                check["missing_required"],
            )
            quercus_df = backfill_missing_columns(quercus_df, check["missing_required"])
            missing_required_header = ", ".join(check["missing_required"])

        if check["missing_optional"]:
            logger.info("Optional Quercus columns missing (will be left blank): %s", check["missing_optional"])

        cleaned_quercus_df = preprocess_quercus(quercus_df)

        upload_df, reactivation_df, to_email_1_2_df, to_email_3_df, audit = run_google_pipeline(
            baseline_df, cleaned_quercus_df, ldap_export_df
        )

        ds = date_suffix()

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{ds}_google_upload.csv", upload_df.to_csv(index=False))
            zf.writestr(f"{ds}_google_reactivate.csv", reactivation_df.to_csv(index=False))
            zf.writestr(f"{ds}_to_email_1_2.csv", to_email_1_2_df.to_csv(index=False))
            zf.writestr(f"{ds}_to_email_3.csv", to_email_3_df.to_csv(index=False))
        zip_buffer.seek(0)

        headers = {
            "Content-Disposition": f"attachment; filename=\"{ds}_google_export.zip\"",
        }
        if missing_required_header:
            headers["X-Missing-Required"] = missing_required_header
        no_home_email = audit.get("no_home_email_students") or []
        if no_home_email:
            headers["X-No-Home-Email"] = ", ".join(no_home_email)
        missing_ldap_passcodes = audit.get("missing_ldap_passcodes") or []
        if missing_ldap_passcodes:
            headers["X-Missing-LDAP-Passcode"] = ", ".join(missing_ldap_passcodes)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers=headers,
        )

    except ValueError as e:
        logger.exception("Value error during Google export")
        return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "bad_request"})
    except KeyError as e:
        logger.exception("Missing column during Google export")
        return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "missing_columns"})
    except Exception:
        logger.exception("Unexpected error during Google export")
        return JSONResponse(status_code=500, content={"detail": "Unexpected server error", "error_code": "internal_error"})
