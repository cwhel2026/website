from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin
from app.database import get_db
from app.models.user import User
from app.services.marketing.email.outreach_mailer import sent_count_today
from app.services.marketing.google_ads.google_ads_service import GoogleAdsClient
from app.services.marketing.integration_setup import build_integration_centre
from app.services.marketing.meta_ads_client import fetch_account_insights
from app.services.marketing.research.google_places import search_places

router = APIRouter(prefix="/marketing/integrations", tags=["marketing-integrations"])


@router.get("/setup-centre")
async def setup_centre(_: Annotated[User, Depends(get_current_admin)]) -> dict:
    return build_integration_centre()


@router.post("/test/meta-insights")
async def test_meta(_: Annotated[User, Depends(get_current_admin)]) -> dict:
    return await fetch_account_insights()


@router.post("/test/google-places")
async def test_places(
    _: Annotated[User, Depends(get_current_admin)],
    query: str = Query("car park Preston"),
) -> dict:
    return await search_places(query=query)


@router.post("/test/google-ads")
async def test_google_ads(_: Annotated[User, Depends(get_current_admin)]) -> dict:
    client = GoogleAdsClient()
    result = await client.search_campaigns()
    return {"ok": result.ok, "dry_run": result.dry_run, "message": result.message, "payload": result.payload}


@router.get("/outreach-stats")
async def outreach_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> dict:
    return {"sent_today": await sent_count_today(db)}

@router.post("/test/provider-health")
async def provider_health(_: Annotated[User, Depends(get_current_admin)]) -> dict:
    from app.services.provider_health import probe_providers
    return {"checks": await probe_providers()}
