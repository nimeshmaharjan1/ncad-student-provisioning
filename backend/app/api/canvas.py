import os
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import zipfile
from app.services.quercus_preprocess import preprocess_quercus
from app.services.canvas_service import generate_canvas_comparison_exports
from app.utils.date_utils import date_suffix

router = APIRouter()


@router.post("/export")
async def export_canvas(baseline: UploadFile = File(...), quercus: UploadFile = File(...)):
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

    new_users_df, updated_baseline_df, _ = generate_canvas_comparison_exports(baseline_df, cleaned_quercus_df)

    ds = date_suffix()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{ds}_canvas.csv", new_users_df.to_csv(index=False))
        zf.writestr(f"{ds}_canvas_all_pre.csv", updated_baseline_df.to_csv(index=False))
    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=\"{ds}_canvas_export.zip\""},
    )
