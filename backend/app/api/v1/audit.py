from fastapi import APIRouter

from backend.app.main import audit

router = APIRouter(prefix="/audit", tags=["audit"])

__all__ = ["router", "audit"]
