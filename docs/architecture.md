# Architecture

LoadFlow is split into a FastAPI backend and a React/Vite frontend.

The backend keeps the interview-critical logic server-side:

- JWT authentication identifies the user.
- `PERMISSION_CATALOG` is fixed; roles are organization-owned bundles of permission rows.
- Admins receive all permissions by bootstrap, while staff permissions come only from their role.
- Broker, carrier, and shipper scoping is enforced in `load_for_user`.
- Compliance is recomputed when a carrier is assigned or a compliance record changes.
- Load status transitions are centralized in `transition`.
- Audit events record load changes, role/staff creation, compliance changes, rate confirmation, POD activity, and denied attempts.

The frontend is a reviewer-friendly operations console. It does not contain security decisions; it calls the same protected APIs a direct client would use.
