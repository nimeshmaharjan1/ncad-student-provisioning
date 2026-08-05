import io
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.services.library_staff_service import build_library_staff_rows
from app.utils.date_utils import date_suffix

logger = logging.getLogger(__name__)
router = APIRouter()


class LibraryStaffPerson(BaseModel):
    name: str
    barcode: str = ""
    gender: str = ""
    registration_date: str = ""
    expiration_date: str = ""


class LibraryStaffRequest(BaseModel):
    people: list[LibraryStaffPerson] = Field(default_factory=list)


def _rows_or_exception(request: LibraryStaffRequest):
    return build_library_staff_rows(
        [
            (
                person.name,
                person.barcode,
                person.gender,
                person.registration_date,
                person.expiration_date,
            )
            for person in request.people
        ]
    )


@router.post("/generate")
async def generate_library_staff(request: LibraryStaffRequest):
    """Return the generated library staff rows as JSON (for the preview table)."""
    try:
        df, warnings = _rows_or_exception(request)
        if df.empty:
            raise ValueError("At least one staff member is required.")
        return {"rows": df.to_dict(orient="records"), "count": len(df), "warnings": warnings}
    except ValueError as e:
        logger.warning("Library staff generation rejected: %s", e)
        return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "bad_request"})
    except Exception:
        logger.exception("Unexpected error during library staff generation")
        return JSONResponse(status_code=500, content={"detail": "Unexpected server error", "error_code": "internal_error"})


@router.post("/export")
async def export_library_staff(request: LibraryStaffRequest):
    """Download the generated library staff rows as a CSV file (for review)."""
    try:
        df, _ = _rows_or_exception(request)
        if df.empty:
            raise ValueError("At least one staff member is required.")
        ds = date_suffix()
        csv_buffer = io.BytesIO(df.to_csv(index=False).encode("utf-8"))
        return StreamingResponse(
            csv_buffer,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{ds}_library.csv"'},
        )
    except ValueError as e:
        logger.warning("Library staff export rejected: %s", e)
        return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "bad_request"})
    except Exception:
        logger.exception("Unexpected error during library staff export")
        return JSONResponse(status_code=500, content={"detail": "Unexpected server error", "error_code": "internal_error"})


@router.post("/export-text")
async def export_library_staff_text(request: LibraryStaffRequest):
    """Download the generated library staff rows as a tab-delimited .txt file.

    This is the file uploaded via SFTP — dates stay in YYYY-MM-DD form, so
    unlike a CSV it is not affected by spreadsheet clients' date defaults.
    """
    try:
        df, _ = _rows_or_exception(request)
        if df.empty:
            raise ValueError("At least one staff member is required.")
        ds = date_suffix()
        txt_buffer = io.BytesIO(df.to_csv(sep="\t", index=False).encode("utf-8"))
        return StreamingResponse(
            txt_buffer,
            media_type="text/tab-separated-values",
            headers={"Content-Disposition": f'attachment; filename="{ds}library.txt"'},
        )
    except ValueError as e:
        logger.warning("Library staff text export rejected: %s", e)
        return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "bad_request"})
    except Exception:
        logger.exception("Unexpected error during library staff text export")
        return JSONResponse(status_code=500, content={"detail": "Unexpected server error", "error_code": "internal_error"})