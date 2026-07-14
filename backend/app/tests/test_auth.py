from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_demo_login_returns_permissions():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "broker.admin@loadflow.test", "password": "Password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert "staff.manage" in body["user"]["permissions"]
