from uuid import UUID

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from indusense.db.base import Base


class PipelineRunSource(Base):
    """Association entre une exécution Silver et un lot Bronze consommé."""

    __tablename__ = "pipeline_run_source"
    __table_args__ = {"schema": "ops"}

    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("ops.pipeline_run.run_id", ondelete="CASCADE"),
        primary_key=True,
    )
    batch_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("ops.ingestion_batch.batch_id", ondelete="RESTRICT"),
        primary_key=True,
    )

    run: Mapped["PipelineRun"] = relationship(back_populates="sources")
