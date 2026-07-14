from fastapi import APIRouter

from backend.app.main import permissions

router = APIRouter(prefix="/permissions", tags=["permissions"])

__all__ = ["router", "permissions"]
