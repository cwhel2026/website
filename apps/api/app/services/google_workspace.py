"""Google Workspace transport; callers must enforce approval and persist tokens securely."""
import base64
from email.message import EmailMessage
from urllib.parse import urlencode

import httpx

SCOPES = (
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/userinfo.email",
)
TOKEN_URL = "https://oauth2.googleapis.com/token"


def authorization_url(client_id: str, redirect_uri: str, state: str, challenge: str) -> str:
    if not all((client_id, redirect_uri, state, challenge)):
        raise ValueError("Incomplete OAuth configuration")
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": client_id, "redirect_uri": redirect_uri,
        "response_type": "code", "scope": " ".join(SCOPES),
        "state": state, "access_type": "offline", "prompt": "consent",
        "code_challenge": challenge, "code_challenge_method": "S256",
    })


async def exchange_code(client: httpx.AsyncClient, *, client_id: str,
                        client_secret: str, redirect_uri: str, code: str,
                        verifier: str) -> dict:
    response = await client.post(TOKEN_URL, data={
        "client_id": client_id, "client_secret": client_secret,
        "redirect_uri": redirect_uri, "code": code,
        "code_verifier": verifier, "grant_type": "authorization_code",
    })
    response.raise_for_status()
    return response.json()


async def refresh_token(client: httpx.AsyncClient, *, client_id: str,
                        client_secret: str, refresh: str) -> dict:
    response = await client.post(TOKEN_URL, data={
        "client_id": client_id, "client_secret": client_secret,
        "refresh_token": refresh, "grant_type": "refresh_token",
    })
    response.raise_for_status()
    return response.json()


class WorkspaceClient:
    def __init__(self, client: httpx.AsyncClient, token: str):
        if not token:
            raise ValueError("Workspace not connected")
        self.client = client
        self.headers = {"Authorization": "Bearer " + token}

    async def identity(self) -> dict:
        response = await self.client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo", headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    async def send_email(self, sender: str, recipient: str, subject: str, body: str) -> dict:
        message = EmailMessage()
        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        response = await self.client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers=self.headers, json={"raw": raw},
        )
        response.raise_for_status()
        return response.json()

    async def create_calendar_event(self, event: dict) -> dict:
        response = await self.client.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers=self.headers, params={"sendUpdates": "none"}, json=event,
        )
        response.raise_for_status()
        return response.json()

    async def create_drive_folder(self, name: str) -> dict:
        response = await self.client.post(
            "https://www.googleapis.com/drive/v3/files", headers=self.headers,
            json={"name": name, "mimeType": "application/vnd.google-apps.folder"},
        )
        response.raise_for_status()
        return response.json()


    async def publish_booking_event(self, event: dict) -> dict:
        event_id = event.get("id", "")
        if not isinstance(event_id, str) or len(event_id) != 32 or any(c not in "0123456789abcdef" for c in event_id):
            raise ValueError("Stable appointment event ID required")
        endpoint = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        response = await self.client.post(endpoint, headers=self.headers,
                                          params={"sendUpdates": "none"}, json=event)
        if response.status_code == 409:
            existing = await self.client.get(f"{endpoint}/{event_id}", headers=self.headers)
            existing.raise_for_status()
            current = existing.json()
            if current.get("id") != event_id or current.get("status") == "cancelled":
                raise ValueError("Calendar event requires review")
            response = await self.client.patch(f"{endpoint}/{event_id}", headers=self.headers,
                                               params={"sendUpdates": "none"},
                                               json={k: v for k, v in event.items() if k != "id"})
        response.raise_for_status()
        return response.json()
