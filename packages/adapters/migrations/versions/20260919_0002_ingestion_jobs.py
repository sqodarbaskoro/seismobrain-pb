"""Durable ingestion jobs, progress, and database dispatch outbox."""
from alembic import op

from seismobrain_adapters.queue.job_store import metadata

revision = '20260919_0002'
down_revision = '20260916_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    metadata.create_all(op.get_bind())


def downgrade() -> None:
    metadata.drop_all(op.get_bind())
