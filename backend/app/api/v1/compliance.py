from fastapi import APIRouter

from backend.app.main import delete_compliance, list_compliance, upsert_compliance

router = APIRouter(prefix="/compliance", tags=["compliance"])

__all__ = ["router", "list_compliance", "upsert_compliance", "delete_compliance"]
