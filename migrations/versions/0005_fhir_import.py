"""Persist confirmed synthetic FHIR snapshots. Revision ID: 0005."""

from alembic import op

from services.lifecycle.store import FhirImport

revision = "0005"
down_revision = "0004"


def upgrade() -> None:
    FhirImport.__table__.create(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    FhirImport.__table__.drop(op.get_bind(), checkfirst=True)
