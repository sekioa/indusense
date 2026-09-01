from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from indusense.db.base import Base
from indusense.db.models.silver.lineage import SilverLineageMixin


class Incident(SilverLineageMixin, Base):
    """Incident Silver typé, minimisé et relié à sa machine."""

    __tablename__ = "incident"
    __table_args__ = (
        CheckConstraint("severity BETWEEN 1 AND 5", name="severity_domain"),
        UniqueConstraint("incident_id", "machine_code"),
        UniqueConstraint("source_batch_id", "source_row_number"),
        Index("ix_incident_machine_occurred_at", "machine_code", "occurred_at"),
        {"schema": "silver"},
    )

    incident_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    machine_code: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("silver.machine.machine_code", ondelete="RESTRICT"),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    severity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_overheating: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_pressure_drop: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_vibration: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_mechanical_noise: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_overconsumption: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_mechanical_blockage: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_sensor_alarm: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_emergency_stop: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_quality_defect: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)

    machine: Mapped["Machine"] = relationship(back_populates="incidents")
    maintenances: Mapped[list["Maintenance"]] = relationship(
        primaryjoin=(
            "and_(Incident.incident_id == Maintenance.related_incident_id, "
            "Incident.machine_code == Maintenance.machine_code)"
        ),
        viewonly=True,
    )
