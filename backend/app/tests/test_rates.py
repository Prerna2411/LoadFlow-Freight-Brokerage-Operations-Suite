from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_rate_versions_endpoint_is_scoped_and_available():
    login = client.post("/api/v1/auth/login", json={"email": "broker.admin@loadflow.test", "password": "Password123"})
    token = login.json()["access_token"]
    loads = client.get("/api/v1/loads", headers={"Authorization": f"Bearer {token}"}).json()

    response = client.get(f"/api/v1/rates/{loads[0]['id']}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
