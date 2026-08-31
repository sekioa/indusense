import csv
import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, sessionmaker

from indusense.db.models import IncidentRaw, IngestionBatch, MachineMaintenanceRaw, TelemetryRaw


@dataclass(frozen=True)
class BronzeSource:
    """Contrat d'une source CSV Bronze et de sa table de destination."""

    name: str
    path: Path
    model: type[IncidentRaw] | type[MachineMaintenanceRaw] | type[TelemetryRaw]


def source_sha256(path: Path) -> str:
    """Calcule l'empreinte du fichier sans en modifier le contenu."""
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for block in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_record_hash(row: dict[str, str]) -> str:
    """Produit une empreinte stable d'une ligne CSV brute."""
    serialized_row = json.dumps(
        row,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized_row.encode("utf-8")).hexdigest()


def read_source_rows(path: Path) -> Iterator[tuple[int, dict[str, str]]]:
    """Lit les lignes CSV avec les chaînes brutes, y compris les cellules vides."""
    with path.open(encoding="utf-8", newline="") as source_file:
        reader = csv.DictReader(source_file)
        if reader.fieldnames is None:
            raise ValueError(f"Fichier CSV sans en-tête : {path}")

        for source_row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"Ligne CSV trop large dans {path} à la ligne {source_row_number}")
            if any(value is None for value in row.values()):
                raise ValueError(f"Ligne CSV incomplète dans {path} à la ligne {source_row_number}")
            yield source_row_number, row


def ingest_source(session_factory: sessionmaker[Session], source: BronzeSource) -> tuple[str, int]:
    """Charge une source une fois, ou la saute si son empreinte est déjà terminée."""
    file_hash = source_sha256(source.path)

    with session_factory() as session:
        completed_batch = session.scalar(
            select(IngestionBatch.batch_id).where(
                IngestionBatch.source_file == source.path.name,
                IngestionBatch.source_sha256 == file_hash,
                IngestionBatch.status == "completed",
            )
        )
        if completed_batch is not None:
            return "skipped", 0

        batch = IngestionBatch(
            source_file=source.path.name,
            source_sha256=file_hash,
            status="running",
        )
        session.add(batch)
        session.commit()
        batch_id = batch.batch_id

    try:
        rows = [
            {
                "batch_id": batch_id,
                "source_row_number": source_row_number,
                "record_hash": source_record_hash(row),
                **row,
            }
            for source_row_number, row in read_source_rows(source.path)
        ]

        with session_factory.begin() as session:
            session.execute(source.model.__table__.insert(), rows)
            session.execute(
                update(IngestionBatch)
                .where(IngestionBatch.batch_id == batch_id)
                .values(status="completed", row_count=len(rows), finished_at=func.now())
            )
        return "completed", len(rows)
    except Exception as error:
        with session_factory.begin() as session:
            session.execute(
                update(IngestionBatch)
                .where(IngestionBatch.batch_id == batch_id)
                .values(
                    status="failed",
                    error_message=str(error)[:4000],
                    finished_at=func.now(),
                )
            )
        raise
