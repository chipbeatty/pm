from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_hello_api_returns_message() -> None:
    response = client.get("/api/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello from FastAPI!"}


def test_root_serves_static_page() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Hello, world" in response.text
    assert 'fetch("/api/hello")' in response.text
