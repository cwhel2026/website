import base64
import json
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from app.services.google_workspace import WorkspaceClient, authorization_url


def test_authorization_uses_pkce_and_offline_access():
    query = parse_qs(urlparse(authorization_url(
        "client", "https://example.com/callback", "state", "challenge",
    )).query)
    assert query["state"] == ["state"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["access_type"] == ["offline"]


@pytest.mark.asyncio
async def test_workspace_transport():
    def handler(request):
        assert request.headers["Authorization"] == "Bearer test-token"
        payload = json.loads(request.content)
        if request.url.host == "gmail.googleapis.com":
            raw = base64.urlsafe_b64decode(payload["raw"])
            assert b"To: customer@example.com" in raw
            assert b"Booking confirmation" in raw
        elif request.url.host == "www.googleapis.com":
            assert payload["mimeType"] == "application/vnd.google-apps.folder"
        else:
            assert request.url.params["sendUpdates"] == "none"
            assert payload["summary"] == "Booking"
        return httpx.Response(200, json={"id": "test-id"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        workspace = WorkspaceClient(client, "test-token")
        assert (await workspace.send_email(
            "bookings@surfacecoat.co.uk", "customer@example.com",
            "Booking confirmation", "Test",
        ))["id"] == "test-id"
        assert (await workspace.create_calendar_event({"summary": "Booking"}))["id"] == "test-id"
        assert (await workspace.create_drive_folder("Customer"))["id"] == "test-id"
