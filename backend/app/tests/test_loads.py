from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_broker_load_board_search():
    login = client.post("/api/v1/auth/login", json={"email": "broker.admin@loadflow.test", "password": "Password123"})
    token = login.json()["access_token"]

    response = client.get("/api/v1/loads", headers={"Authorization": f"Bearer {token}"}, params={"q": "Chicago"})

    assert response.status_code == 200
    assert any("Chicago" in load["origin"] for load in response.json())
