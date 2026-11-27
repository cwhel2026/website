from datetime import UTC, datetime
import logging
import re

import httpx

from app.config import get_settings

# Telegram credentials are embedded in its URL. Never emit HTTP request URLs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


async def probe_providers(transport=None) -> list[dict]:
    s = get_settings()
    results = []

    async with httpx.AsyncClient(timeout=8.0, follow_redirects=False, transport=transport) as client:
        async def probe(name, configured, url, validate, **kwargs):
            state = "not_configured"
            if configured:
                try:
                    response = await client.get(url, **kwargs)
                    state = "verified_read" if response.status_code == 200 and validate(response.json()) else "failed"
                except (httpx.HTTPError, ValueError, TypeError, KeyError):
                    state = "failed"
            results.append({"provider": name, "state": state, "checked_at": datetime.now(UTC).isoformat()})

        await probe("OpenAI", bool(s.openai_api_key), "https://api.openai.com/v1/models",
                    lambda d: isinstance(d, dict) and isinstance(d.get("data"), list),
                    headers={"Authorization": f"Bearer {s.openai_api_key}"})
        token = s.telegram_bot_token or ""
        await probe("Telegram bot", bool(re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]+", token)),
                    f"https://api.telegram.org/bot{token}/getMe",
                    lambda d: isinstance(d, dict) and d.get("ok") is True and isinstance(d.get("result"), dict) and d["result"].get("is_bot") is True)
        account = (s.meta_ad_account_id or "").removeprefix("act_")
        await probe("Meta Ads", bool(s.meta_access_token and account.isdigit()),
                    f"https://graph.facebook.com/v21.0/act_{account}",
                    lambda d: isinstance(d, dict) and d.get("id") == f"act_{account}",
                    headers={"Authorization": f"Bearer {s.meta_access_token}"}, params={"fields":"id"})
        await probe("Weather provider", s.weather_provider == "openmeteo",
                    "https://api.open-meteo.com/v1/forecast",
                    lambda d: isinstance(d, dict) and isinstance(d.get("hourly"), dict) and bool(d["hourly"].get("temperature_2m")),
                    params={"latitude":53.6,"longitude":-2.84,"hourly":"temperature_2m","forecast_days":1})
    return results
