from fastapi import APIRouter, UploadFile, File
import pandas as pd
import io
from app.services.ldap_export import generate_ldap_comparison_exports
from app.services.quercus_preprocess import preprocess_quercus

router = APIRouter()

@router.post("/export")
async def export_ldap(baseline: UploadFile = File(...), quercus: UploadFile = File(...)):
    # This endpoint represents the official LDAP provisioning pipeline and is separate from Quercus preprocessing.
    baseline_contents = await baseline.read()
    quercus_contents = await quercus.read()

    baseline_df = pd.read_csv(io.StringIO(baseline_contents.decode("utf-8")))
    quercus_df = pd.read_csv(io.StringIO(quercus_contents.decode("utf-8")))

    baseline_df.columns = baseline_df.columns.str.strip()
    quercus_df.columns = quercus_df.columns.str.strip()

    cleaned_quercus_df = preprocess_quercus(quercus_df)

    new_students_df, updated_baseline_df, audit_info = generate_ldap_comparison_exports(baseline_df, cleaned_quercus_df)

    def sanitize_df(df: pd.DataFrame) -> list:
        records = df.to_dict(orient="records")
        for row in records:
            for key, val in row.items():
                if pd.isna(val):
                    row[key] = None
        return records

    return {
        "new_students": sanitize_df(new_students_df),
        "updated_baseline": sanitize_df(updated_baseline_df),
        "audit_info": {
            "new_students_count": audit_info["new_students_count"],
            "updated_baseline_count": audit_info["updated_baseline_count"]
        }
    }
