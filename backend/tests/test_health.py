def test_healthcheck_returns_ok(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"
    assert response.json()["data"]["service"] == "core-community-backend"
