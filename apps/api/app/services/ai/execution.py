"""Bounded employee jobs. Local writes and their evidence commit atomically.

No handler in this module publishes, spends, contacts customers or books work.
The task UUID is derived from the trusted Telegram update, never model arguments.
"""
import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from app.models.agents import AgentProfile
from app.models.orchestration import AgentTask, TaskStatus
from app.models.marketing import RegionalCampaign, CampaignStatus, AdPlatform
from app.services.audit import record_audit

WORK_ROLES = {"campaign": {"marketing", "personal_assistant"}, "finance_review": {"finance", "personal_assistant"}, "operations_review": {"personal_assistant"}}


async def queue_work(db, *, agent_slug, chat_id, request_id, kind, brief, budget_gbp=None):
    if kind not in WORK_ROLES or agent_slug not in WORK_ROLES[kind]:
        return {"error": "Employee does not have permission for this work"}
    if not isinstance(brief, str) or not 1 <= len(brief.strip()) <= 4000:
        return {"error": "A work brief of 1–4000 characters is required"}
    if kind == "campaign":
        try:
            amount = Decimal(str(budget_gbp))
            if not amount.is_finite() or not 0 < amount <= 100000 or amount != amount.quantize(Decimal('.01')):
                raise ValueError()
        except Exception:
            return {"error": "An explicit positive campaign budget is required"}
    profile = await db.scalar(select(AgentProfile).where(AgentProfile.slug == agent_slug).with_for_update())
    if not profile or profile.is_paused or profile.emergency_stop:
        return {"error": "Employee unavailable or paused"}
    ident = uuid5(NAMESPACE_URL, f"surfacecoat:employee:{chat_id}:{request_id}:{kind}")
    existing = await db.get(AgentTask, ident)
    if existing:
        return {"task_id": str(ident), "status": existing.status.value, "duplicate": True}
    task = AgentTask(id=ident, agent_slug=agent_slug, assigned_by=f"telegram:{chat_id}", action_key="employee_execution", title=brief[:255], payload_json=json.dumps({"kind": kind, "brief": brief, "budget_gbp": str(budget_gbp) if budget_gbp is not None else None}), status=TaskStatus.QUEUED)
    db.add(task)
    await db.flush()
    await record_audit(db, actor_type="ai_employee", actor_id=agent_slug, action="employee_work_queued", entity_type="agent_task", entity_id=ident, detail={"kind": kind})
    return {"task_id": str(ident), "status": "queued", "message": "Saved for background execution. Completion will be reported through Telegram and the dashboard. No external action authorised."}


async def collect_evidence(db, names):
    from app.services.ai.tool_registry import run_tool
    evidence = {}
    for name in names:
        try:
            async with db.begin_nested():
                evidence[name] = await run_tool(db, name, {})
        except Exception:
            evidence[name] = {"error": "Evidence unavailable"}
    return evidence


async def execute_work(db, task):
    payload = json.loads(task.payload_json)
    kind = payload['kind']
    if task.agent_slug not in WORK_ROLES.get(kind, set()):
        raise ValueError("Work permission denied")
    if kind == "campaign":
        from app.services.ai.commercial_plan import plan_campaign, scenario_reach
        evidence = await collect_evidence(db, ("marketing_budget_policy", "marketing_capacity", "marketing_weekly_spend", "finance_cashflow", "marketing_integrations", "marketing_experiments"))
        plan = plan_campaign(evidence['marketing_capacity'], evidence['marketing_budget_policy'], evidence['marketing_weekly_spend'], payload['budget_gbp'])
        rows = plan.get('allocation', [])
        total = sum((Decimal(r['total_gbp']) for r in rows), Decimal(0))
        plan['scenarios'] = scenario_reach(total, plan.get('evidence', {}).get('allocated_spare_slots', 0)//2) if total else {}
        plan['finance_review'] = {"status": "unverified", "reason": "Recorded cash flow is a forecast; bank balance, liabilities and job costs must be reconciled before spend approval.", "evidence": evidence['finance_cashflow']}
        plan['operations_review'] = {"status": "provisional", "capacity": evidence['marketing_capacity'], "condition": "Reserve preparation and coating visits within seven days; confirm weather and travel before booking."}
        plan['audience'] = {"segment": "Domestic tarmac driveway owners within the selected service territory", "basis": "Test hypothesis, not verified audience research", "objective": "OUTCOME_LEADS", "placements": ["facebook", "instagram"], "creative": "Permission-cleared before/after photos of the same driveway, plus a short coating demonstration", "qualification": ["postcode", "surface type", "approximate area", "photographs"], "retargeting": "Requires consent and an eligible populated custom audience; not enabled by this draft"}
        plan['research_status'] = "Database evidence only; no live competitor or audience research performed"
        plan['launch_blockers'] = list(dict.fromkeys(plan.get('launch_blockers', []) + ["Verified bank affordability and job contribution", "Owner approval of final targeting, creative and spend", "Meta permissions, account limits and complete ad set configuration"]))
        campaign = RegionalCampaign(id=uuid5(NAMESPACE_URL, f"surfacecoat:campaign:{task.id}"), name=f"Employee draft — {rows[0]['territory'] if rows else 'territory review required'}"[:200], platform=AdPlatform.META, status=CampaignStatus.DRAFT, simulation_only=True, daily_budget_gbp=Decimal(rows[0]['daily_gbp']) if rows else Decimal(0), monthly_budget_gbp=Decimal(0), headline="Bring your tired tarmac back to black", body_text="SurfaceCoat driveway cleaning and recolouring. Send your postcode and driveway photographs for an assessment.", landing_path="/quote")
        db.add(campaign)
        await db.flush()
        return {"kind": kind, "campaign_id": str(campaign.id), "summary": f"Saved campaign draft: £{total} proposed over seven days. Financial verification and launch approval remain outstanding.", "plan": plan, "evidence": evidence, "external_actions": False}
    names = ("finance_summary", "finance_cashflow", "finance_tax_reserves", "pricing_profile") if kind == "finance_review" else ("jobs_next_week", "wash_pending_coat", "rain_risk_coating", "quotations_awaiting", "marketing_capacity")
    evidence = await collect_evidence(db, names)
    return {"kind": kind, "summary": "Saved financial evidence review; estimates require reconciliation." if kind == "finance_review" else "Saved operations evidence review; weather, travel and seven-day coating dates require booking validation.", "evidence": evidence, "external_actions": False}


async def run_next_employee_work(db):
    from app.services.notifications.outbox import enqueue_notification
    task = await db.scalar(select(AgentTask).join(AgentProfile, AgentProfile.slug == AgentTask.agent_slug).where(AgentTask.action_key == 'employee_execution', AgentTask.status == TaskStatus.QUEUED, AgentTask.iteration_count < AgentTask.max_iterations, AgentProfile.is_paused.is_(False), AgentProfile.emergency_stop.is_(False)).order_by(AgentTask.priority.desc(), AgentTask.created_at).limit(1).with_for_update(of=(AgentTask, AgentProfile), skip_locked=True))
    if task is None:
        return {"processed": 0}
    task.iteration_count += 1
    try:
        async with db.begin_nested():
            task.status = TaskStatus.RUNNING
            result = await execute_work(db, task)
            task.result_json = json.dumps(result, default=str)
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(UTC)
            await record_audit(db, actor_type="ai_employee", actor_id=task.agent_slug, action="employee_work_completed", entity_type="agent_task", entity_id=task.id, detail={"kind": result['kind'], "campaign_id": result.get('campaign_id')})
            await enqueue_notification(db, channel="telegram", title="Employee work completed", body=f"{result['summary']}\nReference: {task.id}\nReview the saved evidence in the dashboard.", category="assistant_reply", dedupe_key=f"employee-completed:{task.id}", payload={"reply_chat_id": int(task.assigned_by.split(':')[1])})
    except Exception:
        await db.refresh(task)
        task.status = TaskStatus.FAILED if task.iteration_count >= task.max_iterations else TaskStatus.QUEUED
        task.result_json = json.dumps({"error": "Work failed; no partial business writes committed", "attempt": task.iteration_count})
        if task.status == TaskStatus.FAILED:
            await enqueue_notification(db, channel="telegram", title="Employee work needs attention", body=f"Could not complete {task.title} after {task.iteration_count} attempts. Reference: {task.id}", category="assistant_reply", dedupe_key=f"employee-failed:{task.id}", payload={"reply_chat_id": int(task.assigned_by.split(':')[1])})
        await db.commit()
        return {"processed": 0, "failed_attempt": True}
    await db.commit()
    return {"processed": 1}
