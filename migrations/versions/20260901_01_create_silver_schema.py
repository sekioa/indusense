"""create silver schema and pipeline tracking

Revision ID: 20260901_01
Revises: 20260831_01
Create Date: 2026-09-01 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260901_01"
down_revision: str | Sequence[str] | None = "20260831_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _lineage_columns() -> list[sa.Column]:
    return [
        sa.Column("source_batch_id", sa.Uuid(), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
        sa.Column("source_record_hash", sa.String(length=64), nullable=False),
        sa.Column("pipeline_run_id", sa.Uuid(), nullable=False),
        sa.Column("transformation_version", sa.String(length=32), nullable=False),
        sa.Column(
            "silver_processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def _lineage_constraints(table_name: str) -> list[sa.Constraint]:
    return [
        sa.ForeignKeyConstraint(
            ["source_batch_id"],
            ["ops.ingestion_batch.batch_id"],
            name=f"fk_{table_name}_source_batch_id_ingestion_batch",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["pipeline_run_id"],
            ["ops.pipeline_run.run_id"],
            name=f"fk_{table_name}_pipeline_run_id_pipeline_run",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "source_batch_id",
            "source_row_number",
            name=f"uq_{table_name}_source_batch_id",
        ),
    ]


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS silver")

    op.create_table(
        "pipeline_run",
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("pipeline_version", sa.String(length=32), nullable=False),
        sa.Column("transformation_version", sa.String(length=32), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('running', 'completed', 'failed')",
            name="ck_pipeline_run_pipeline_status_domain",
        ),
        sa.PrimaryKeyConstraint("run_id", name="pk_pipeline_run"),
        schema="ops",
    )
    op.create_table(
        "pipeline_run_source",
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["ops.pipeline_run.run_id"],
            name="fk_pipeline_run_source_run_id_pipeline_run",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["ops.ingestion_batch.batch_id"],
            name="fk_pipeline_run_source_batch_id_ingestion_batch",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("run_id", "batch_id", name="pk_pipeline_run_source"),
        schema="ops",
    )
    op.create_table(
        "transformation_issue",
        sa.Column("issue_id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("source_batch_id", sa.Uuid(), nullable=False),
        sa.Column("source_table", sa.String(length=64), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
        sa.Column("source_record_hash", sa.String(length=64), nullable=False),
        sa.Column("target_table", sa.String(length=64), nullable=False),
        sa.Column("rule_code", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("original_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "severity IN ('warning', 'rejected')",
            name="ck_transformation_issue_issue_severity_domain",
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["ops.pipeline_run.run_id"],
            name="fk_transformation_issue_run_id_pipeline_run",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_batch_id"],
            ["ops.ingestion_batch.batch_id"],
            name="fk_transformation_issue_source_batch_id_ingestion_batch",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("issue_id", name="pk_transformation_issue"),
        schema="ops",
    )
    op.create_index(
        "ix_transformation_issue_run_id",
        "transformation_issue",
        ["run_id"],
        schema="ops",
    )

    op.create_table(
        "machine",
        sa.Column("machine_code", sa.String(length=16), nullable=False),
        sa.Column("commissioning_date", sa.Date(), nullable=False),
        sa.Column("max_daily_capacity", sa.Integer(), nullable=False),
        sa.Column("max_hourly_capacity_pieces", sa.Integer(), nullable=False),
        sa.Column("model", sa.String(length=32), nullable=False),
        sa.Column("production_line", sa.String(length=16), nullable=False),
        sa.Column("location", sa.String(length=16), nullable=False),
        sa.Column("criticality", sa.String(length=8), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_lineage_columns(),
        sa.CheckConstraint(
            "max_daily_capacity > 0",
            name="ck_machine_positive_daily_capacity",
        ),
        sa.CheckConstraint(
            "max_hourly_capacity_pieces > 0",
            name="ck_machine_positive_hourly_capacity",
        ),
        sa.CheckConstraint(
            "criticality IN ('LOW', 'MEDIUM', 'HIGH')",
            name="ck_machine_criticality_domain",
        ),
        *_lineage_constraints("machine"),
        sa.PrimaryKeyConstraint("machine_code", name="pk_machine"),
        schema="silver",
    )
    op.create_index("ix_machine_location", "machine", ["location"], schema="silver")
    op.create_index(
        "ix_machine_production_line",
        "machine",
        ["production_line"],
        schema="silver",
    )

    op.create_table(
        "incident",
        sa.Column("incident_id", sa.String(length=16), nullable=False),
        sa.Column("machine_code", sa.String(length=16), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("severity", sa.SmallInteger(), nullable=False),
        sa.Column("is_overheating", sa.Boolean(), nullable=False),
        sa.Column("is_pressure_drop", sa.Boolean(), nullable=False),
        sa.Column("is_vibration", sa.Boolean(), nullable=False),
        sa.Column("is_mechanical_noise", sa.Boolean(), nullable=False),
        sa.Column("is_overconsumption", sa.Boolean(), nullable=False),
        sa.Column("is_mechanical_blockage", sa.Boolean(), nullable=False),
        sa.Column("is_sensor_alarm", sa.Boolean(), nullable=False),
        sa.Column("is_emergency_stop", sa.Boolean(), nullable=False),
        sa.Column("is_quality_defect", sa.Boolean(), nullable=False),
        *_lineage_columns(),
        sa.CheckConstraint(
            "severity BETWEEN 1 AND 5",
            name="ck_incident_severity_domain",
        ),
        sa.ForeignKeyConstraint(
            ["machine_code"],
            ["silver.machine.machine_code"],
            name="fk_incident_machine_code_machine",
            ondelete="RESTRICT",
        ),
        *_lineage_constraints("incident"),
        sa.PrimaryKeyConstraint("incident_id", name="pk_incident"),
        sa.UniqueConstraint(
            "incident_id",
            "machine_code",
            name="uq_incident_incident_id",
        ),
        schema="silver",
    )
    op.create_index(
        "ix_incident_machine_occurred_at",
        "incident",
        ["machine_code", "occurred_at"],
        schema="silver",
    )

    op.create_table(
        "maintenance",
        sa.Column("maintenance_id", sa.Integer(), nullable=False),
        sa.Column("machine_code", sa.String(length=16), nullable=False),
        sa.Column("source_machine_code", sa.String(length=16), nullable=False),
        sa.Column("machine_code_was_aligned", sa.Boolean(), nullable=False),
        sa.Column("maintenance_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("maintenance_type", sa.String(length=16), nullable=False),
        sa.Column("action_type", sa.String(length=32), nullable=False),
        sa.Column("component", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("related_incident_id", sa.String(length=16), nullable=True),
        sa.Column("duration_hours", sa.Numeric(precision=6, scale=2), nullable=False),
        *_lineage_columns(),
        sa.CheckConstraint(
            "maintenance_type IN ('proactive', 'reactive')",
            name="ck_maintenance_maintenance_type_domain",
        ),
        sa.CheckConstraint(
            "(maintenance_type = 'proactive' AND related_incident_id IS NULL) "
            "OR (maintenance_type = 'reactive' AND related_incident_id IS NOT NULL)",
            name="ck_maintenance_incident_required_by_type",
        ),
        sa.CheckConstraint(
            "duration_hours > 0",
            name="ck_maintenance_positive_duration",
        ),
        sa.ForeignKeyConstraint(
            ["machine_code"],
            ["silver.machine.machine_code"],
            name="fk_maintenance_machine_code_machine",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["related_incident_id", "machine_code"],
            ["silver.incident.incident_id", "silver.incident.machine_code"],
            name="fk_maintenance_related_incident_id_incident",
            ondelete="RESTRICT",
        ),
        *_lineage_constraints("maintenance"),
        sa.PrimaryKeyConstraint("maintenance_id", name="pk_maintenance"),
        schema="silver",
    )
    op.create_index(
        "ix_maintenance_machine_at",
        "maintenance",
        ["machine_code", "maintenance_at"],
        schema="silver",
    )
    op.create_index(
        "ix_maintenance_related_incident",
        "maintenance",
        ["related_incident_id"],
        schema="silver",
    )
    op.create_index(
        "ix_maintenance_type",
        "maintenance",
        ["maintenance_type"],
        schema="silver",
    )

    op.create_table(
        "telemetry",
        sa.Column("telemetry_id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("machine_code", sa.String(length=16), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature_c", sa.Double(), nullable=True),
        sa.Column("pressure_bar", sa.Double(), nullable=True),
        sa.Column("voltage_mean_v", sa.Double(), nullable=True),
        sa.Column("rotation_mean_rpm", sa.Double(), nullable=True),
        sa.Column("pieces_produced", sa.Integer(), nullable=False),
        *_lineage_columns(),
        sa.CheckConstraint(
            "temperature_c IS NULL OR temperature_c >= 0",
            name="ck_telemetry_non_negative_temperature",
        ),
        sa.CheckConstraint(
            "pressure_bar IS NULL OR pressure_bar >= 0",
            name="ck_telemetry_non_negative_pressure",
        ),
        sa.CheckConstraint(
            "voltage_mean_v IS NULL OR voltage_mean_v >= 0",
            name="ck_telemetry_non_negative_voltage",
        ),
        sa.CheckConstraint(
            "rotation_mean_rpm IS NULL OR rotation_mean_rpm >= 0",
            name="ck_telemetry_non_negative_rotation",
        ),
        sa.CheckConstraint(
            "pieces_produced >= 0",
            name="ck_telemetry_non_negative_pieces",
        ),
        sa.ForeignKeyConstraint(
            ["machine_code"],
            ["silver.machine.machine_code"],
            name="fk_telemetry_machine_code_machine",
            ondelete="RESTRICT",
        ),
        *_lineage_constraints("telemetry"),
        sa.PrimaryKeyConstraint("telemetry_id", name="pk_telemetry"),
        sa.UniqueConstraint(
            "machine_code",
            "measured_at",
            name="uq_telemetry_machine_code",
        ),
        schema="silver",
    )


def downgrade() -> None:
    for table_name in ("telemetry", "maintenance", "incident", "machine"):
        op.drop_table(table_name, schema="silver")
    op.drop_table("transformation_issue", schema="ops")
    op.drop_table("pipeline_run_source", schema="ops")
    op.drop_table("pipeline_run", schema="ops")
    op.execute("DROP SCHEMA silver")
