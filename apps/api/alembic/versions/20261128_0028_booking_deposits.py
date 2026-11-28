"""Persist booking deposits and deduplicate payment events."""
from alembic import op
import sqlalchemy as sa

revision = "20261128_0028"
down_revision = "20261128_0027"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "booking_deposits",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("jobs.id"), nullable=False, unique=True),
        sa.Column("invoice_id", sa.Uuid(), sa.ForeignKey("invoices.id"), nullable=True, unique=True),
        sa.Column("total_pence", sa.BigInteger(), nullable=False),
        sa.Column("amount_pence", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("billing_request_id", sa.String(100), unique=True),
        sa.Column("provider_payment_id", sa.String(100), unique=True),
        sa.Column("payment_url", sa.Text()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("amount_pence > 0 AND amount_pence <= total_pence", name="ck_booking_deposit_amount"),
        sa.CheckConstraint("status IN ('draft','pending','confirmed','failed','cancelled','review')", name="ck_booking_deposit_status"),
    )
    op.create_table(
        "booking_payment_events",
        sa.Column("event_id", sa.String(100), primary_key=True),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("payment_id", sa.String(100)),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("booking_payment_events")
    op.drop_table("booking_deposits")
