"""Unit tests for FastAPI endpoints using TestClient."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data


def test_auth_me_endpoint():
    response = client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert "authenticated" in data


def test_metrics_endpoints():
    # Register a metric
    payload = {
        "name": "average_order_value",
        "target_table": "orders",
        "formula": "amount / order_count",
        "sql_expression": "AVG(amount)",
        "unit": "currency",
        "description": "Average order amount",
        "synonyms": ["aov"],
    }
    create_resp = client.post("/metrics", json=payload)
    assert create_resp.status_code in (200, 201)

    # List metrics
    list_resp = client.get("/metrics")
    assert list_resp.status_code == 200
    metrics = list_resp.json()["metrics"]
    assert any(m["name"] == "average_order_value" for m in metrics)


def test_conversations_endpoint():
    create_resp = client.post("/conversations", json={"title": "Q3 Performance"})
    assert create_resp.status_code == 201
    conv = create_resp.json()
    assert "id" in conv

    get_resp = client.get(f"/conversations/{conv['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == conv["id"]


def test_dataquery_execute_sql_safety():
    # Attempt to execute forbidden non-SELECT SQL
    resp = client.post(
        "/api/dataquery/execute-sql",
        json={"sql": "DROP TABLE users;", "table_name": "users"},
    )
    assert resp.status_code == 422
    assert "safety" in resp.json().get("detail", "").lower() or "validation" in resp.json().get("detail", "").lower()

