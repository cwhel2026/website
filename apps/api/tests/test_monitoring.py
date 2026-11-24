from fastapi import FastAPI
from starlette.testclient import TestClient

from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers.health import health


def test_health_payload_version():
    payload = __import__("asyncio").run(health())
    assert payload["version"] == "0.7.0"
    assert payload["status"] == "ok"


def _mini_app() -> FastAPI:
    mini = FastAPI()
    mini.add_middleware(RequestIdMiddleware)
    mini.add_middleware(SecurityHeadersMiddleware)

    @mini.get("/health")
    def ping():
        return {"status": "ok"}

    return mini


def test_security_headers():
    with TestClient(_mini_app()) as client:
        response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Request-ID")


def test_request_id_echoed():
    with TestClient(_mini_app()) as client:
        response = client.get("/health", headers={"X-Request-ID": "test-req-123"})
    assert response.headers.get("X-Request-ID") == "test-req-123"