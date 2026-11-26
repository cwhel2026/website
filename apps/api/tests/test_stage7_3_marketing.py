from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.marketing_ops import CommercialPipelineStage, CommercialProspect
from app.services.marketing.brand_profile import brand_system_prompt
from app.services.marketing.commercial_pipeline import transition_pipeline
from app.services.marketing.job_media_telegram import parse_job_reference
from app.services.marketing.meta_leads_service import _dedupe
from app.services.marketing.profitability_full import marketing_profitability_full


def test_parse_job_reference():
    assert parse_job_reference("#marketing before RMD-ABCD12 permission") == "RMD-ABCD12"


def test_brand_system_prompt():
    brand = SimpleNamespace(
        business_name="Revive My Drive Ltd",
        tone_of_voice="Professional",
        approved_claims_json=["Claim A"],
        approved_ctas_json=["Call us"],
        service_areas_json=["Preston"],
    )
    prompt = brand_system_prompt(brand)
    assert "Revive My Drive" in prompt
    assert "Never invent" in prompt


def test_meta_lead_dedupe_key_stable():
    payload = {"leadgen_id": "1", "x": 2}
    assert _dedupe(payload) == _dedupe(payload)
    assert _dedupe({**payload, "y": 3}) != _dedupe(payload)


@pytest.mark.asyncio
async def test_pipeline_opt_out_blocks():
    prospect = CommercialProspect(
        dedupe_key="test-pipeline-opt",
        business_name="Test",
        source_name="test",
        opt_out=True,
        pipeline_stage=CommercialPipelineStage.DISCOVERED,
    )
    db = AsyncMock()
    ok, msg = await transition_pipeline(db, prospect, CommercialPipelineStage.QUALIFIED)
    assert not ok
    assert "opt" in msg.lower()


@pytest.mark.asyncio
async def test_profitability_unknown_contribution(monkeypatch):
    async def fake_funnel(_db, *, days=90):
        return {
            "advertising_spend_gbp": 0.0,
            "quotations_accepted": 0,
            "attribution_touches": 0,
        }

    monkeypatch.setattr(
        "app.services.marketing.profitability_full.marketing_funnel_attribution",
        fake_funnel,
    )
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=0)
    db.execute = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    data = await marketing_profitability_full(db, days=30)
    assert data.get("job_contribution_gbp") is None
    assert "null not zero" in (data.get("job_contribution_note") or "")