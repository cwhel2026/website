import json
from decimal import Decimal
import pytest
import pytest_asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.agents import AgentProfile
from app.models.audit import AuditEvent
from app.models.marketing import RegionalCampaign
from app.models.notifications import NotificationOutbox
from app.models.orchestration import AgentTask, TaskStatus
from app.services.ai.execution import queue_work, run_next_employee_work
from app.services.ai.budget_math import campaign_budget

POLICY = dict(weekly_limit_gbp=150, monthly_limit_gbp=600, daily_limit_gbp=25, meta_daily_limit_gbp=25, meta_weekly_budget_gbp=150, meta_safety_buffer_pct=5)

@pytest_asyncio.fixture
async def db():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        for model in (AgentProfile, AgentTask, AuditEvent, RegionalCampaign, NotificationOutbox):
            await conn.run_sync(lambda c, m=model: m.__table__.create(c))
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        session.add(AgentProfile(slug='marketing', name='Olivia'))
        await session.commit()
        yield session
    await engine.dispose()

async def evidence(db, names):
    return {'marketing_budget_policy': POLICY, 'marketing_weekly_spend': {'total_spent_gbp': 0}, 'marketing_capacity': {'recommend_advertising': True, 'territories': [{'territory_name': 'Preston', 'allocated_spare_slots': 2, 'demand_score': 0}]}, 'finance_cashflow': {'opening_cash_gbp': {'status': 'unknown'}}, 'marketing_integrations': {'error': 'Not configured'}, 'marketing_experiments': []}

@pytest.mark.asyncio
async def test_campaign_150_saved_once_and_visible_to_dashboard(db, monkeypatch):
    monkeypatch.setattr('app.services.ai.execution.collect_evidence', evidence)
    kwargs = dict(agent_slug='marketing', chat_id=123, request_id=456, kind='campaign', brief='Prepare a £150 campaign', budget_gbp=150)
    first = await queue_work(db, **kwargs)
    duplicate = await queue_work(db, **kwargs)
    assert duplicate['task_id'] == first['task_id'] and duplicate['duplicate']
    await db.commit()
    assert await run_next_employee_work(db) == {'processed': 1}
    assert await run_next_employee_work(db) == {'processed': 0}
    campaign = await db.scalar(select(RegionalCampaign))
    assert campaign.daily_budget_gbp == Decimal('20.35')
    assert campaign.simulation_only and not campaign.external_campaign_id
    task = await db.scalar(select(AgentTask))
    result = json.loads(task.result_json)
    assert task.status == TaskStatus.COMPLETED
    assert result['campaign_id'] == str(campaign.id)
    assert result['plan']['finance_review']['status'] == 'unverified'
    assert Decimal(result['plan']['scenarios']['optimistic']['forecast']['fulfillable_jobs']) <= 1
    assert await db.scalar(select(func.count()).select_from(NotificationOutbox)) == 1
    from app.routers.business_director import employee_work
    assert (await employee_work(db, None))[0]['result']['campaign_id'] == str(campaign.id)

@pytest.mark.asyncio
async def test_failed_write_rolls_back_and_retries(db, monkeypatch):
    monkeypatch.setattr('app.services.ai.execution.collect_evidence', evidence)
    await queue_work(db, agent_slug='marketing', chat_id=123, request_id=99, kind='campaign', brief='Prepare campaign', budget_gbp=150)
    await db.commit()
    from app.services.ai.execution import execute_work
    async def fail_after_write(session, task):
        await execute_work(session, task)
        raise RuntimeError('crash after campaign insert')
    monkeypatch.setattr('app.services.ai.execution.execute_work', fail_after_write)
    for _ in range(3):
        assert (await run_next_employee_work(db))['failed_attempt']
        assert await db.scalar(select(func.count()).select_from(RegionalCampaign)) == 0
    task = await db.scalar(select(AgentTask))
    assert task.status == TaskStatus.FAILED and task.iteration_count == 3
    assert await run_next_employee_work(db) == {'processed': 0}

@pytest.mark.asyncio
async def test_role_boundaries_and_emergency_stop(db):
    assert 'error' in await queue_work(db, agent_slug='marketing', chat_id=1, request_id=1, kind='finance_review', brief='review')
    profile = await db.scalar(select(AgentProfile))
    profile.emergency_stop = True
    await db.commit()
    assert 'error' in await queue_work(db, agent_slug='marketing', chat_id=1, request_id=1, kind='campaign', brief='draft', budget_gbp=150)

@pytest.mark.parametrize('changes,spend,commitments,max_total', [({},0,0,142.5), ({'monthly_limit_gbp': 100},80,0,19), ({'meta_weekly_budget_gbp': 50},0,0,47.5), ({'daily_limit_gbp': 0},0,0,0), ({},0,10,76), ({'meta_safety_buffer_pct': 100},0,0,None)])
def test_authoritative_budget(changes, spend, commitments, max_total):
    result = campaign_budget({**POLICY, **changes}, {'total_spent_gbp': spend}, 150, commitments)
    if max_total is None:
        assert 'error' in result
    else:
        assert Decimal(result['total_gbp']) <= Decimal(str(max_total))
    assert result['authorised_spend_gbp'] == '0'

@pytest.mark.asyncio
async def test_no_capacity_preserves_draft_without_spend(db, monkeypatch):
    async def empty(session, names):
        result = await evidence(session, names)
        result['marketing_capacity'] = {'recommend_advertising': False, 'territories': []}
        return result
    monkeypatch.setattr('app.services.ai.execution.collect_evidence', empty)
    await queue_work(db, agent_slug='marketing', chat_id=123, request_id=55, kind='campaign', brief='Prepare campaign', budget_gbp=150)
    await db.commit()
    assert await run_next_employee_work(db) == {'processed': 1}
    campaign = await db.scalar(select(RegionalCampaign))
    assert campaign.daily_budget_gbp == 0
    result = json.loads((await db.scalar(select(AgentTask))).result_json)
    assert result['plan']['allocation'] == []


def test_platform_estimate_is_not_reach():
    from app.services.marketing.meta.delivery_estimates import parse_estimate
    assert not parse_estimate({'data': []})['available']
    assert not parse_estimate({'data': [{'estimate_ready': False}]})['available']
    result = parse_estimate({'data': [{'estimate_ready': True, 'estimate_mau_lower_bound': 100, 'estimate_mau_upper_bound': 200}]})
    assert result['audience_upper'] == 200 and 'reach' not in result

@pytest.mark.asyncio
async def test_telegram_request_to_worker_to_dashboard(db, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    from app.models.notifications import TelegramProcessedUpdate, TelegramConversationMessage
    from app.routers import telegram
    from app.services.ai.tool_registry import run_tool
    async with db.bind.begin() as conn:
        for model in (TelegramProcessedUpdate, TelegramConversationMessage):
            await conn.run_sync(lambda c, m=model: m.__table__.create(c))
    monkeypatch.setattr(telegram, 'get_settings', lambda: SimpleNamespace(telegram_bot_token='test', telegram_webhook_secret='test-secret', telegram_admin_id_list=[123], public_origin='https://example.com'))
    monkeypatch.setattr(telegram, '_safe_send', AsyncMock(return_value=12))
    async def provider(session, question, **kwargs):
        assert question == 'prepare a £150 campaign'
        result = await run_tool(session, 'queue_employee_work', {'kind': 'campaign', 'brief': question, 'budget_gbp': 150}, agent_slug=kwargs['agent_slug'], execution_context=kwargs['execution_context'])
        assert result['status'] == 'queued'
        return 'Campaign work saved for execution.', result, 'test-provider'
    monkeypatch.setattr('app.services.ai.employee_chat.chat_with_openai', provider)
    monkeypatch.setattr('app.services.ai.execution.collect_evidence', evidence)
    update = telegram.TelegramUpdate(update_id=777, message={'from': {'id': 123}, 'chat': {'id': 123}, 'text': 'Olivia, prepare a £150 campaign'})
    response = await telegram.telegram_webhook(update, db, 'test-secret')
    assert json.loads(response.body)['status'] == 'ok'
    assert json.loads((await telegram.telegram_webhook(update, db, 'test-secret')).body)['status'] == 'duplicate'
    assert await db.scalar(select(func.count()).select_from(AgentTask)) == 1
    assert await run_next_employee_work(db) == {'processed': 1}
    from app.routers.business_director import employee_work
    result = (await employee_work(db, None))[0]
    assert result['status'] == 'completed' and result['result']['campaign_id']
