# Database Schema

SQLite tables are created by SQLAlchemy on startup for the take-home demo.

| Table | Purpose |
| --- | --- |
| `organizations` | Broker and carrier organizations |
| `users` | Broker staff, carrier staff, and shipper accounts |
| `permissions` | Fixed permission catalog |
| `roles` | Admin-created organization-scoped roles |
| `role_permissions` | Permissions assigned to roles |
| `user_roles` | Roles assigned to users |
| `carrier_compliance` | Insurance, authority, equipment, and commodity compliance |
| `loads` | Main shipment/load records |
| `load_status_history` | Workflow state history with timestamps and actor |
| `rate_confirmation_versions` | Versioned broker-carrier rate agreements |
| `pod_files` | Proof of Delivery upload metadata |
| `audit_logs` | Activity and permission-denied logs |
| `notifications` | Renewal and system notifications |

If you previously ran an older local version, delete `loadflow.db` before restarting so SQLite is recreated with this schema.
