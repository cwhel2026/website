"""Commercial sales pipeline — GDPR-safe stage transitions."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_ops import CommercialPipelineStage, CommercialProspect


ALLOWED: dict[CommercialPipelineStage, set[CommercialPipelineStage]] = {
    CommercialPipelineStage.DISCOVERED: {CommercialPipelineStage.RESEARCH_REQUIRED, CommercialPipelineStage.QUALIFIED, CommercialPipelineStage.DO_NOT_CONTACT},
    CommercialPipelineStage.RESEARCH_REQUIRED: {CommercialPipelineStage.QUALIFIED, CommercialPipelineStage.DO_NOT_CONTACT},
    CommercialPipelineStage.QUALIFIED: {CommercialPipelineStage.CONTACT_VERIFIED, CommercialPipelineStage.DO_NOT_CONTACT},
    CommercialPipelineStage.CONTACT_VERIFIED: {CommercialPipelineStage.OUTREACH_DRAFTED, CommercialPipelineStage.DO_NOT_CONTACT},
    CommercialPipelineStage.OUTREACH_DRAFTED: {CommercialPipelineStage.APPROVED, CommercialPipelineStage.DO_NOT_CONTACT},
    CommercialPipelineStage.APPROVED: {CommercialPipelineStage.CONTACTED, CommercialPipelineStage.DO_NOT_CONTACT},
    CommercialPipelineStage.CONTACTED: {CommercialPipelineStage.REPLIED, CommercialPipelineStage.DO_NOT_CONTACT},
    CommercialPipelineStage.REPLIED: {
        CommercialPipelineStage.SITE_SURVEY_REQUESTED,
        CommercialPipelineStage.NEGOTIATION,
        CommercialPipelineStage.DO_NOT_CONTACT,
    },
    CommercialPipelineStage.SITE_SURVEY_REQUESTED: {CommercialPipelineStage.QUOTATION_SUBMITTED, CommercialPipelineStage.LOST},
    CommercialPipelineStage.QUOTATION_SUBMITTED: {CommercialPipelineStage.NEGOTIATION, CommercialPipelineStage.WON, CommercialPipelineStage.LOST},
    CommercialPipelineStage.NEGOTIATION: {CommercialPipelineStage.WON, CommercialPipelineStage.LOST},
    CommercialPipelineStage.WON: set(),
    CommercialPipelineStage.LOST: set(),
    CommercialPipelineStage.DO_NOT_CONTACT: set(),
}


def _append_history(prospect: CommercialProspect, event: str, detail: str) -> None:
    hist = list(prospect.contact_history_json or [])
    hist.append({"at": datetime.now(UTC).isoformat(), "event": event, "detail": detail})
    prospect.contact_history_json = hist


async def transition_pipeline(
    db: AsyncSession,
    prospect: CommercialProspect,
    new_stage: CommercialPipelineStage,
    *,
    note: str = "",
) -> tuple[bool, str]:
    if prospect.opt_out and new_stage != CommercialPipelineStage.DO_NOT_CONTACT:
        return False, "Prospect opted out"
    current = prospect.pipeline_stage
    if new_stage not in ALLOWED.get(current, set()) and new_stage != CommercialPipelineStage.DO_NOT_CONTACT:
        return False, f"Invalid transition {current.value} → {new_stage.value}"
    prospect.pipeline_stage = new_stage
    if new_stage == CommercialPipelineStage.DO_NOT_CONTACT:
        prospect.opt_out = True
    _append_history(prospect, "stage_change", f"{current.value} → {new_stage.value}. {note}")
    await db.flush()
    return True, "OK"