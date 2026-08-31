from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from indusense.db.base import Base


class TelemetryRaw(Base):
    """Ligne brute issue de ``telemetry.csv.csv``."""

    __tablename__ = "telemetry_raw"
    __table_args__ = (
        UniqueConstraint("batch_id", "source_row_number"),
        {"schema": "bronze"},
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    batch_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("ops.ingestion_batch.batch_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    record_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    machine_id: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[str] = mapped_column(Text, nullable=False)
    temperature_c: Mapped[str] = mapped_column(Text, nullable=False)
    pressure_bar: Mapped[str] = mapped_column(Text, nullable=False)
    voltage_mean_v: Mapped[str] = mapped_column(Text, nullable=False)
    rotation_mean_rpm: Mapped[str] = mapped_column(Text, nullable=False)
    pieces_produced: Mapped[str] = mapped_column(Text, nullable=False)
