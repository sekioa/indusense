from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from indusense.db.base import Base
from indusense.db.models.silver.lineage import SilverLineageMixin


class Machine(SilverLineageMixin, Base):
    """Référentiel Silver des machines dans leur état courant."""

    __tablename__ = "machine"
    __table_args__ = (
        CheckConstraint("max_daily_capacity > 0", name="positive_daily_capacity"),
        CheckConstraint(
            "max_hourly_capacity_pieces > 0",
            name="positive_hourly_capacity",
        ),
        CheckConstraint(
            "criticality IN ('LOW', 'MEDIUM', 'HIGH')",
            name="criticality_domain",
        ),
        UniqueConstraint("source_batch_id", "source_row_number"),
        Index("ix_machine_production_line", "production_line"),
        Index("ix_machine_location", "location"),
        {"schema": "silver"},
    )

    machine_code: Mapped[str] = mapped_column(String(16), primary_key=True)
    commissioning_date: Mapped[date] = mapped_column(Date, nullable=False)
    max_daily_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    max_hourly_capacity_pieces: Mapped[int] = mapped_column(Integer, nullable=False)
    model: Mapped[str] = mapped_column(String(32), nullable=False)
    production_line: Mapped[str] = mapped_column(String(16), nullable=False)
    location: Mapped[str] = mapped_column(String(16), nullable=False)
    criticality: Mapped[str] = mapped_column(String(8), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    incidents: Mapped[list["Incident"]] = relationship(back_populates="machine")
    maintenances: Mapped[list["Maintenance"]] = relationship(back_populates="machine")
    telemetry: Mapped[list["Telemetry"]] = relationship(back_populates="machine")
