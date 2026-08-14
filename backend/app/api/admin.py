import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.core.settings import (
    VALID_SYSTEMS,
    get_all_validation_modes,
    set_validation_mode,
    source_of,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _settings_payload() -> dict:
    return {
        "systems": list(VALID_SYSTEMS),
        "modes": get_all_validation_modes(),
        "sources": {system: source_of(system) for system in VALID_SYSTEMS},
    }


@router.get("/settings")
async def get_settings():
    """Current effective validation modes for every system."""
    return _settings_payload()


@router.put("/settings")
async def update_settings(request: Request):
    """Persist per-system validation modes.

    Body shape: {"validation_modes": {"ldap": "warn", "canvas": "strict"}}
    Env vars still take precedence over the persisted file.
    """
    payload = await request.json()
    modes = payload.get("validation_modes") or payload.get("modes") or {}
    if not isinstance(modes, dict):
        return JSONResponse(
            status_code=400,
            content={"detail": "validation_modes must be an object"},
        )
    for system, mode in modes.items():
        try:
            set_validation_mode(str(system), str(mode))
        except ValueError as e:
            return JSONResponse(status_code=400, content={"detail": str(e)})
    return _settings_payload()
