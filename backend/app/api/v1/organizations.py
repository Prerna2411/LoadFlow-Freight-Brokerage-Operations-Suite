from fastapi import APIRouter

from backend.app.main import organizations

router = APIRouter(prefix="/organizations", tags=["organizations"])

__all__ = ["router", "organizations"]
