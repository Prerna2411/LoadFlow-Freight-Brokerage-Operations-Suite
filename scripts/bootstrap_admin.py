"""Bootstrap is exposed by POST /api/v1/bootstrap/admin.

Example:
curl -X POST http://localhost:8000/api/v1/bootstrap/admin \
  -H "Content-Type: application/json" \
  -d '{"organization_name":"Acme Brokerage","organization_type":"broker","name":"Admin","email":"admin@example.com","password":"Password123"}'
"""

print(__doc__)
