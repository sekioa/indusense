import csv
import hashlib
import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, sessionmaker

from indusense.db.base import Base
from indusense.db.models import IngestionBatch


BronzeRow = tuple[int, dict[str, str]]
BronzeRowReader = Callable[[Path], Iterator[BronzeRow]]


@dataclass(frozen=True)
class BronzeTarget:
    """Table Bronze et lecteur produisant ses lignes depuis une source."""

    model: type[Base]
    reader: BronzeRowReader


@dataclass(frozen=True)
class BronzeSource:
    """Contrat d'un fichier Bronze et de ses tables de destination."""

    name: str
    path: Path
    targets: tuple[BronzeTarget, ...]


def csv_target(model: type[Base]) -> BronzeTarget:
    """Construit une cible Bronze utilisant le lecteur CSV fidèle à la source."""

    return BronzeTarget(model=model, reader=read_csv_rows)


def sql_insert_target(
    model: type[Base],
    table_name: str,
    *,
    defaults: dict[str, str] | None = None,
) -> BronzeTarget:
    """Construit une cible lisant un bloc ``INSERT`` nommé dans un fichier SQL."""

    return BronzeTarget(
        model=model,
        reader=partial(read_sql_insert_rows, table_name=table_name, defaults=defaults),
    )


def source_sha256(path: Path) -> str:
    """Calcule l'empreinte du fichier sans en modifier le contenu."""
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for block in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_record_hash(row: dict[str, str]) -> str:
    """Produit une empreinte stable d'une ligne Bronze brute."""
    serialized_row = json.dumps(
        row,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized_row.encode("utf-8")).hexdigest()


def read_csv_rows(path: Path) -> Iterator[BronzeRow]:
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


def read_sql_insert_rows(
    path: Path,
    *,
    table_name: str,
    defaults: dict[str, str] | None = None,
) -> Iterator[BronzeRow]:
    """Extrait sans exécution les valeurs d'un bloc ``INSERT INTO`` SQL contrôlé."""

    insert_prefix = f"INSERT INTO {table_name} ("
    columns: list[str] | None = None
    reading_values = False
    row_count = 0

    with path.open(encoding="utf-8") as source_file:
        for source_row_number, source_line in enumerate(source_file, start=1):
            stripped_line = source_line.strip()

            if columns is None:
                if not stripped_line.startswith(insert_prefix):
                    continue

                closing_parenthesis = stripped_line.find(")", len(insert_prefix))
                if closing_parenthesis == -1:
                    raise ValueError(
                        f"En-tête INSERT incomplet pour {table_name} dans {path}"
                    )
                columns = [
                    column.strip()
                    for column in stripped_line[len(insert_prefix) : closing_parenthesis].split(",")
                ]
                continue

            if not reading_values:
                if stripped_line == "VALUES":
                    reading_values = True
                continue

            values_line, separator, _ = stripped_line.partition("ON CONFLICT")
            values_line = values_line.rstrip(",;")

            if values_line:
                if not (values_line.startswith("(") and values_line.endswith(")")):
                    raise ValueError(
                        f"Ligne SQL inattendue pour {table_name} dans {path} "
                        f"à la ligne {source_row_number}"
                    )

                parsed_values = next(
                    csv.reader(
                        [values_line[1:-1]],
                        delimiter=",",
                        quotechar="'",
                        doublequote=True,
                        skipinitialspace=True,
                    )
                )
                if len(parsed_values) != len(columns):
                    raise ValueError(
                        f"Nombre de valeurs invalide pour {table_name} dans {path} "
                        f"à la ligne {source_row_number}"
                    )

                row = {
                    column: "" if value == "NULL" else value
                    for column, value in zip(columns, parsed_values, strict=True)
                }
                row.update(defaults or {})
                row_count += 1
                yield source_row_number, row

            if separator:
                break

    if columns is None:
        raise ValueError(f"Bloc INSERT INTO {table_name} introuvable dans {path}")
    if not reading_values or row_count == 0:
        raise ValueError(f"Aucune valeur INSERT pour {table_name} dans {path}")


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
        target_rows: list[tuple[BronzeTarget, list[dict[str, object]]]] = []
        total_row_count = 0

        for target in source.targets:
            rows = [
                {
                    "batch_id": batch_id,
                    "source_row_number": source_row_number,
                    "record_hash": source_record_hash(row),
                    **row,
                }
                for source_row_number, row in target.reader(source.path)
            ]
            if not rows:
                raise ValueError(
                    f"Aucune ligne pour {target.model.__table__.fullname} dans {source.path}"
                )
            target_rows.append((target, rows))
            total_row_count += len(rows)

        with session_factory.begin() as session:
            for target, rows in target_rows:
                session.execute(target.model.__table__.insert(), rows)
            session.execute(
                update(IngestionBatch)
                .where(IngestionBatch.batch_id == batch_id)
                .values(
                    status="completed",
                    row_count=total_row_count,
                    finished_at=func.now(),
                )
            )
        return "completed", total_row_count
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
