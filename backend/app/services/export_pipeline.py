import pandas as pd
from app.services.quercus_transform import transform_quercus
from app.services.ldap_service import generate_ldap_export
from app.services.canvas_service import generate_canvas_export
from app.services.athens_service import generate_athens_export
from app.services.library_service import generate_library_export

def run_export_pipeline(df: pd.DataFrame):
    """
    Runs the complete export pipeline on a raw Quercus DataFrame.
    
    1. Runs the transform_quercus function.
    2. Generates downstream system-specific DataFrames:
       - LDAP
       - Canvas
       - Athens
       - Library
       
    Returns:
        tuple: (ldap_df, canvas_df, athens_df, library_df)
    """
    cleaned_df = transform_quercus(df)

    ldap_df = generate_ldap_export(cleaned_df)
    canvas_df = generate_canvas_export(cleaned_df)
    athens_df = generate_athens_export(cleaned_df)
    library_df = generate_library_export(cleaned_df)

    return ldap_df, canvas_df, athens_df, library_df
