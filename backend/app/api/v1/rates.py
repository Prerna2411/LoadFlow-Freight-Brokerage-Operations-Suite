from fastapi import APIRouter

from backend.app.main import confirm_rate, rate_versions

router = APIRouter(prefix="/rates", tags=["rates"])

__all__ = ["router", "confirm_rate", "rate_versions"]
