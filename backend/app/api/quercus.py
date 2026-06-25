import pandas as pd
from fastapi import APIRouter, UploadFile, File
import io
from app.services.quercus_transform import transform_quercus

router = APIRouter()

@router.post("/upload")
async def upload_quercus(file: UploadFile = File(...)):
    contents = await file.read()

    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    
    cleaned_df = transform_quercus(df)

    # Convert head(3) to dictionary, replacing NaN/nulls with None for standard JSON serialization
    sample_rows = cleaned_df.head(3).to_dict(orient="records")
    for row in sample_rows:
        for key, val in row.items():
            if pd.isna(val):
                row[key] = None

    return {
        "raw_row_count": len(df),
        "cleaned_row_count": len(cleaned_df),
        "sample_rows": sample_rows
    }