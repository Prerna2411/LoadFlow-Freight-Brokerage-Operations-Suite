from fastapi import APIRouter

from backend.app.main import create_shipper, create_staff, list_shippers

router = APIRouter(prefix="/users", tags=["users"])

__all__ = ["router", "create_staff", "create_shipper", "list_shippers"]
