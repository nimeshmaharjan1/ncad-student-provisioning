from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import zipfile
from app.services.quercus_transform import transform_quercus
from app.services.export_pipeline import run_export_pipeline
from app.utils.date_utils import date_suffix
from app.utils.df_utils import sanitize_records

router = APIRouter()

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
        "ldap_preview": sanitize_records(ldap_df.head(3)),
        "canvas_preview": sanitize_records(canvas_df.head(3)),
        "athens_preview": sanitize_records(athens_df.head(3)),
        "library_preview": sanitize_records(library_df.head(3))
    }

@router.post("/bundle")
async def export_bundle(file: UploadFile = File(...)):
    contents = await file.read()
    
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    
    # Run the full export pipeline
    ldap_df, canvas_df, athens_df, library_df = run_export_pipeline(df)
    
    ds = date_suffix()

    # Package into a zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(f"{ds}_ldap.csv", ldap_df.to_csv(index=False))
        zip_file.writestr(f"{ds}_canvas.csv", canvas_df.to_csv(index=False))
        zip_file.writestr(f"{ds}_athens.csv", athens_df.to_csv(index=False))
        zip_file.writestr(f"{ds}_library.csv", library_df.to_csv(index=False))
        
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={ds}_quercus_exports.zip"}
    )


