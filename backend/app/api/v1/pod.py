from fastapi import APIRouter

from backend.app.main import upload_pod, verify_pod

router = APIRouter(prefix="/pod", tags=["pod"])

__all__ = ["router", "upload_pod", "verify_pod"]
