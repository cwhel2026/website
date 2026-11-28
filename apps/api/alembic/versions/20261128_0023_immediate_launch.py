"""Remove the superseded March launch restriction, preserving custom dates."""
from alembic import op

revision = "20261128_0023"
down_revision = "20261127_0022"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE scheduling_settings SET earliest_work_date = NULL WHERE earliest_work_date = DATE '2027-03-01'")


def downgrade():
    # Do not reintroduce an obsolete booking restriction or overwrite owner settings.
    pass
