import pandas as pd
from fastapi import APIRouter, UploadFile, File
import io

router = APIRouter()

@router.post("/upload")
async def upload_quercus(file: UploadFile = File(...)):
    contents = await file.read()

    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

    return {
        "rows": len(df),
        "columns": list(df.columns)
    }