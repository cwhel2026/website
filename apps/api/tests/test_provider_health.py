import httpx
import pytest
from types import SimpleNamespace

from app.services import provider_health


@pytest.mark.asyncio
async def test_provider_probes_are_read_only_and_fail_closed(monkeypatch):
    monkeypatch.setattr(provider_health, "get_settings", lambda: SimpleNamespace(
        openai_api_key="secret", telegram_bot_token="123:secret", meta_ad_account_id="act_456",
        meta_access_token="secret", weather_provider="openmeteo"))
    def respond(request):
        assert request.method == "GET"
        if request.url.host == "api.openai.com":
            return httpx.Response(200, json={"data":[]})
        if request.url.host == "api.telegram.org":
            return httpx.Response(200, json={"ok":False,"error":"secret"})
        if request.url.host == "graph.facebook.com":
            return httpx.Response(200, json={"id":"act_456"})
        return httpx.Response(200, json={"hourly":{}})
    result = await provider_health.probe_providers(httpx.MockTransport(respond))
    assert [r["state"] for r in result] == ["verified_read","failed","verified_read","failed"]
    assert "secret" not in str(result)
