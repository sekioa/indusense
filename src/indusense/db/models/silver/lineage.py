from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column


class SilverLineageMixin:
    """Colonnes communes reliant une ligne Silver à sa source et à son exécution."""

    source_batch_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("ops.ingestion_batch.batch_id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_record_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    pipeline_run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("ops.pipeline_run.run_id", ondelete="RESTRICT"),
        nullable=False,
    )
    transformation_version: Mapped[str] = mapped_column(String(32), nullable=False)
    silver_processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
