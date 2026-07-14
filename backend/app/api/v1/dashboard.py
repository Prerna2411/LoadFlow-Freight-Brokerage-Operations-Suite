from fastapi import APIRouter

from backend.app.main import dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

__all__ = ["router", "dashboard"]
