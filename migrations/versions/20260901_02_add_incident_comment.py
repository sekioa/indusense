"""retain incident comments in silver

Revision ID: 20260901_02
Revises: 20260901_01
Create Date: 2026-09-01 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260901_02"
down_revision: str | Sequence[str] | None = "20260901_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "incident",
        sa.Column("comment", sa.Text(), nullable=True),
        schema="silver",
    )
    op.execute("UPDATE silver.incident SET comment = '' WHERE comment IS NULL")
    op.alter_column("incident", "comment", nullable=False, schema="silver")


def downgrade() -> None:
    op.drop_column("incident", "comment", schema="silver")
