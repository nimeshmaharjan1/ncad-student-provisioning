from datetime import datetime
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from app.services.library_service import generate_library_export

router = APIRouter()


@router.post("/export")
async def export_library(files: list[UploadFile] = File(...)):
    dfs = []
    for f in files:
        contents = await f.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        df.columns = df.columns.str.strip()
        dfs.append(df)

    library_df = generate_library_export(*dfs)

    date_suffix = datetime.now().strftime("%Y%m%d")
    filename = f"{date_suffix}_library.csv"

    csv_content = library_df.to_csv(index=False)

    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )
