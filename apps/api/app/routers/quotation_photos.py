"""Public photograph upload by secret token, and owner review of repairs."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_admin
from app.database import get_db
from app.models.quotation import Quotation
from app.models.quotation_photo import QuotePhotoSet
from app.models.user import User
from app.rate_limit import limiter
from app.services.quote_photo_store import MAX_UPLOAD_BYTES, photo_file
from app.services.quote_photos import (
    add_photos,
    assess_photo_set,
    load_set,
    new_photo_set,
    record_repair_decision,
    remove_photo,
)

router = APIRouter(prefix="/quotation-photos", tags=["quotation-photos"])


class PhotoOut(BaseModel):
    id: UUID


class PhotoSetOut(BaseModel):
    token: str
    photos: list[PhotoOut]
    note: str | None = None


class ReviewOut(BaseModel):
    id: UUID
    token: str
    quotation_id: UUID | None
    quotation_reference: str | None = None
    quotation_total_gbp: str | None = None
    photo_count: int
    customer_note: str | None = None
    ai_status: str
    ai_summary: str | None = None
    findings: list | None = None
    review_required: bool
    review_status: str
    repair_price_gbp: str | None = None
    repair_note: str | None = None
    marketing_use_allowed: bool


class RepairDecisionIn(BaseModel):
    repair_price_gbp: float | None = None
    repair_note: str = Field(min_length=2, max_length=500)
    approved: bool = True


def _public(photo_set: QuotePhotoSet) -> PhotoSetOut:
    return PhotoSetOut(
        token=photo_set.token,
        photos=[PhotoOut(id=photo.id) for photo in photo_set.photos],
        note=photo_set.customer_note,
    )


@router.get("/admin/reviews", response_model=list[ReviewOut])
async def list_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> list[ReviewOut]:
    rows = (
        await db.execute(
            select(QuotePhotoSet)
            .options(selectinload(QuotePhotoSet.photos))
            .order_by(QuotePhotoSet.created_at.desc())
            .limit(100)
        )
    ).scalars().all()
    return [await _review(db, row) for row in rows]


@router.patch("/admin/sets/{set_id}/repair", response_model=ReviewOut)
async def decide_repair(
    set_id: UUID,
    body: RepairDecisionIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_admin)],
) -> ReviewOut:
    photo_set = await db.get(QuotePhotoSet, set_id)
    if photo_set is None:
        raise HTTPException(status_code=404, detail="Photographs not found")
    price = None if body.repair_price_gbp is None else Decimal(str(body.repair_price_gbp)).quantize(Decimal("0.01"))
    before = None
    if photo_set.quotation_id:
        before = await db.scalar(select(Quotation.total_inc_vat_gbp).where(Quotation.id == photo_set.quotation_id))
    record_repair_decision(
        photo_set,
        repair_price_gbp=price,
        repair_note=body.repair_note,
        approved=body.approved,
    )
    await db.commit()
    photo_set = await db.scalar(
        select(QuotePhotoSet).options(selectinload(QuotePhotoSet.photos)).where(QuotePhotoSet.id == set_id)
    )
    if photo_set is None:
        raise HTTPException(status_code=404, detail="Photographs not found")
    if photo_set.quotation_id and before is not None:
        after = await db.scalar(select(Quotation.total_inc_vat_gbp).where(Quotation.id == photo_set.quotation_id))
        if after != before:
            raise HTTPException(status_code=500, detail="Repair review must not change the quotation total")
    return await _review(db, photo_set)


@router.post("", response_model=PhotoSetOut)
@limiter.limit("20/minute")
async def upload_photos(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    files: Annotated[list[UploadFile], File()],
    token: Annotated[str | None, Form()] = None,
    note: Annotated[str | None, Form()] = None,
    replace_id: Annotated[UUID | None, Form()] = None,
) -> PhotoSetOut:
    del request
    if token:
        photo_set = await load_set(db, token.strip())
    else:
        photo_set = new_photo_set()
        db.add(photo_set)
        await db.flush()
        photo_set = await load_set(db, photo_set.token)
    blobs: list[bytes] = []
    for upload in files:
        raw = await upload.read(MAX_UPLOAD_BYTES + 1)
        blobs.append(raw)
    await add_photos(db, photo_set, blobs, note=note, replace_id=replace_id)
    set_id = photo_set.id
    token_value = photo_set.token
    await db.commit()
    photo_set = await load_set(db, token_value)
    background_tasks.add_task(assess_photo_set, set_id)
    return _public(photo_set)


@router.get("/{token}", response_model=PhotoSetOut)
async def list_photos(token: str, db: Annotated[AsyncSession, Depends(get_db)]) -> PhotoSetOut:
    return _public(await load_set(db, token))


@router.get("/{token}/{photo_id}")
async def download_photo(
    token: str,
    photo_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    photo_set = await load_set(db, token)
    match = next((photo for photo in photo_set.photos if photo.id == photo_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="Photograph not found")
    try:
        path = photo_file(match.storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Photograph not found") from exc
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, no-store"})


@router.delete("/{token}/{photo_id}", response_model=PhotoSetOut)
async def delete_photo(
    token: str,
    photo_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PhotoSetOut:
    photo_set = await load_set(db, token)
    await remove_photo(db, photo_set, photo_id)
    token_value = photo_set.token
    await db.commit()
    return _public(await load_set(db, token_value))


async def _review(db: AsyncSession, photo_set: QuotePhotoSet) -> ReviewOut:
    reference = None
    total = None
    if photo_set.quotation_id:
        quotation = await db.get(Quotation, photo_set.quotation_id)
        if quotation is not None:
            reference = quotation.reference
            total = f"{quotation.total_inc_vat_gbp:.2f}"
    return ReviewOut(
        id=photo_set.id,
        token=photo_set.token,
        quotation_id=photo_set.quotation_id,
        quotation_reference=reference,
        quotation_total_gbp=total,
        photo_count=len(photo_set.photos),
        customer_note=photo_set.customer_note,
        ai_status=photo_set.ai_status,
        ai_summary=photo_set.ai_summary,
        findings=photo_set.findings_json,
        review_required=photo_set.review_required,
        review_status=photo_set.review_status,
        repair_price_gbp=None if photo_set.repair_price_gbp is None else f"{photo_set.repair_price_gbp:.2f}",
        repair_note=photo_set.repair_note,
        marketing_use_allowed=photo_set.marketing_use_allowed,
    )
