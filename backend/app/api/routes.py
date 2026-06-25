from fastapi import APIRouter
from app.api import quercus, export

router = APIRouter()

router.include_router(quercus.router, prefix="/quercus")
router.include_router(export.router, prefix="/export")