import asyncio
import contextlib
import logging
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
from app.database import SessionLocal
from app.routers import growth_fund, marketing_surfacecoat, ops, workspace, booking_payments
from app.routers import (
    approvals,
    assistant,
    auth,
    automations,
    bookkeeping,
    briefings,
    calendar,
    communications,
    crm,
    marketing,
    marketing_content,
    marketing_integrations,
    marketing_launch,
    marketing_public,
    marketing_webhooks,
    public,
    accountant,
    analytics,
    business_director,
    company,
    finance,
    finance_insights,
    health,
    inventory,
    jobs,
    quotation_photos,
    quotations,
    regional_ops,
    remuneration,
    services,
    tax_centre,
    telegram,
    territories,
    weather,
    notifications,
)
from app.seeds.bootstrap import seed_database

settings = get_settings()
logger = logging.getLogger(__name__)


def _try_register_telegram_webhook() -> None:
    if not settings.telegram_auto_register_webhook:
        return
    if not settings.telegram_bot_token or not settings.telegram_webhook_secret:
        return
    try:
        from app.services.telegram.register import WebhookRegistrationError, register_telegram_webhook

        register_telegram_webhook()
    except WebhookRegistrationError as exc:
        logger.warning("Telegram webhook auto-registration skipped: %s", exc)
    except Exception:
        logger.exception("Telegram webhook auto-registration failed")


async def _bootstrap_data() -> None:
    """Seeding — runs in the background so /health can respond quickly.

    The schema is owned exclusively by Alembic (``alembic upgrade head`` runs
    before the API starts); the API never creates or alters tables itself.
    """
    try:
        async with SessionLocal() as session:
            await seed_database(session)
        await asyncio.to_thread(_try_register_telegram_webhook)
    except Exception:
        logger.exception("API bootstrap failed (migrations, seed, or webhook registration)")
    try:
        async with SessionLocal() as recover_db:
            from app.services.notifications.outbox import process_pending_telegram
            from app.services.quote_conversion import recover_outstanding_quote_alerts

            recovered = await recover_outstanding_quote_alerts(recover_db)
            delivered = await process_pending_telegram(recover_db)
            if recovered or delivered:
                logger.info("Telegram recovery: requeued=%s delivered=%s", recovered, delivered)
    except Exception:
        logger.exception("Telegram outbox recovery failed")


async def _telegram_outbox_pump() -> None:
    """Deliver pending Telegram rows even when the Celery worker is not running."""
    from app.services.notifications.outbox import process_pending_telegram

    while True:
        await asyncio.sleep(90)
        try:
            async with SessionLocal() as session:
                await process_pending_telegram(session)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Telegram outbox pump failed")


async def _booking_outbox_pump() -> None:
    from sqlalchemy import select
    from app.models.notifications import NotificationOutbox, OutboxStatus
    from app.services.payments.workspace_delivery import deliver_booking_notification
    from app.services.payments.polling import sweep_sandbox_deposits

    while True:
        await asyncio.sleep(90)
        try:
            if settings.global_emergency_stop:
                continue
            await sweep_sandbox_deposits(SessionLocal)
            if not settings.workspace_booking_delivery_enabled:
                continue
            async with SessionLocal() as session:
                ids = list(await session.scalars(select(NotificationOutbox.id).where(
                    NotificationOutbox.category == "booking_confirmation",
                    NotificationOutbox.channel.in_(("workspace_email", "workspace_calendar")),
                    NotificationOutbox.status == OutboxStatus.PENDING,
                ).order_by(NotificationOutbox.created_at).limit(20)))
            for notification_id in ids:
                try:
                    await deliver_booking_notification(SessionLocal, notification_id)
                except Exception:
                    logger.warning("Booking notification delivery unavailable")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.warning("Booking outbox pump unavailable")


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_production_settings(settings)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    # CI integration tests (ENVIRONMENT=test) need a fully seeded DB before requests.
    if settings.environment == "test":
        await _bootstrap_data()
        yield
        return
    bootstrap = asyncio.create_task(_bootstrap_data())
    pump = asyncio.create_task(_telegram_outbox_pump())
    booking_pump = asyncio.create_task(_booking_outbox_pump())
    yield
    booking_pump.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await booking_pump
    pump.cancel()
    bootstrap.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await pump
    with contextlib.suppress(asyncio.CancelledError):
        await bootstrap


app = FastAPI(
    title="SurfaceCoat API",
    version="0.7.0",
    description="Regional business operating system — Phase 7 production readiness",
    lifespan=lifespan,
    docs_url=None if settings.environment.lower() == "production" else "/docs",
    redoc_url=None if settings.environment.lower() == "production" else "/redoc",
    openapi_url=None if settings.environment.lower() == "production" else "/openapi.json",
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
app.include_router(quotation_photos.router, prefix=prefix)
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
app.include_router(notifications.router, prefix=prefix)
app.include_router(marketing.router, prefix=prefix)
app.include_router(marketing_integrations.router, prefix=prefix)
app.include_router(marketing_content.router, prefix=prefix)
app.include_router(marketing_webhooks.router, prefix=prefix)
app.include_router(marketing_launch.router, prefix=prefix)
app.include_router(marketing_surfacecoat.router, prefix=prefix)
app.include_router(growth_fund.router, prefix=prefix)
app.include_router(marketing_public.router, prefix=prefix)
app.include_router(public.router, prefix=prefix)
app.include_router(company.router, prefix=prefix)
app.include_router(finance.router, prefix=prefix)
app.include_router(bookkeeping.router, prefix=prefix)
app.include_router(tax_centre.router, prefix=prefix)
app.include_router(remuneration.router, prefix=prefix)
app.include_router(finance_insights.router, prefix=prefix)
app.include_router(accountant.router, prefix=prefix)
app.include_router(inventory.router, prefix=prefix)
app.include_router(analytics.router, prefix=prefix)
app.include_router(business_director.router, prefix=prefix)
app.include_router(ops.router, prefix=prefix)
app.include_router(workspace.router, prefix=prefix)
app.include_router(booking_payments.router, prefix=prefix)
app.include_router(health.router)