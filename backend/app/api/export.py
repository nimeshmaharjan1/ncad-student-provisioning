from fastapi import APIRouter, UploadFile, File
import pandas as pd
import io
from app.services.quercus_transform import transform_quercus
from app.services.ldap_service import generate_ldap_export
from app.services.canvas_service import generate_canvas_export
from app.services.athens_service import generate_athens_export
from app.services.library_service import generate_library_export

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
    
    cleaned_df = transform_quercus(df)
    
    # Generate individual system exports
    ldap_df = generate_ldap_export(cleaned_df)
    canvas_df = generate_canvas_export(cleaned_df)
    athens_df = generate_athens_export(cleaned_df)
    library_df = generate_library_export(cleaned_df)
    
    return {
        "raw_row_count": len(df),
        "cleaned_row_count": len(cleaned_df),
        "ldap_preview": sanitize_preview(ldap_df),
        "canvas_preview": sanitize_preview(canvas_df),
        "athens_preview": sanitize_preview(athens_df),
        "library_preview": sanitize_preview(library_df)
    }
