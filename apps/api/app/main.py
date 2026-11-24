from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.rate_limit import limiter
from app.security.startup import validate_production_settings
from app.database import Base, SessionLocal, engine
from app.routers import (
    approvals,
    assistant,
    auth,
    automations,
    briefings,
    calendar,
    communications,
    crm,
    marketing,
    marketing_public,
    analytics,
    business_director,
    finance,
    health,
    inventory,
    jobs,
    quotations,
    regional_ops,
    services,
    telegram,
    territories,
    weather,
)
from app.seeds.bootstrap import seed_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_production_settings(settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_database(session)
    yield


app = FastAPI(
    title="Revive My Drive API",
    version="0.7.0",
    description="Regional business operating system — Phase 7 production readiness",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = "/api/v1"
app.include_router(auth.router, prefix=prefix)
app.include_router(territories.router, prefix=prefix)
app.include_router(services.router, prefix=prefix)
app.include_router(crm.router, prefix=prefix)
app.include_router(quotations.router, prefix=prefix)
app.include_router(jobs.router, prefix=prefix)
app.include_router(calendar.router, prefix=prefix)
app.include_router(weather.router, prefix=prefix)
app.include_router(regional_ops.router, prefix=prefix)
app.include_router(assistant.router, prefix=prefix)
app.include_router(approvals.router, prefix=prefix)
app.include_router(briefings.router, prefix=prefix)
app.include_router(automations.router, prefix=prefix)
app.include_router(communications.router, prefix=prefix)
app.include_router(telegram.router, prefix=prefix)
app.include_router(marketing.router, prefix=prefix)
app.include_router(marketing_public.router, prefix=prefix)
app.include_router(finance.router, prefix=prefix)
app.include_router(inventory.router, prefix=prefix)
app.include_router(analytics.router, prefix=prefix)
app.include_router(business_director.router, prefix=prefix)
app.include_router(health.router)