from dataclasses import dataclass

from app.config import get_settings
from app.models.finance import FreeAgentConnectionState

settings = get_settings()


@dataclass
class FreeAgentStatus:
    state: FreeAgentConnectionState
    message: str
    can_sync: bool


def freeagent_status() -> FreeAgentStatus:
    client_id = getattr(settings, "freeagent_client_id", None)
    client_secret = getattr(settings, "freeagent_client_secret", None)
    if not client_id or not client_secret:
        return FreeAgentStatus(
            FreeAgentConnectionState.NOT_CONFIGURED,
            "FreeAgent OAuth credentials not set — use CSV import as fallback.",
            False,
        )
    return FreeAgentStatus(
        FreeAgentConnectionState.PENDING_OAUTH,
        "Credentials present but OAuth flow not completed in this environment.",
        False,
    )


async def sync_invoices_from_freeagent() -> dict:
    status = freeagent_status()
    if not status.can_sync:
        return {"synced": 0, "message": status.message}
    return {"synced": 0, "message": "Not implemented — verify FreeAgent API access first"}