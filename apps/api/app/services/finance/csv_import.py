import csv
import io
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import BankTransaction, SyncSource


@dataclass
class CsvImportResult:
    imported: int
    skipped_duplicates: int
    errors: list[str]


def _parse_date(value: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


async def import_bank_csv(db: AsyncSession, content: str) -> CsvImportResult:
    """
    Expected columns (flexible headers): date, description, amount
    Mettle/FreeAgent export compatible subset.
    """
    reader = csv.DictReader(io.StringIO(content))
    imported = 0
    skipped = 0
    errors: list[str] = []
    if not reader.fieldnames:
        return CsvImportResult(0, 0, ["CSV has no header row"])

    field_map = {h.lower().strip(): h for h in reader.fieldnames}

    def col(*names: str) -> str | None:
        for n in names:
            if n in field_map:
                return field_map[n]
        return None

    date_col = col("date", "transaction date", "transacted_on")
    desc_col = col("description", "memo", "details")
    amount_col = col("amount", "amount_gbp", "money")
    id_col = col("id", "transaction id", "external_id")

    if not date_col or not desc_col or not amount_col:
        return CsvImportResult(0, 0, ["Required columns: date, description, amount"])

    for i, row in enumerate(reader, start=2):
        dt = _parse_date(row.get(date_col, ""))
        if not dt:
            errors.append(f"Row {i}: invalid date")
            continue
        try:
            amount = Decimal(str(row.get(amount_col, "0")).replace("£", "").replace(",", ""))
        except (InvalidOperation, ValueError):
            errors.append(f"Row {i}: invalid amount")
            continue
        external_id = row.get(id_col) if id_col else None
        if external_id:
            exists = await db.execute(
                select(BankTransaction).where(BankTransaction.external_id == external_id)
            )
            if exists.scalar_one_or_none():
                skipped += 1
                continue
        db.add(
            BankTransaction(
                external_id=external_id,
                description=row.get(desc_col, "")[:255],
                amount_gbp=amount,
                transacted_at=dt.date(),
                source=SyncSource.CSV,
            )
        )
        imported += 1

    return CsvImportResult(imported, skipped, errors)