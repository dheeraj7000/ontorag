"""Health check and basic API tests."""


def test_health_endpoint(client):
    """Health check returns ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ontorag"
    assert data["version"] == "0.1.0"


def test_docs_available(client):
    """OpenAPI docs should be accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_ingest_rejects_invalid_file_type(client):
    """Ingest endpoint rejects unsupported file types."""
    response = client.post(
        "/api/v1/ingest/",
        files={"file": ("test.exe", b"fake content", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_ingest_accepts_markdown(client):
    """Ingest endpoint accepts markdown files."""
    content = b"# Test Document\n\nThis is a test."
    response = client.post(
        "/api/v1/ingest/",
        files={"file": ("test.md", content, "text/markdown")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["size_bytes"] == len(content)


def test_query_endpoint_exists(client):
    """Query endpoint responds (stub for now)."""
    response = client.post(
        "/api/v1/query/",
        json={"question": "What is FastAPI?"},
    )
    assert response.status_code == 200


def test_graph_stats_endpoint(client):
    """Graph stats endpoint responds."""
    response = client.get("/api/v1/graph/stats")
    assert response.status_code == 200


def test_hallucination_check_endpoint(client):
    """Hallucination check endpoint responds."""
    response = client.post(
        "/api/v1/hallucination/check",
        json={"answer": "FastAPI uses Django under the hood."},
    )
    assert response.status_code == 200
