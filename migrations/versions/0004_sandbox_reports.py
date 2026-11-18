"""Synthetic lab report revisions. Revision ID: 0004."""

from alembic import op

from services.lifecycle.store import SandboxReport

revision = "0004"
down_revision = "0003"


def upgrade() -> None:
    SandboxReport.__table__.create(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    SandboxReport.__table__.drop(op.get_bind(), checkfirst=True)
