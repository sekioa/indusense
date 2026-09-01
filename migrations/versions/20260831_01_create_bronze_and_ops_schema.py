"""create bronze and ops schema

Revision ID: 20260831_01
Revises:
Create Date: 2026-08-31 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260831_01"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _bronze_table(name: str, source_columns: list[str]) -> None:
    op.create_table(
        name,
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
        sa.Column("record_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        *(sa.Column(column_name, sa.Text(), nullable=False) for column_name in source_columns),
        sa.ForeignKeyConstraint(["batch_id"], ["ops.ingestion_batch.batch_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("batch_id", "source_row_number"),
        schema="bronze",
    )
    op.create_index(f"ix_{name}_batch_id", name, ["batch_id"], schema="bronze")


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS ops")
    op.execute("CREATE SCHEMA IF NOT EXISTS bronze")

    op.create_table(
        "ingestion_batch",
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("source_file", sa.Text(), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("batch_id"),
        schema="ops",
    )
    op.create_index(
        "ix_ingestion_batch_source_sha256",
        "ingestion_batch",
        ["source_sha256"],
        schema="ops",
    )

    _bronze_table(
        "machine_raw",
        [
            "machine_code", "commissioning_date", "max_daily_capacity",
            "max_hourly_capacity_pieces", "model", "production_line", "location", "criticality",
            "is_active",
        ],
    )
    _bronze_table(
        "maintenance_raw",
        [
            "maintenance_id", "machine_code", "maintenance_at", "maintenance_type",
            "action_type", "component", "description", "related_incident_id", "duration_hours",
        ],
    )
    _bronze_table(
        "incident_raw",
        [
            "incident_id", "date", "time", "operator_name", "machine_id", "severity",
            "operator_badge", "comment", "shift", "type_surchauffe", "type_baisse_pression",
            "type_vibration", "type_bruit_mecanique", "type_surconsommation",
            "type_blocage_mecanique", "type_alarme_capteur", "type_arret_urgence",
            "type_defaut_qualite",
        ],
    )
    _bronze_table(
        "telemetry_raw",
        [
            "machine_id", "timestamp", "temperature_c", "pressure_bar", "voltage_mean_v",
            "rotation_mean_rpm", "pieces_produced",
        ],
    )


def downgrade() -> None:
    for table_name in ("telemetry_raw", "incident_raw", "maintenance_raw", "machine_raw"):
        op.drop_table(table_name, schema="bronze")
    op.drop_table("ingestion_batch", schema="ops")
    op.execute("DROP SCHEMA bronze")
    op.execute("DROP SCHEMA ops")
