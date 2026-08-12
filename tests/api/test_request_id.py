from fastapi.testclient import TestClient


def test_generates_request_id_when_absent(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.headers["x-request-id"]


def test_echoes_caller_supplied_request_id(client: TestClient) -> None:
    response = client.get("/healthz", headers={"X-Request-ID": "trace-me-123"})

    assert response.headers["x-request-id"] == "trace-me-123"
