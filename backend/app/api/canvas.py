from datetime import datetime
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import zipfile
from app.services.quercus_preprocess import preprocess_quercus
from app.services.canvas_service import generate_canvas_comparison_exports

router = APIRouter()


@router.post("/export")
async def export_canvas(baseline: UploadFile = File(...), quercus: UploadFile = File(...)):
    baseline_contents = await baseline.read()
    quercus_contents = await quercus.read()

    baseline_df = pd.read_csv(io.StringIO(baseline_contents.decode("utf-8")))
    quercus_df = pd.read_csv(io.StringIO(quercus_contents.decode("utf-8")))

    baseline_df.columns = baseline_df.columns.str.strip()
    quercus_df.columns = quercus_df.columns.str.strip()

    cleaned_quercus_df = preprocess_quercus(quercus_df)

    new_users_df, updated_baseline_df, _ = generate_canvas_comparison_exports(baseline_df, cleaned_quercus_df)

    date_suffix = datetime.now().strftime("%Y%m%d")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{date_suffix}_canvas.csv", new_users_df.to_csv(index=False))
        zf.writestr(f"canvas_all_pre_{date_suffix}.csv", updated_baseline_df.to_csv(index=False))
    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=\"canvas_export_{date_suffix}.zip\""},
    )
