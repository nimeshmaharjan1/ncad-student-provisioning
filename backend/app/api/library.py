import zipfile
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from app.services.library_service import clean_library_data, build_library_template
from app.utils.date_utils import date_suffix

router = APIRouter()


@router.post("/export")
async def export_library(files: list[UploadFile] = File(...)):
    dfs = []
    for f in files:
        contents = await f.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        df.columns = df.columns.str.strip()
        dfs.append(df)

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
