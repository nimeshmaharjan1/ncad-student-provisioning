import os
from fastapi import APIRouter, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import zipfile
from app.services.ldap_export import generate_ldap_comparison_exports
from app.services.quercus_preprocess import preprocess_quercus

router = APIRouter()

@router.post("/export")
async def export_ldap(baseline: UploadFile = File(...), quercus: UploadFile = File(...)):
    # This endpoint represents the official LDAP provisioning pipeline and is separate from Quercus preprocessing.
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

    cleaned_quercus_df = preprocess_quercus(quercus_df)

    new_students_df, updated_baseline_df, audit_info = generate_ldap_comparison_exports(baseline_df, cleaned_quercus_df)

    def sanitize_df(df: pd.DataFrame) -> list:
        records = df.to_dict(orient="records")
        for row in records:
            for key, val in row.items():
                if pd.isna(val):
                    row[key] = None
        return records

    return {
        "new_students": sanitize_df(new_students_df),
        "updated_baseline": sanitize_df(updated_baseline_df),
        "audit_info": {
            "new_students_count": audit_info["new_students_count"],
            "updated_baseline_count": audit_info["updated_baseline_count"]
        }
    }


@router.post("/download")
async def download_ldap(
    baseline: UploadFile = File(...),
    quercus: UploadFile = File(...),
    format: str = "zip",
    new_students_filename: str | None = Form(None),
    updated_baseline_filename: str | None = Form(None),
):
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

    cleaned_quercus_df = preprocess_quercus(quercus_df)

    new_students_df, updated_baseline_df, _ = generate_ldap_comparison_exports(baseline_df, cleaned_quercus_df)

    def _ensure_csv(name: str) -> str:
        return name if name.lower().endswith(".csv") else name + ".csv"

    new_fn = _ensure_csv(new_students_filename) if new_students_filename else "new_students.csv"
    upd_fn = _ensure_csv(updated_baseline_filename) if updated_baseline_filename else "updated_baseline.csv"

    if format == "zip":
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(new_fn, new_students_df.to_csv(index=False))
            zf.writestr(upd_fn, updated_baseline_df.to_csv(index=False))
        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=\"ldap_export.zip\""}
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
        headers={"Content-Disposition": "attachment; filename=\"ldap_export.csv\""}
    )