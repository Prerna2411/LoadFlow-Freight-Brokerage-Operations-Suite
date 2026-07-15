from fastapi import APIRouter

from backend.app.api.v1 import audit, auth, compliance, dashboard, loads, organizations, permissions, pod, rates, roles, users

api_router = APIRouter(prefix="/api/v1")

ROUTE_MODULES = [
    auth,
    users,
    organizations,
    roles,
    permissions,
    loads,
    compliance,
    rates,
    dashboard,
    pod,
    audit,
]


def registered_modules() -> list[str]:
    return [module.__name__.split(".")[-1] for module in ROUTE_MODULES]


__all__ = ["ROUTE_MODULES", "api_router", "registered_modules"]
