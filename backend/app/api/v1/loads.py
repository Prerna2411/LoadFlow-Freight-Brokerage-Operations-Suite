from fastapi import APIRouter

from backend.app.main import assign_carrier, carrier_decision, create_load, delete_load, get_load, list_loads, load_audit, load_history, override_compliance, update_load, update_status

router = APIRouter(prefix="/loads", tags=["loads"])

__all__ = [
    "router",
    "list_loads",
    "create_load",
    "get_load",
    "update_load",
    "delete_load",
    "assign_carrier",
    "carrier_decision",
    "override_compliance",
    "update_status",
    "load_audit",
    "load_history",
]
