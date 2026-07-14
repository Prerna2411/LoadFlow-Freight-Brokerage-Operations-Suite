from fastapi import APIRouter

from backend.app.api.v1 import audit, auth, compliance, dashboard, loads, organizations, permissions, pod, rates, roles, users

api_router = APIRouter()

# Routes are registered in backend.app.main for the take-home runnable app.
# These module imports keep the planned architecture discoverable and reusable.
ROUTE_MODULES = [auth, users, organizations, roles, permissions, loads, compliance, rates, dashboard, pod, audit]
