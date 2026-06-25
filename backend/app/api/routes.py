from fastapi import APIRouter
from app.api import quercus

router = APIRouter()

router.include_router(quercus.router, prefix="/quercus")