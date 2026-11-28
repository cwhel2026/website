import pytest

from app.services.marketing.integration_setup import build_integration_centre
from app.services.marketing.media_store import store_bytes, resolve_path
from app.services.marketing.research.osm_overpass import query_commercial_features


def test_integration_centre_lists_providers():
    data = build_integration_centre()
    platforms = {i["platform"] for i in data["integrations"]}
    assert "companies_house" in platforms
    assert "google_places" in platforms
    assert "meta_ads" in platforms


def test_media_store_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("MARKETING_MEDIA_DIR", str(tmp_path))
    from app.config import get_settings

    get_settings.cache_clear()
    key, digest = store_bytes(data=b"hello", filename="test.jpg")
    assert digest
    path = resolve_path(key)
    assert path.read_bytes() == b"hello"


@pytest.mark.asyncio
async def test_osm_overpass_returns_structure():
    result = await query_commercial_features(lat=53.75, lon=-2.7, radius_m=2000)
    assert "ok" in result
    assert "items" in result

def test_phase12_campaign_budget_validation():
    from pydantic import ValidationError
    from app.routers.marketing import CampaignIn
    from app.models.marketing import AdPlatform
    for amount in ("-1", "NaN", "Infinity"):
        with pytest.raises(ValidationError):
            CampaignIn(name="Test", platform=AdPlatform.META, daily_budget_gbp=amount)


def test_phase12_outreach_requires_verified_corporate_contact():
    from types import SimpleNamespace
    from app.services.marketing.outreach_compliance import validate_outreach_eligibility
    prospect = SimpleNamespace(opt_out=False, contact_email="office@example.com", is_corporate_subscriber=None, lawful_basis="legitimate_interest")
    assert not validate_outreach_eligibility(prospect)[0]
    prospect.is_corporate_subscriber = True
    assert validate_outreach_eligibility(prospect)[0]
    prospect.opt_out = True
    assert not validate_outreach_eligibility(prospect)[0]


@pytest.mark.asyncio
async def test_phase12_pending_outreach_cannot_send():
    from types import SimpleNamespace
    from app.models.marketing_ops import OutreachMessageStatus
    from app.services.marketing.email.outreach_mailer import approve_and_send
    prospect = SimpleNamespace(opt_out=False, contact_email="office@example.com", is_corporate_subscriber=True, lawful_basis="legitimate_interest")
    message = SimpleNamespace(status=OutreachMessageStatus.PENDING_APPROVAL)
    result = await approve_and_send(None, message, prospect)
    assert not result["ok"]
    assert message.status == OutreachMessageStatus.PENDING_APPROVAL
