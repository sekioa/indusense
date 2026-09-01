from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from indusense.db.base import Base


class TransformationIssue(Base):
    """Rejet, avertissement ou doublon tracé pendant une transformation Silver."""

    __tablename__ = "transformation_issue"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('warning', 'rejected')",
            name="issue_severity_domain",
        ),
        {"schema": "ops"},
    )

    issue_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("ops.pipeline_run.run_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_batch_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("ops.ingestion_batch.batch_id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_table: Mapped[str] = mapped_column(String(64), nullable=False)
    source_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_record_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    target_table: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    original_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    run: Mapped["PipelineRun"] = relationship(back_populates="issues")
