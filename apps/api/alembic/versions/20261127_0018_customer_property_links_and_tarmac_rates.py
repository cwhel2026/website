"""Link enquiries and quotations to properties; publish tarmac rates.

Revision ID: 20261127_0018
Revises: 20261126_0017

Adds nullable identifiers only. Existing customers, properties, quotes and
pricing rows are kept. A new pricing profile becomes active; the previous
profile is deactivated, not deleted. Invented block-paving and imprinted
concrete per-m² rules are deactivated, not deleted.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.schema import ops as safe

revision: str = "20261127_0018"
down_revision: str | Sequence[str] | None = "20261126_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    safe.add_column(
        "enquiries",
        sa.Column("property_id", sa.UUID(), nullable=True),
    )
    safe.add_column("enquiries", sa.Column("utm_source", sa.String(120), nullable=True))
    safe.add_column("enquiries", sa.Column("utm_medium", sa.String(120), nullable=True))
    safe.add_column("enquiries", sa.Column("utm_campaign", sa.String(120), nullable=True))
    safe.add_column(
        "quotations",
        sa.Column("property_id", sa.UUID(), nullable=True),
    )
    safe.add_column("pricing_rules", sa.Column("label", sa.String(40), nullable=True))
    safe.create_index("ix_enquiries_property_id", "enquiries", ["property_id"])
    safe.create_index("ix_quotations_property_id", "quotations", ["property_id"])

    op.execute(
        """
        DO $$ BEGIN
            ALTER TABLE enquiries
                ADD CONSTRAINT enquiries_property_id_fkey
                FOREIGN KEY (property_id) REFERENCES customer_properties(id);
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            ALTER TABLE quotations
                ADD CONSTRAINT quotations_property_id_fkey
                FOREIGN KEY (property_id) REFERENCES customer_properties(id);
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.execute(
        """
        UPDATE pricing_rules
           SET is_active = false
         WHERE rule_type = 'PER_SQM'
           AND surface_type IN ('BLOCK_PAVING', 'IMPRINTED_CONCRETE')
        """
    )
    op.execute(
        """
        INSERT INTO pricing_profiles (id, name, version, notes, is_active, effective_from, created_at)
        SELECT gen_random_uuid(),
               'surfacecoat-tarmac',
               COALESCE((SELECT MAX(version) FROM pricing_profiles), 0) + 1,
               'Launch tarmac £10/m², standard £12/m², minimum £350 before travel, travel £0.45/mile and £25/hour.',
               true,
               now(),
               now()
         WHERE NOT EXISTS (
             SELECT 1 FROM pricing_profiles WHERE name = 'surfacecoat-tarmac'
         )
        """
    )
    op.execute(
        """
        UPDATE pricing_profiles
           SET is_active = false
         WHERE name <> 'surfacecoat-tarmac'
           AND EXISTS (SELECT 1 FROM pricing_profiles WHERE name = 'surfacecoat-tarmac')
        """
    )
    op.execute("UPDATE pricing_profiles SET is_active = true WHERE name = 'surfacecoat-tarmac'")
    op.execute(
        """
        INSERT INTO pricing_rules (id, profile_id, rule_type, surface_type, amount_gbp, percentage, label, is_active)
        SELECT gen_random_uuid(), p.id, 'PER_SQM', 'TARMAC', 10, NULL, 'launch', true
          FROM pricing_profiles p
         WHERE p.name = 'surfacecoat-tarmac'
           AND NOT EXISTS (
               SELECT 1 FROM pricing_rules r
                WHERE r.profile_id = p.id AND r.label = 'launch' AND r.rule_type = 'PER_SQM'
           )
        """
    )
    op.execute(
        """
        INSERT INTO pricing_rules (id, profile_id, rule_type, surface_type, amount_gbp, percentage, label, is_active)
        SELECT gen_random_uuid(), p.id, 'PER_SQM', 'TARMAC', 12, NULL, 'standard', true
          FROM pricing_profiles p
         WHERE p.name = 'surfacecoat-tarmac'
           AND NOT EXISTS (
               SELECT 1 FROM pricing_rules r
                WHERE r.profile_id = p.id AND r.label = 'standard' AND r.rule_type = 'PER_SQM'
           )
        """
    )
    op.execute(
        """
        INSERT INTO pricing_rules (id, profile_id, rule_type, surface_type, amount_gbp, percentage, label, is_active)
        SELECT gen_random_uuid(), p.id, 'MINIMUM_JOB', NULL, 350, NULL, NULL, true
          FROM pricing_profiles p
         WHERE p.name = 'surfacecoat-tarmac'
           AND NOT EXISTS (
               SELECT 1 FROM pricing_rules r
                WHERE r.profile_id = p.id AND r.rule_type = 'MINIMUM_JOB'
           )
        """
    )
    op.execute(
        """
        INSERT INTO pricing_rules (id, profile_id, rule_type, surface_type, amount_gbp, percentage, label, is_active)
        SELECT gen_random_uuid(), p.id, 'TRAVEL', NULL, 0.45, 25, NULL, true
          FROM pricing_profiles p
         WHERE p.name = 'surfacecoat-tarmac'
           AND NOT EXISTS (
               SELECT 1 FROM pricing_rules r
                WHERE r.profile_id = p.id AND r.rule_type = 'TRAVEL'
           )
        """
    )
    op.execute(
        """
        INSERT INTO pricing_rules (id, profile_id, rule_type, surface_type, amount_gbp, percentage, label, is_active)
        SELECT gen_random_uuid(), p.id, rule.rule_type, NULL, rule.amount, NULL, NULL, true
          FROM pricing_profiles p
          CROSS JOIN (VALUES
              ('VAT_RATE'::pricing_rule_type, 20),
              ('MIN_CONTRIBUTION_MARGIN'::pricing_rule_type, 35),
              ('COMMERCIAL_MULTIPLIER'::pricing_rule_type, 1.30)
          ) AS rule(rule_type, amount)
         WHERE p.name = 'surfacecoat-tarmac'
           AND NOT EXISTS (
               SELECT 1 FROM pricing_rules r
                WHERE r.profile_id = p.id AND r.rule_type = rule.rule_type
           )
        """
    )


def downgrade() -> None:
    op.execute("UPDATE pricing_profiles SET is_active = false WHERE name = 'surfacecoat-tarmac'")
    op.execute(
        """
        UPDATE pricing_profiles SET is_active = true
         WHERE id = (
             SELECT id FROM pricing_profiles
              WHERE name <> 'surfacecoat-tarmac'
              ORDER BY version DESC
              LIMIT 1
         )
        """
    )
