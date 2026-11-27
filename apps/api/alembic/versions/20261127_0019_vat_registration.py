"""VAT registration is off until an effective date is set.

Revision ID: 20261127_0019
Revises: 20261127_0018

Adds the company VAT effective date and freezes the tax treatment on each
quotation and invoice. Existing rows that already contain VAT keep that
treatment. Unknown company VAT status becomes not registered. Nothing is deleted.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.schema import ops as safe

revision: str = "20261127_0019"
down_revision: str | Sequence[str] | None = "20261127_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    safe.add_column(
        "company_profiles",
        sa.Column("vat_rate_percent", sa.Numeric(5, 2), nullable=False, server_default="20"),
    )
    safe.add_column(
        "company_profiles",
        sa.Column("vat_effective_from", sa.Date(), nullable=True),
    )
    safe.add_column(
        "quotations",
        sa.Column("vat_charged", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    safe.add_column(
        "quotations",
        sa.Column("vat_rate_percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
    )
    safe.add_column(
        "invoices",
        sa.Column("vat_charged", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    safe.add_column(
        "invoices",
        sa.Column("vat_rate_percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
    )
    op.execute(
        "UPDATE company_profiles SET vat_status = 'NOT_REGISTERED' WHERE vat_status::text IN ('unknown', 'UNKNOWN')"
    )
    op.execute(
        """
        UPDATE quotations
           SET vat_charged = true, vat_rate_percent = 20
         WHERE vat_gbp > 0
        """
    )
    op.execute(
        """
        UPDATE invoices
           SET vat_charged = true, vat_rate_percent = 20
         WHERE vat_gbp > 0
        """
    )
    op.execute(
        """
        UPDATE message_templates
           SET body_template = replace(body_template, ' is {{total}} inc. VAT.', ' is {{total}}.')
         WHERE slug = 'quote_delivery'
           AND body_template LIKE '%inc. VAT%'
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE invoices DROP COLUMN IF EXISTS vat_rate_percent")
    op.execute("ALTER TABLE invoices DROP COLUMN IF EXISTS vat_charged")
    op.execute("ALTER TABLE quotations DROP COLUMN IF EXISTS vat_rate_percent")
    op.execute("ALTER TABLE quotations DROP COLUMN IF EXISTS vat_charged")
    op.execute("ALTER TABLE company_profiles DROP COLUMN IF EXISTS vat_effective_from")
    op.execute("ALTER TABLE company_profiles DROP COLUMN IF EXISTS vat_rate_percent")
