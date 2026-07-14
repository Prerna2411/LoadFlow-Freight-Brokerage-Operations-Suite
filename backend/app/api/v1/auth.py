from fastapi import APIRouter

from backend.app.main import bootstrap_admin, login, me

router = APIRouter(prefix="/auth", tags=["auth"])

__all__ = ["router", "login", "me", "bootstrap_admin"]
