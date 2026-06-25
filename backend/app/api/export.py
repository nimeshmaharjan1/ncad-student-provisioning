from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import zipfile
from app.services.quercus_transform import transform_quercus
from app.services.export_pipeline import run_export_pipeline

router = APIRouter()

def sanitize_preview(df: pd.DataFrame) -> list:
    """Converts the first 3 rows of a DataFrame to records, mapping NaNs to None for JSON compliance."""
    sample_df = df.head(3)
    records = sample_df.to_dict(orient="records")
    for row in records:
        for key, val in row.items():
            if pd.isna(val):
                row[key] = None
    return records

@router.post("/all")
async def export_all(file: UploadFile = File(...)):
    contents = await file.read()
    
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    
    # Run the full export pipeline
    ldap_df, canvas_df, athens_df, library_df = run_export_pipeline(df)
    
    # We need the cleaned row count. Since all downstream dataframes have the same row count
    # (except for status-based filters, but since the pipeline uses the cleaned dataframe,
    # we can use any of them, or count them directly).
    # Wait, the number of cleaned rows is the size of the output dataframes (they are projections).
    cleaned_row_count = len(ldap_df)
    
    return {
        "raw_row_count": len(df),
        "cleaned_row_count": cleaned_row_count,
        "ldap_preview": sanitize_preview(ldap_df),
        "canvas_preview": sanitize_preview(canvas_df),
        "athens_preview": sanitize_preview(athens_df),
        "library_preview": sanitize_preview(library_df)
    }

@router.post("/bundle")
async def export_bundle(file: UploadFile = File(...)):
    contents = await file.read()
    
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    
    # Run the full export pipeline
    ldap_df, canvas_df, athens_df, library_df = run_export_pipeline(df)
    
    # Package into a zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("ldap.csv", ldap_df.to_csv(index=False))
        zip_file.writestr("canvas.csv", canvas_df.to_csv(index=False))
        zip_file.writestr("athens.csv", athens_df.to_csv(index=False))
        zip_file.writestr("library.csv", library_df.to_csv(index=False))
        
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=quercus_exports.zip"}
    )


