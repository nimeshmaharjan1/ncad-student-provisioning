import pandas as pd
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import io
from app.services.quercus_preprocess import preprocess_quercus

router = APIRouter()

@router.post("/upload")
async def upload_quercus(file: UploadFile = File(...)):
    contents = await file.read()

    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    df.columns = df.columns.str.strip()
    
    cleaned_df = preprocess_quercus(df)

    # Convert head(10) to dictionary, replacing NaN/nulls with None for standard JSON serialization
    sample_rows = cleaned_df.head(10).to_dict(orient="records")
    for row in sample_rows:
        for key, val in row.items():
            if pd.isna(val):
                row[key] = None

    return {
        "raw_row_count": len(df),
        "cleaned_row_count": len(cleaned_df),
        "filtered_out_status_count": cleaned_df.attrs.get("filtered_out_status_count", 0),
        "external_students_removed_count": cleaned_df.attrs.get("external_students_removed_count", 0),
        "duplicate_rows_detected": cleaned_df.attrs.get("duplicate_rows_detected", 0),
        "sample_rows": sample_rows
    }

@router.post("/download")
async def download_quercus(file: UploadFile = File(...)):
    contents = await file.read()

    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    df.columns = df.columns.str.strip()
    
    cleaned_df = preprocess_quercus(df)

    # Convert cleaned DataFrame to CSV string
    stream = io.StringIO()
    cleaned_df.to_csv(stream, index=False)
    response_content = stream.getvalue()

    # Create response with headers to force file download
    return StreamingResponse(
        io.BytesIO(response_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=\"quercus_cleaned.csv\""}
    )