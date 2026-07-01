from fastapi import APIRouter
from app.api import quercus, ldap, google, canvas, library, athens

router = APIRouter()

router.include_router(quercus.router, prefix="/quercus")
router.include_router(ldap.router, prefix="/ldap")
router.include_router(google.router, prefix="/google")
router.include_router(canvas.router, prefix="/canvas")
router.include_router(library.router, prefix="/library")
router.include_router(athens.router, prefix="/athens")