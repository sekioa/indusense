from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Double, ForeignKey, Identity, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from indusense.db.base import Base
from indusense.db.models.silver.lineage import SilverLineageMixin


class Telemetry(SilverLineageMixin, Base):
    """Mesure Silver unique par machine et par instant UTC."""

    __tablename__ = "telemetry"
    __table_args__ = (
        CheckConstraint(
            "temperature_c IS NULL OR temperature_c >= 0",
            name="non_negative_temperature",
        ),
        CheckConstraint(
            "pressure_bar IS NULL OR pressure_bar >= 0",
            name="non_negative_pressure",
        ),
        CheckConstraint(
            "voltage_mean_v IS NULL OR voltage_mean_v >= 0",
            name="non_negative_voltage",
        ),
        CheckConstraint(
            "rotation_mean_rpm IS NULL OR rotation_mean_rpm >= 0",
            name="non_negative_rotation",
        ),
        CheckConstraint("pieces_produced >= 0", name="non_negative_pieces"),
        UniqueConstraint("machine_code", "measured_at"),
        UniqueConstraint("source_batch_id", "source_row_number"),
        {"schema": "silver"},
    )

    telemetry_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )
    machine_code: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("silver.machine.machine_code", ondelete="RESTRICT"),
        nullable=False,
    )
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    temperature_c: Mapped[float | None] = mapped_column(Double)
    pressure_bar: Mapped[float | None] = mapped_column(Double)
    voltage_mean_v: Mapped[float | None] = mapped_column(Double)
    rotation_mean_rpm: Mapped[float | None] = mapped_column(Double)
    pieces_produced: Mapped[int] = mapped_column(Integer, nullable=False)

    machine: Mapped["Machine"] = relationship(back_populates="telemetry")
