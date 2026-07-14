from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def token(email: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_shipper_cannot_list_audit_log():
    response = client.get("/api/v1/audit", headers={"Authorization": f"Bearer {token('shipper@loadflow.test')}"})

    assert response.status_code == 403


def test_carrier_sees_only_assigned_loads():
    response = client.get("/api/v1/loads", headers={"Authorization": f"Bearer {token('driver@loadflow.test')}"})

    assert response.status_code == 200
    assert all(load["carrier"] == "Northstar Carrier" for load in response.json())
