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


class IncidentRaw(Base):
    """Ligne brute issue de ``releves_incidents.csv.csv``."""

    __tablename__ = "incident_raw"
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

    incident_id: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[str] = mapped_column(Text, nullable=False)
    time: Mapped[str] = mapped_column(Text, nullable=False)
    operator_name: Mapped[str] = mapped_column(Text, nullable=False)
    machine_id: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    operator_badge: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    shift: Mapped[str] = mapped_column(Text, nullable=False)
    type_surchauffe: Mapped[str] = mapped_column(Text, nullable=False)
    type_baisse_pression: Mapped[str] = mapped_column(Text, nullable=False)
    type_vibration: Mapped[str] = mapped_column(Text, nullable=False)
    type_bruit_mecanique: Mapped[str] = mapped_column(Text, nullable=False)
    type_surconsommation: Mapped[str] = mapped_column(Text, nullable=False)
    type_blocage_mecanique: Mapped[str] = mapped_column(Text, nullable=False)
    type_alarme_capteur: Mapped[str] = mapped_column(Text, nullable=False)
    type_arret_urgence: Mapped[str] = mapped_column(Text, nullable=False)
    type_defaut_qualite: Mapped[str] = mapped_column(Text, nullable=False)
