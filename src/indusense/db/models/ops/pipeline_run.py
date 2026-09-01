from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from indusense.db.base import Base


class PipelineRun(Base):
    """Exécution traçable du pipeline Bronze vers Silver."""

    __tablename__ = "pipeline_run"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'failed')",
            name="pipeline_status_domain",
        ),
        {"schema": "ops"},
    )

    run_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    pipeline_version: Mapped[str] = mapped_column(String(32), nullable=False)
    transformation_version: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    metrics: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)

    sources: Mapped[list["PipelineRunSource"]] = relationship(back_populates="run")
    issues: Mapped[list["TransformationIssue"]] = relationship(back_populates="run")
