from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from indusense.db.base import Base
from indusense.db.models.silver.lineage import SilverLineageMixin


class Maintenance(SilverLineageMixin, Base):
    """Intervention Silver reliée à sa machine et, si réactive, à son incident."""

    __tablename__ = "maintenance"
    __table_args__ = (
        ForeignKeyConstraint(
            ["related_incident_id", "machine_code"],
            ["silver.incident.incident_id", "silver.incident.machine_code"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "maintenance_type IN ('proactive', 'reactive')",
            name="maintenance_type_domain",
        ),
        CheckConstraint(
            "(maintenance_type = 'proactive' AND related_incident_id IS NULL) "
            "OR (maintenance_type = 'reactive' AND related_incident_id IS NOT NULL)",
            name="incident_required_by_type",
        ),
        CheckConstraint("duration_hours > 0", name="positive_duration"),
        UniqueConstraint("source_batch_id", "source_row_number"),
        Index("ix_maintenance_machine_at", "machine_code", "maintenance_at"),
        Index("ix_maintenance_type", "maintenance_type"),
        Index("ix_maintenance_related_incident", "related_incident_id"),
        {"schema": "silver"},
    )

    maintenance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    machine_code: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("silver.machine.machine_code", ondelete="RESTRICT"),
        nullable=False,
    )
    source_machine_code: Mapped[str] = mapped_column(String(16), nullable=False)
    machine_code_was_aligned: Mapped[bool] = mapped_column(Boolean, nullable=False)
    maintenance_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    maintenance_type: Mapped[str] = mapped_column(String(16), nullable=False)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    component: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    related_incident_id: Mapped[str | None] = mapped_column(String(16))
    duration_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)

    machine: Mapped["Machine"] = relationship(
        back_populates="maintenances",
        foreign_keys=[machine_code],
    )
    incident: Mapped["Incident | None"] = relationship(
        primaryjoin=(
            "and_(Maintenance.related_incident_id == Incident.incident_id, "
            "Maintenance.machine_code == Incident.machine_code)"
        ),
        viewonly=True,
    )
