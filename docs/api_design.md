# API Design

Base URL: `/api/v1`

- `POST /auth/login` returns a JWT and user permissions.
- `POST /bootstrap/admin` creates the first broker or carrier admin only when none exists for that account type.
- `GET /permissions` returns the fixed permission catalog.
- `GET/POST /roles` lists and creates organization-scoped custom roles.
- `POST /users/staff` creates staff inside the caller's organization.
- `GET/POST /loads` lists scoped loads and creates broker loads.
- `POST /loads/{id}/assign-carrier` assigns a carrier and auto-checks compliance.
- `POST /loads/{id}/override-compliance` requires `load.override_compliance_flag`.
- `POST /loads/{id}/status` advances the state machine.
- `POST /loads/{id}/rate-confirmations` creates the next rate confirmation version.
- `GET /rates/{load_id}` returns all versions visible to the caller.
- `GET/POST /compliance` manages carrier compliance records.
- `POST /pod/{load_id}` uploads POD after delivery.
- `POST /pod/{load_id}/verify` lets broker users verify POD.
- `GET /dashboard` returns dashboard counts and alerts.
- `GET /audit` returns organization audit events.
