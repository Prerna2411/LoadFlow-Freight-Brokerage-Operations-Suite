from fastapi.testclient import TestClient
from uuid import uuid4

from backend.app.main import app


client = TestClient(app)


def token(email: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_compliance_blocks_rate_confirmation_on_flagged_load():
    broker_token = token("broker.admin@loadflow.test")
    shipper = client.get("/api/v1/users/shippers", headers={"Authorization": f"Bearer {broker_token}"}).json()[0]
    load = client.post(
        "/api/v1/loads",
        headers={"Authorization": f"Bearer {broker_token}"},
        json={
            "reference": f"LF-FLAG-{uuid4().hex[:8]}",
            "shipper_user_id": shipper["id"],
            "origin": "Akron, OH",
            "destination": "Austin, TX",
            "equipment_type": "Flatbed",
            "commodity": "Steel",
        },
    ).json()
    carriers = client.get("/api/v1/organizations", headers={"Authorization": f"Bearer {broker_token}"}, params={"type": "carrier"}).json()
    assigned = client.post(
        f"/api/v1/loads/{load['id']}/assign-carrier",
        headers={"Authorization": f"Bearer {broker_token}"},
        json={"carrier_org_id": carriers[0]["id"]},
    ).json()

    assert assigned["compliance_flag"] is True
    response = client.post(
        f"/api/v1/loads/{load['id']}/rate-confirmations",
        headers={"Authorization": f"Bearer {broker_token}"},
        json={"base_rate": 2500, "accessorials": []},
    )
    assert response.status_code == 409
