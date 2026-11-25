from decimal import Decimal

from app.models.finance import BankTransaction, Receipt, SyncSource
from app.services.finance.receipt_accounting import AccountingRoute, classify_receipt_route


def test_classify_company_bank():
    receipt = Receipt(filename="x.jpg", payment_method="card")
    txn = BankTransaction(
        description="SCREWFIX",
        amount_gbp=Decimal("-50"),
        transacted_at=__import__("datetime").date.today(),
        source=SyncSource.FREEAGENT,
        is_reconciled=False,
    )
    assert classify_receipt_route(receipt, txn) == AccountingRoute.COMPANY_BANK


def test_classify_already_reconciled():
    receipt = Receipt(filename="x.jpg")
    txn = BankTransaction(
        description="Fuel",
        amount_gbp=Decimal("-40"),
        transacted_at=__import__("datetime").date.today(),
        source=SyncSource.FREEAGENT,
        is_reconciled=True,
    )
    assert classify_receipt_route(receipt, txn) == AccountingRoute.ALREADY_RECONCILED


def test_classify_personal_payment_method():
    receipt = Receipt(filename="x.jpg", payment_method="personal cash", extracted_total_gbp=Decimal("20"))
    assert classify_receipt_route(receipt, None) == AccountingRoute.PERSONAL_DIRECTOR


def test_unmatched_with_total_not_personal():
    receipt = Receipt(filename="x.jpg", payment_method="card", extracted_total_gbp=Decimal("20"))
    assert classify_receipt_route(receipt, None) == AccountingRoute.UNMATCHED