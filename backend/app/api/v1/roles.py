from fastapi import APIRouter

from backend.app.main import create_role, list_roles

router = APIRouter(prefix="/roles", tags=["roles"])

__all__ = ["router", "create_role", "list_roles"]
