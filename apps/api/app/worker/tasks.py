import asyncio
import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.database_sync import SessionLocal
from app.models.background_job import JobRunStatus
from app.models.jobs import Appointment, AppointmentType
from app.models.scheduling import SchedulingSettings
from app.models.weather import ProductProfile, WorkActivity
from app.services.weather.providers.openmeteo import fetch_openmeteo_hourly_sync
from app.services.weather.providers.simulation import simulate_hourly_forecast
from app.services.weather_engine import score_window, suitability_to_json
from app.worker.celery_app import celery_app
from app.worker.job_recorder import finish_run, start_run


def _worker_id() -> str:
    return celery_app.current_task.request.hostname if celery_app.current_task else "inline"


@celery_app.task(name="rmd.refresh_weather_hq", bind=True)
def refresh_weather_hq(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "refresh_weather_hq", dedupe_key=None, worker_id=_worker_id())
    try:
        settings_row = session.execute(select(SchedulingSettings).limit(1)).scalar_one_or_none()
        lat = float(settings_row.base_latitude) if settings_row else 53.5977
        lon = float(settings_row.base_longitude) if settings_row else -2.8407
        try:
            rows = fetch_openmeteo_hourly_sync(lat, lon, hours=48)
            source = "openmeteo"
            live = True
        except Exception as exc:
            rows = simulate_hourly_forecast(lat, lon, hours=48)
            source = "simulation"
            live = False
        detail = {
            "source": source,
            "live_forecast": live,
            "booking_safe": live,
            "hours": len(rows),
            "lat": lat,
            "lon": lon,
        }
        status = JobRunStatus.SUCCEEDED if live else JobRunStatus.FAILED
        error = None if live else "Live HQ weather unavailable; cache refreshed with simulation only (not for booking)."
        finish_run(session, run, status=status, detail=detail, error=error)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.appointment_weather_risk", bind=True)
def appointment_weather_risk(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "appointment_weather_risk", dedupe_key=None, worker_id=_worker_id())
    try:
        now = datetime.now(UTC)
        end = now + timedelta(days=3)
        profile = session.execute(
            select(ProductProfile).where(ProductProfile.is_active.is_(True)).limit(1)
        ).scalar_one_or_none()
        if profile is None:
            finish_run(session, run, status=JobRunStatus.SKIPPED, detail={"reason": "no_product_profile"})
            return {"checked": 0}

        appts = session.execute(
            select(Appointment).where(
                Appointment.scheduled_start >= now,
                Appointment.scheduled_start < end,
            )
        ).scalars().all()
        checked = 0
        flagged = 0
        live_failures = 0
        for appt in appts:
            lat = appt.latitude or 53.5977
            lon = appt.longitude or -2.8407
            try:
                forecast = fetch_openmeteo_hourly_sync(lat, lon, hours=72)
            except Exception:
                forecast = None
            activity = (
                WorkActivity.WASHING
                if appt.appointment_type == AppointmentType.PREPARATION
                else WorkActivity.COATING
            )
            if forecast is None:
                appt.weather_suitable = None
                appt.weather_notes = json.dumps(
                    {
                        "status": "unverified",
                        "reason": "live_forecast_unavailable",
                        "message": "Coating/wash suitability not updated — live weather required.",
                    }
                )
                live_failures += 1
                checked += 1
                flagged += 1
                continue
            result = score_window(
                activity,
                profile,
                forecast,
                appt.scheduled_start,
                appt.duration_minutes / 60,
            )
            appt.weather_suitable = result.is_safe
            appt.weather_notes = suitability_to_json(result)
            checked += 1
            if not result.is_safe:
                flagged += 1
        session.commit()
        detail = {
            "checked": checked,
            "flagged_unsuitable": flagged,
            "live_failures": live_failures,
        }
        if live_failures:
            from app.database import SessionLocal as AsyncSessionLocal
            from app.services.notifications.outbox import notify_owner_telegram

            async def _alert():
                async with AsyncSessionLocal() as adb:
                    await notify_owner_telegram(
                        adb,
                        title="Weather suitability unverified",
                        body=(
                            f"{live_failures} upcoming appointment(s) could not be checked against "
                            "a live forecast. Coating approval is blocked until weather is verified."
                        ),
                        category="weather_risk",
                        dedupe_key=f"weather-live-fail:{datetime.now(UTC).date().isoformat()}",
                    )

            asyncio.run(_alert())

        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        session.commit()
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.deliver_notification_outbox", bind=True)
def deliver_notification_outbox(self) -> dict:
    session = SessionLocal()
    run = start_run(
        session,
        "deliver_notification_outbox",
        dedupe_key=None,
        worker_id=_worker_id(),
    )
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.notifications.outbox import process_pending_telegram

        async def _deliver():
            async with AsyncSessionLocal() as adb:
                return await process_pending_telegram(adb)

        count = asyncio.run(_deliver())
        detail = {"delivered": count}
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.morning_briefing", bind=True)
def morning_briefing(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "morning_briefing", dedupe_key=datetime.now(UTC).date().isoformat(), worker_id=_worker_id())
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.models.briefings import BriefingKind
        from app.services.briefing_service import generate_briefing

        async def _brief():
            async with AsyncSessionLocal() as db:
                record = await generate_briefing(db, BriefingKind.MORNING)
                await db.commit()
                return json.loads(record.payload_json)

        payload = asyncio.run(_brief())
        detail = {"sections": list(payload.keys())}
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return {"stored": False, "sections": detail["sections"], "preview": json.dumps(payload, default=str)[:500]}
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.finance_report_daily", bind=True)
def finance_report_daily(self) -> dict:
    session = SessionLocal()
    run = start_run(
        session,
        "finance_report_daily",
        dedupe_key=datetime.now(UTC).date().isoformat(),
        worker_id=_worker_id(),
    )
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.finance.financial_reports import (
            deliver_report_telegram,
            generate_daily_finance_report,
        )

        async def _run():
            async with AsyncSessionLocal() as adb:
                record = await generate_daily_finance_report(adb)
                await deliver_report_telegram(adb, record)
                await adb.commit()
                return {"report_id": str(record.id)}

        detail = asyncio.run(_run())
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.finance_report_weekly", bind=True)
def finance_report_weekly(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "finance_report_weekly", dedupe_key=None, worker_id=_worker_id())
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.finance.financial_reports import (
            deliver_report_telegram,
            generate_weekly_finance_report,
        )

        async def _run():
            async with AsyncSessionLocal() as adb:
                record = await generate_weekly_finance_report(adb)
                await deliver_report_telegram(adb, record)
                await adb.commit()
                return {"report_id": str(record.id)}

        detail = asyncio.run(_run())
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.finance_report_monthly", bind=True)
def finance_report_monthly(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "finance_report_monthly", dedupe_key=datetime.now(UTC).strftime("%Y-%m"), worker_id=_worker_id())
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.finance.financial_reports import deliver_report_telegram, generate_monthly_finance_report

        async def _run():
            async with AsyncSessionLocal() as adb:
                record = await generate_monthly_finance_report(adb)
                await deliver_report_telegram(adb, record)
                await adb.commit()
                return {"report_id": str(record.id)}

        detail = asyncio.run(_run())
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.finance_report_annual", bind=True)
def finance_report_annual(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "finance_report_annual", dedupe_key=None, worker_id=_worker_id())
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.finance.financial_reports import (
            annual_report_idempotency_key,
            deliver_report_telegram,
            generate_annual_finance_report,
        )

        async def _run():
            async with AsyncSessionLocal() as adb:
                idem = await annual_report_idempotency_key(adb)
                if idem is None:
                    return {"skipped": True, "reason": "not_accounting_year_end"}
                record = await generate_annual_finance_report(adb)
                await deliver_report_telegram(adb, record)
                await adb.commit()
                return {"report_id": str(record.id)}

        detail = asyncio.run(_run())
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.finance_task_centre_notify", bind=True)
def finance_task_centre_notify(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "finance_task_centre_notify", dedupe_key=datetime.now(UTC).date().isoformat(), worker_id=_worker_id())
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.finance.financial_task_centre import task_centre_plain_summary
        from app.services.notifications.outbox import enqueue_notification

        async def _run():
            async with AsyncSessionLocal() as adb:
                body = await task_centre_plain_summary(adb)
                await enqueue_notification(
                    adb,
                    channel="telegram",
                    title="Finance task centre",
                    body=body,
                    category="finance_tasks",
                    dedupe_key=f"tasks:{datetime.now(UTC).date().isoformat()}",
                    priority="normal",
                )
                await adb.commit()
                return {"queued": True}

        detail = asyncio.run(_run())
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.financial_watchdog", bind=True)
def financial_watchdog(self) -> dict:
    session = SessionLocal()
    run = start_run(
        session,
        "financial_watchdog",
        dedupe_key=datetime.now(UTC).date().isoformat(),
        worker_id=_worker_id(),
    )
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.finance.watchdog import run_financial_watchdog
        from app.services.notifications.outbox import enqueue_notification

        async def _watch():
            async with AsyncSessionLocal() as adb:
                issues = await run_financial_watchdog(adb)
                high = [i for i in issues if i["severity"] == "high"]
                if high:
                    body = "\n".join(f"• {i['title']}" for i in high[:6])
                    await enqueue_notification(
                        adb,
                        channel="telegram",
                        title="Urgent finance alerts",
                        body=body,
                        category="finance_watchdog",
                        dedupe_key=f"watchdog-auto:{datetime.now(UTC).date().isoformat()}",
                        priority="high",
                    )
                await adb.commit()
                return {"issues": len(issues), "urgent": len(high)}

        detail = asyncio.run(_watch())
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.bookkeeping_categorize", bind=True)
def bookkeeping_categorize(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "bookkeeping_categorize", dedupe_key=None, worker_id=_worker_id())
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.finance.bookkeeping.review_queue import categorize_uncategorized_transactions

        async def _cat():
            async with AsyncSessionLocal() as adb:
                result = await categorize_uncategorized_transactions(adb)
                await adb.commit()
                return result

        detail = asyncio.run(_cat())
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.freeagent_sync_incremental", bind=True)
def freeagent_sync_incremental(self) -> dict:
    session = SessionLocal()
    today = datetime.now(UTC).date().isoformat()
    run = start_run(
        session,
        "freeagent_sync_incremental",
        dedupe_key=f"freeagent-sync:{today}",
        worker_id=_worker_id(),
    )
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.finance.freeagent_sync import sync_all_freeagent

        async def _sync():
            async with AsyncSessionLocal() as adb:
                result = await sync_all_freeagent(adb)
                await adb.commit()
                return result

        result = asyncio.run(_sync())
        detail = {k: v for k, v in result.items()}
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.marketing_daily_brief", bind=True)
def marketing_daily_brief(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "marketing_daily_brief", dedupe_key=None, worker_id=_worker_id())
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.marketing.director_proactive import run_daily_director_cycle

        from app.services.notifications.outbox import enqueue_notification

        async def _plan_and_notify():
            async with AsyncSessionLocal() as adb:
                plan = await run_daily_director_cycle(adb, execute_research=False)
                recs = (plan.get("recommendations") or [])[:5]
                body = "\n".join(f"• {r.get('action')}" for r in recs if r.get("action"))
                try:
                    from app.services.marketing.growth_fund import fund_summary

                    gf = await fund_summary(adb)
                    body = (
                        f"Growth fund: £{gf['virtual_reserve_balance_gbp']:.2f} "
                        f"(available £{gf['available_uncommitted_gbp']:.2f})\n"
                        f"Weekly ad limit: £150 until you approve more.\n\n"
                        + (body or "")
                    )
                except Exception:
                    pass
                await enqueue_notification(
                    adb,
                    channel="telegram",
                    title="Marketing director — daily brief",
                    body=body or plan.get("summary") or "No actions",
                    category="marketing_director",
                    dedupe_key=f"marketing_brief:{datetime.now(UTC).date().isoformat()}",
                )
                await adb.commit()
                return plan

        plan = asyncio.run(_plan_and_notify())
        brief = {
            "summary": plan.get("summary"),
            "recommendations": (plan.get("recommendations") or [])[:5],
            "pre_launch_mode": plan.get("pre_launch_mode"),
        }
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=brief)
        return brief
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.marketing_prospect_research", bind=True)
def marketing_prospect_research(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "marketing_prospect_research", dedupe_key=None, worker_id=_worker_id())
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.models.territory import Territory
        from app.services.marketing.research.prospect_orchestrator import run_territory_research

        async def _run():
            async with AsyncSessionLocal() as adb:
                terr = (
                    await adb.execute(
                        select(Territory).where(Territory.is_active.is_(True)).order_by(Territory.code).limit(1)
                    )
                ).scalar_one_or_none()
                if terr is None:
                    return {"ok": False, "message": "No active territory"}
                return await run_territory_research(
                    adb,
                    territory_id=terr.id,
                    category="commercial_surface",
                    places_query=f"car park {terr.name}",
                )

        detail = asyncio.run(_run())
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.marketing_weekly_strategy", bind=True)
def marketing_weekly_strategy(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "marketing_weekly_strategy", dedupe_key=None, worker_id=_worker_id())
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.marketing.director import build_weekly_marketing_plan
        from app.services.marketing.marketing_profitability import marketing_profitability_snapshot

        async def _run():
            async with AsyncSessionLocal() as adb:
                plan = await build_weekly_marketing_plan(adb)
                profit = await marketing_profitability_snapshot(adb, days=30)
                return {"plan": plan, "profitability": profit}

        detail = asyncio.run(_run())
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail={"summary": "weekly strategy generated"})
        return {"ok": True, "attribution_events_7d": detail["plan"].get("attribution_events_7d")}
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.marketing_capacity_snapshot", bind=True)
def marketing_capacity_snapshot(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "marketing_capacity_snapshot", dedupe_key=None, worker_id=_worker_id())
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.marketing.capacity_engine import global_capacity_snapshot

        async def _cap():
            async with AsyncSessionLocal() as adb:
                return await global_capacity_snapshot(adb)

        snap = asyncio.run(_cap())
        detail = {k: float(v) if hasattr(v, "as_tuple") else v for k, v in snap.__dict__.items()}
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.assess_quote_photos", bind=True)
def assess_quote_photos(self, set_id: str) -> dict:
    """Vision check for driveway photographs. The quotation price does not wait for this."""
    session = SessionLocal()
    run = start_run(session, "assess_quote_photos", dedupe_key=set_id, worker_id=_worker_id())
    try:
        from uuid import UUID

        from app.services.quote_photos import assess_photo_set

        asyncio.run(assess_photo_set(UUID(set_id)))
        detail = {"set_id": set_id}
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.purge_quote_photos", bind=True)
def purge_quote_photos(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "purge_quote_photos", dedupe_key=None, worker_id=_worker_id())
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.quote_photos import purge_expired_quote_photos

        async def _purge():
            async with AsyncSessionLocal() as adb:
                removed = await purge_expired_quote_photos(adb)
                await adb.commit()
                return removed

        removed = asyncio.run(_purge())
        detail = {"removed": removed}
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=detail)
        return detail
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()


@celery_app.task(name="rmd.marketing_organic_sync", bind=True)
def marketing_organic_sync(self) -> dict:
    session = SessionLocal()
    run = start_run(session, "marketing_organic_sync", dedupe_key=None, worker_id=_worker_id())
    try:
        from app.database import SessionLocal as AsyncSessionLocal
        from app.services.marketing.organic_post_sync import sync_all_organic

        async def _sync():
            async with AsyncSessionLocal() as adb:
                result = await sync_all_organic(adb)
                await adb.commit()
                return result

        result = asyncio.run(_sync())
        finish_run(session, run, status=JobRunStatus.SUCCEEDED, detail=result)
        return result
    except Exception as exc:
        finish_run(session, run, status=JobRunStatus.FAILED, error=str(exc))
        raise
    finally:
        session.close()

@celery_app.task(name="rmd.employee_work")
def employee_work():
    from app.database import SessionLocal as AsyncSessionLocal
    from app.services.ai.background_work import run_next_owner_task

    async def run():
        async with AsyncSessionLocal() as db:
            return await run_next_owner_task(db)

    return asyncio.run(run())
