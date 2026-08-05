import logging
import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from app.services.canvas_staff_service import build_canvas_staff_rows
from app.utils.date_utils import date_suffix

logger = logging.getLogger(__name__)
router = APIRouter()


class CanvasStaffRequest(BaseModel):
    names: list[str] = Field(default_factory=list)


@router.post("/generate")
async def generate_canvas_staff(request: CanvasStaffRequest):
    """Return the generated Canvas staff rows as JSON (for the preview table)."""
    try:
        df, warnings = build_canvas_staff_rows(request.names)
        if df.empty:
            raise ValueError("At least one staff name is required.")
        return {"rows": df.to_dict(orient="records"), "count": len(df), "warnings": warnings}
    except ValueError as e:
        logger.warning("Canvas staff generation rejected: %s", e)
        return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "bad_request"})
    except Exception:
        logger.exception("Unexpected error during Canvas staff generation")
        return JSONResponse(status_code=500, content={"detail": "Unexpected server error", "error_code": "internal_error"})


@router.post("/export")
async def export_canvas_staff(request: CanvasStaffRequest):
    """Download the generated Canvas staff rows as a CSV file."""
    try:
        df, _ = build_canvas_staff_rows(request.names)
        if df.empty:
            raise ValueError("At least one staff name is required.")
        ds = date_suffix()
        csv_buffer = io.BytesIO(df.to_csv(index=False).encode("utf-8"))
        return StreamingResponse(
            csv_buffer,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{ds}_canvas_staff.csv"'},
        )
    except ValueError as e:
        logger.warning("Canvas staff export rejected: %s", e)
        return JSONResponse(status_code=400, content={"detail": str(e), "error_code": "bad_request"})
    except Exception:
        logger.exception("Unexpected error during Canvas staff export")
        return JSONResponse(status_code=500, content={"detail": "Unexpected server error", "error_code": "internal_error"})
