# LoadFlow

LoadFlow is a take-home implementation of a freight brokerage operations suite. It uses FastAPI, SQLAlchemy 2.0, SQLite, React 19, Vite, and TypeScript because that stack is quick to run locally while still making API-layer RBAC and object scoping explicit.

## What Works

- Auth for broker org users, carrier org users, and shippers.
- Bootstrap endpoint for the first broker/carrier admin; staff are created later by users with `staff.manage`.
- Fixed permission catalog with admin-created custom roles. Server code checks permissions, not role names.
- Role assignment is represented by `user_roles`; `role_id` is retained only as a convenience pointer for single-role UI display.
- API-layer org and object scoping for broker, carrier, and shipper users.
- Permission-denied attempts are printed and stored in the audit log.
- Load CRUD, broker search/filter, state transitions, timestamped audit entries.
- Carrier compliance records with insurance, authority, equipment, and commodity checks.
- Compliance flags block rate confirmation and progression beyond `Carrier Assigned` until overridden.
- Versioned rate confirmations; the load stores the confirmed version it is using.
- Broker, carrier, and shipper dashboards in one React app.
- Stretch coverage: POD upload/view links, POD verification, compliance expiry alert data, audit log endpoint, audit log viewer, and load status history viewer.

## Run Locally

Backend:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn backend.app.main:app --reload
```

If your deployment service uses `backend/` as the root directory, use `backend/requirements.txt`; it points back to the same dependency list.

If Uvicorn fails during seed data with a `passlib` / `bcrypt` traceback, your environment has an incompatible `bcrypt` version. Repair it with:

```bash
pip install --force-reinstall bcrypt==4.0.1 passlib==1.7.4
```

On PowerShell, if `npm run ...` is blocked by script policy, use `npm.cmd`:

```bash
npm.cmd run dev
npm.cmd run build
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The API runs at `http://localhost:8000`.

If you already created a local SQLite database from an earlier iteration, remove `loadflow.db` once before running so the current table names are created fresh:

```bash
del loadflow.db
```

For an existing database you want to keep, mark it as migrated instead:

```bash
alembic stamp head
```

## Demo Accounts

All seeded users use password `Password123`. Passwords are stored only as hashes in the `users.password_hash` column.

- Broker Admin: `broker.admin@loadflow.test`
- Broker Dispatcher: `dispatcher@loadflow.test`
- Broker Ops Lead: `ops.lead@loadflow.test`
- Broker Billing: `billing@loadflow.test`
- Carrier Admin: `carrier.admin@loadflow.test`
- Carrier Driver: `driver@loadflow.test`
- Carrier Dispatch: `carrier.dispatch@loadflow.test`
- Prairie POD Clerk: `prairie.pod@loadflow.test`
- Shipper: `shipper@loadflow.test`
- Evergreen Foods Shipper: `evergreen.foods@loadflow.test`
- Metro Retail Shipper: `metro.retail@loadflow.test`

## Seed Data

On startup, the app seeds a richer demo dataset if those rows are missing:

- 3 organizations: 1 broker and 2 carriers.
- 7 fixed permissions.
- 6 roles across broker and carrier organizations.
- 11 users across broker, carrier, and shipper account types.
- 2 carrier compliance records, including one lapsed carrier for compliance-blocking demos.
- 7 loads across Posted, Carrier Assigned, Rate Confirmed, In Transit, Delivered, and Invoiced/Closed states.
- Multiple load status history rows, rate confirmation versions, audit logs, notifications, and one seeded POD file.

## Bootstrap

The seed creates demo admins automatically. In a clean production database, create the first org admin with:

```bash
curl -X POST http://localhost:8000/api/v1/bootstrap/admin ^
  -H "Content-Type: application/json" ^
  -d "{\"organization_name\":\"Acme Brokerage\",\"organization_type\":\"broker\",\"name\":\"Admin\",\"email\":\"admin@example.com\",\"password\":\"Password123\"}"
```

After that, staff accounts are invited through `POST /api/v1/users/staff` by an admin or a role with `staff.manage`.

## Tests

```bash
pytest backend/app/tests
```

## Assumptions

- Shippers are individual accounts and have no roles.
- Broker users can list carrier organizations for assignment, but carrier users only see their own organization and assigned loads.
- Local POD storage is enough for the take-home; production would use object storage.
- Demo data is seeded on app start so the reviewer can run the app immediately.

## Incomplete / Next With More Time

- Add Alembic migration files instead of `create_all`.
- Add richer carrier accept/decline workflow before broker rate confirmation.
- Add signed file URLs and virus scanning for POD uploads.
- Add full frontend forms for POD file upload and audit log exploration.
- Add a CI pipeline and deploy manifests for Render/Vercel.
