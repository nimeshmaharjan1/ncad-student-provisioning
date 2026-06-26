from fastapi import APIRouter
from app.api import quercus, export, ldap, google

router = APIRouter()

router.include_router(quercus.router, prefix="/quercus")
router.include_router(export.router, prefix="/export")
router.include_router(ldap.router, prefix="/ldap")
router.include_router(google.router, prefix="/google")