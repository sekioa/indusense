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


class MaintenanceRaw(Base):
    """Ligne maintenance brute extraite du bloc ``INSERT`` de ``machine.sql``."""

    __tablename__ = "maintenance_raw"
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

    maintenance_id: Mapped[str] = mapped_column(Text, nullable=False)
    machine_code: Mapped[str] = mapped_column(Text, nullable=False)
    maintenance_at: Mapped[str] = mapped_column(Text, nullable=False)
    maintenance_type: Mapped[str] = mapped_column(Text, nullable=False)
    action_type: Mapped[str] = mapped_column(Text, nullable=False)
    component: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    related_incident_id: Mapped[str] = mapped_column(Text, nullable=False)
    duration_hours: Mapped[str] = mapped_column(Text, nullable=False)
