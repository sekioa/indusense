import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, sessionmaker

from indusense.db.models import (
    Incident,
    IncidentRaw,
    IngestionBatch,
    Machine,
    MachineRaw,
    Maintenance,
    MaintenanceRaw,
    PipelineRun,
    PipelineRunSource,
    Telemetry,
    TelemetryRaw,
    TransformationIssue,
)


PIPELINE_VERSION = "1.1.0"
TRANSFORMATION_VERSION = "20260901_02"
SOURCE_FILES = ("machine.sql", "releves_incidents.csv", "telemetry.csv")
INSERT_CHUNK_SIZE = 5_000


@dataclass(frozen=True)
class SilverDataset:
    machines: list[dict[str, object]]
    incidents: list[dict[str, object]]
    maintenances: list[dict[str, object]]
    telemetry: list[dict[str, object]]
    issues: list[dict[str, object]]
    metrics: dict[str, object]


@dataclass(frozen=True)
class SilverBuildResult:
    run_id: UUID
    metrics: dict[str, object]


class SilverDataQualityError(ValueError):
    """Violation bloquante du contrat Silver reliée à une ligne Bronze."""

    def __init__(
        self,
        message: str,
        *,
        raw_row: object,
        source_table: str,
        target_table: str,
        rule_code: str,
    ) -> None:
        super().__init__(message)
        self.raw_row = raw_row
        self.source_table = source_table
        self.target_table = target_table
        self.rule_code = rule_code


def _quality_error(
    raw_row: object,
    *,
    source_table: str,
    target_table: str,
    rule_code: str,
    message: str,
) -> SilverDataQualityError:
    return SilverDataQualityError(
        message,
        raw_row=raw_row,
        source_table=source_table,
        target_table=target_table,
        rule_code=rule_code,
    )


def _required_text(
    value: str,
    *,
    raw_row: object,
    source_table: str,
    target_table: str,
    column: str,
) -> str:
    normalized = value.strip()
    if not normalized:
        raise _quality_error(
            raw_row,
            source_table=source_table,
            target_table=target_table,
            rule_code="REQUIRED_VALUE",
            message=f"Valeur obligatoire vide : {source_table}.{column}",
        )
    return normalized


def _integer(
    value: str,
    *,
    raw_row: object,
    source_table: str,
    target_table: str,
    column: str,
) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise _quality_error(
            raw_row,
            source_table=source_table,
            target_table=target_table,
            rule_code="INVALID_INTEGER",
            message=f"Entier invalide : {source_table}.{column}={value!r}",
        ) from error


def _optional_non_negative_float(
    value: str,
    *,
    raw_row: object,
    column: str,
) -> float | None:
    if not value.strip():
        return None
    try:
        parsed = float(value)
    except ValueError as error:
        raise _quality_error(
            raw_row,
            source_table="bronze.telemetry_raw",
            target_table="silver.telemetry",
            rule_code="INVALID_NUMBER",
            message=f"Nombre invalide : bronze.telemetry_raw.{column}={value!r}",
        ) from error
    if not math.isfinite(parsed) or parsed < 0:
        raise _quality_error(
            raw_row,
            source_table="bronze.telemetry_raw",
            target_table="silver.telemetry",
            rule_code="INVALID_MEASUREMENT",
            message=f"Mesure négative ou non finie : {column}={value!r}",
        )
    return parsed


def _boolean(
    value: str,
    *,
    raw_row: object,
    source_table: str,
    target_table: str,
    column: str,
) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true"}:
        return True
    if normalized in {"0", "false"}:
        return False
    raise _quality_error(
        raw_row,
        source_table=source_table,
        target_table=target_table,
        rule_code="INVALID_BOOLEAN",
        message=f"Booléen invalide : {source_table}.{column}={value!r}",
    )


def _utc_datetime(
    value: str,
    *,
    raw_row: object,
    source_table: str,
    target_table: str,
    column: str,
) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise _quality_error(
            raw_row,
            source_table=source_table,
            target_table=target_table,
            rule_code="INVALID_TIMESTAMP",
            message=f"Timestamp invalide : {source_table}.{column}={value!r}",
        ) from error
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _lineage(raw_row: object, run_id: UUID) -> dict[str, object]:
    return {
        "source_batch_id": raw_row.batch_id,
        "source_row_number": raw_row.source_row_number,
        "source_record_hash": raw_row.record_hash,
        "pipeline_run_id": run_id,
        "transformation_version": TRANSFORMATION_VERSION,
    }


def _raw_payload(raw_row: object) -> dict[str, object]:
    technical_columns = {"id", "batch_id", "record_hash", "ingested_at"}
    return {
        column.name: getattr(raw_row, column.name)
        for column in raw_row.__table__.columns
        if column.name not in technical_columns
    }


def _machine_row(raw: MachineRaw, run_id: UUID) -> dict[str, object]:
    source = "bronze.machine_raw"
    target = "silver.machine"
    machine_code = _required_text(
        raw.machine_code,
        raw_row=raw,
        source_table=source,
        target_table=target,
        column="machine_code",
    ).upper()
    try:
        commissioning_date = date.fromisoformat(raw.commissioning_date)
    except ValueError as error:
        raise _quality_error(
            raw,
            source_table=source,
            target_table=target,
            rule_code="INVALID_DATE",
            message=f"Date de mise en service invalide : {raw.commissioning_date!r}",
        ) from error
    daily_capacity = _integer(
        raw.max_daily_capacity,
        raw_row=raw,
        source_table=source,
        target_table=target,
        column="max_daily_capacity",
    )
    hourly_capacity = _integer(
        raw.max_hourly_capacity_pieces,
        raw_row=raw,
        source_table=source,
        target_table=target,
        column="max_hourly_capacity_pieces",
    )
    if daily_capacity <= 0 or hourly_capacity <= 0:
        raise _quality_error(
            raw,
            source_table=source,
            target_table=target,
            rule_code="INVALID_CAPACITY",
            message=f"Capacité non positive pour {machine_code}",
        )
    criticality = raw.criticality.strip().upper()
    if criticality not in {"LOW", "MEDIUM", "HIGH"}:
        raise _quality_error(
            raw,
            source_table=source,
            target_table=target,
            rule_code="INVALID_CRITICALITY",
            message=f"Criticité invalide : {raw.criticality!r}",
        )
    return {
        "machine_code": machine_code,
        "commissioning_date": commissioning_date,
        "max_daily_capacity": daily_capacity,
        "max_hourly_capacity_pieces": hourly_capacity,
        "model": raw.model.strip(),
        "production_line": raw.production_line.strip(),
        "location": raw.location.strip(),
        "criticality": criticality,
        "is_active": _boolean(
            raw.is_active,
            raw_row=raw,
            source_table=source,
            target_table=target,
            column="is_active",
        ),
        **_lineage(raw, run_id),
    }


def _incident_row(raw: IncidentRaw, run_id: UUID) -> dict[str, object]:
    source = "bronze.incident_raw"
    target = "silver.incident"
    severity = _integer(
        raw.severity,
        raw_row=raw,
        source_table=source,
        target_table=target,
        column="severity",
    )
    if severity not in range(1, 6):
        raise _quality_error(
            raw,
            source_table=source,
            target_table=target,
            rule_code="INVALID_SEVERITY",
            message=f"Gravité hors domaine : {severity}",
        )

    boolean_columns = {
        "is_overheating": "type_surchauffe",
        "is_pressure_drop": "type_baisse_pression",
        "is_vibration": "type_vibration",
        "is_mechanical_noise": "type_bruit_mecanique",
        "is_overconsumption": "type_surconsommation",
        "is_mechanical_blockage": "type_blocage_mecanique",
        "is_sensor_alarm": "type_alarme_capteur",
        "is_emergency_stop": "type_arret_urgence",
        "is_quality_defect": "type_defaut_qualite",
    }
    flags = {
        target_column: _boolean(
            getattr(raw, source_column),
            raw_row=raw,
            source_table=source,
            target_table=target,
            column=source_column,
        )
        for target_column, source_column in boolean_columns.items()
    }
    return {
        "incident_id": raw.incident_id.strip().upper(),
        "machine_code": raw.machine_id.strip().upper(),
        "occurred_at": _utc_datetime(
            f"{raw.date.strip()}T{raw.time.strip()}",
            raw_row=raw,
            source_table=source,
            target_table=target,
            column="date+time",
        ),
        "severity": severity,
        **flags,
        "comment": raw.comment.strip(),
        **_lineage(raw, run_id),
    }


def _maintenance_row(
    raw: MaintenanceRaw,
    run_id: UUID,
    machine_codes: set[str],
    incidents: dict[str, dict[str, object]],
) -> dict[str, object]:
    source = "bronze.maintenance_raw"
    target = "silver.maintenance"
    source_machine_code = raw.machine_code.strip().upper()
    if source_machine_code not in machine_codes:
        raise _quality_error(
            raw,
            source_table=source,
            target_table=target,
            rule_code="UNKNOWN_MACHINE",
            message=f"Machine source inconnue : {source_machine_code}",
        )
    maintenance_type = raw.maintenance_type.strip().lower()
    related_incident_id = raw.related_incident_id.strip().upper() or None
    if maintenance_type == "reactive":
        if related_incident_id not in incidents:
            raise _quality_error(
                raw,
                source_table=source,
                target_table=target,
                rule_code="UNKNOWN_RELATED_INCIDENT",
                message=f"Incident lié inconnu : {related_incident_id!r}",
            )
        machine_code = str(incidents[related_incident_id]["machine_code"])
    elif maintenance_type == "proactive":
        if related_incident_id is not None:
            raise _quality_error(
                raw,
                source_table=source,
                target_table=target,
                rule_code="UNEXPECTED_RELATED_INCIDENT",
                message="Une maintenance proactive ne doit pas référencer d'incident",
            )
        machine_code = source_machine_code
    else:
        raise _quality_error(
            raw,
            source_table=source,
            target_table=target,
            rule_code="INVALID_MAINTENANCE_TYPE",
            message=f"Type de maintenance invalide : {maintenance_type!r}",
        )
    try:
        duration_hours = Decimal(raw.duration_hours)
    except InvalidOperation as error:
        raise _quality_error(
            raw,
            source_table=source,
            target_table=target,
            rule_code="INVALID_DURATION",
            message=f"Durée invalide : {raw.duration_hours!r}",
        ) from error
    if not duration_hours.is_finite() or duration_hours <= 0:
        raise _quality_error(
            raw,
            source_table=source,
            target_table=target,
            rule_code="INVALID_DURATION",
            message=f"Durée non positive ou non finie : {raw.duration_hours!r}",
        )
    return {
        "maintenance_id": _integer(
            raw.maintenance_id,
            raw_row=raw,
            source_table=source,
            target_table=target,
            column="maintenance_id",
        ),
        "machine_code": machine_code,
        "source_machine_code": source_machine_code,
        "machine_code_was_aligned": machine_code != source_machine_code,
        "maintenance_at": _utc_datetime(
            raw.maintenance_at,
            raw_row=raw,
            source_table=source,
            target_table=target,
            column="maintenance_at",
        ),
        "maintenance_type": maintenance_type,
        "action_type": raw.action_type.strip(),
        "component": raw.component.strip(),
        "description": raw.description.strip(),
        "related_incident_id": related_incident_id,
        "duration_hours": duration_hours,
        **_lineage(raw, run_id),
    }


def _telemetry_row(raw: TelemetryRaw, run_id: UUID) -> dict[str, object]:
    source = "bronze.telemetry_raw"
    target = "silver.telemetry"
    pieces_produced = _integer(
        raw.pieces_produced,
        raw_row=raw,
        source_table=source,
        target_table=target,
        column="pieces_produced",
    )
    if pieces_produced < 0:
        raise _quality_error(
            raw,
            source_table=source,
            target_table=target,
            rule_code="INVALID_PIECES_PRODUCED",
            message=f"Nombre de pièces négatif : {pieces_produced}",
        )
    return {
        "machine_code": raw.machine_id.strip().upper(),
        "measured_at": _utc_datetime(
            raw.timestamp,
            raw_row=raw,
            source_table=source,
            target_table=target,
            column="timestamp",
        ),
        "temperature_c": _optional_non_negative_float(raw.temperature_c, raw_row=raw, column="temperature_c"),
        "pressure_bar": _optional_non_negative_float(raw.pressure_bar, raw_row=raw, column="pressure_bar"),
        "voltage_mean_v": _optional_non_negative_float(raw.voltage_mean_v, raw_row=raw, column="voltage_mean_v"),
        "rotation_mean_rpm": _optional_non_negative_float(raw.rotation_mean_rpm, raw_row=raw, column="rotation_mean_rpm"),
        "pieces_produced": pieces_produced,
        **_lineage(raw, run_id),
    }


def _assert_unique_key(
    rows: Sequence[dict[str, object]],
    *,
    key: str,
    entity: str,
) -> None:
    seen: set[object] = set()
    for row in rows:
        value = row[key]
        if value in seen:
            raise ValueError(f"Clé métier dupliquée dans {entity} : {value!r}")
        seen.add(value)


def transform_bronze_rows(
    *,
    machine_rows: Sequence[MachineRaw],
    incident_rows: Sequence[IncidentRaw],
    maintenance_rows: Sequence[MaintenanceRaw],
    telemetry_rows: Sequence[TelemetryRaw],
    run_id: UUID,
) -> SilverDataset:
    """Transforme quatre grains Bronze en dataset Silver validé en mémoire."""

    machines = [_machine_row(raw, run_id) for raw in machine_rows]
    _assert_unique_key(machines, key="machine_code", entity="machine")
    machine_codes = {str(row["machine_code"]) for row in machines}

    incidents = [_incident_row(raw, run_id) for raw in incident_rows]
    _assert_unique_key(incidents, key="incident_id", entity="incident")
    for raw, row in zip(incident_rows, incidents, strict=True):
        if row["machine_code"] not in machine_codes:
            raise _quality_error(
                raw,
                source_table="bronze.incident_raw",
                target_table="silver.incident",
                rule_code="UNKNOWN_MACHINE",
                message=f"Machine d'incident inconnue : {row['machine_code']}",
            )
    incidents_by_id = {str(row["incident_id"]): row for row in incidents}

    maintenances = [
        _maintenance_row(raw, run_id, machine_codes, incidents_by_id)
        for raw in maintenance_rows
    ]
    _assert_unique_key(maintenances, key="maintenance_id", entity="maintenance")

    telemetry: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    telemetry_groups: dict[tuple[str, datetime], list[TelemetryRaw]] = {}

    for raw in telemetry_rows:
        machine_code = raw.machine_id.strip().upper()
        measured_at = _utc_datetime(
            raw.timestamp,
            raw_row=raw,
            source_table="bronze.telemetry_raw",
            target_table="silver.telemetry",
            column="timestamp",
        )
        if machine_code not in machine_codes:
            raise _quality_error(
                raw,
                source_table="bronze.telemetry_raw",
                target_table="silver.telemetry",
                rule_code="UNKNOWN_MACHINE",
                message=f"Machine de télémétrie inconnue : {machine_code}",
            )
        telemetry_groups.setdefault((machine_code, measured_at), []).append(raw)

    sensor_columns = (
        "temperature_c",
        "pressure_bar",
        "voltage_mean_v",
        "rotation_mean_rpm",
    )
    telemetry_duplicate_count = 0
    telemetry_missing_count = 0
    for group_rows in telemetry_groups.values():
        ordered_rows = sorted(
            group_rows,
            key=lambda row: (
                sum(not getattr(row, column).strip() for column in sensor_columns),
                row.source_row_number,
            ),
        )
        retained_raw = ordered_rows[0]
        transformed = _telemetry_row(retained_raw, run_id)
        telemetry.append(transformed)
        missing_columns = [
            column for column in sensor_columns if transformed[column] is None
        ]
        if missing_columns:
            telemetry_missing_count += 1
            issues.append(
                {
                    "run_id": run_id,
                    "source_batch_id": retained_raw.batch_id,
                    "source_table": "bronze.telemetry_raw",
                    "source_row_number": retained_raw.source_row_number,
                    "source_record_hash": retained_raw.record_hash,
                    "target_table": "silver.telemetry",
                    "rule_code": "TELEMETRY_MISSING_MEASUREMENT",
                    "severity": "warning",
                    "action": "retained_with_null",
                    "reason": (
                        "Mesure Silver conservée avec capteur absent : "
                        + ", ".join(missing_columns)
                    ),
                    "original_payload": _raw_payload(retained_raw),
                }
            )

        for raw in ordered_rows[1:]:
            telemetry_duplicate_count += 1
            issues.append(
                {
                    "run_id": run_id,
                    "source_batch_id": raw.batch_id,
                    "source_table": "bronze.telemetry_raw",
                    "source_row_number": raw.source_row_number,
                    "source_record_hash": raw.record_hash,
                    "target_table": "silver.telemetry",
                    "rule_code": "TELEMETRY_BUS_DUPLICATE",
                    "severity": "warning",
                    "action": "deduplicated",
                    "reason": (
                        "Doublon machine/timestamp écarté ; ligne Bronze conservée : "
                        f"{retained_raw.source_row_number}"
                    ),
                    "original_payload": {
                        **_raw_payload(raw),
                        "retained_source_row_number": retained_raw.source_row_number,
                    },
                }
            )

    aligned_maintenance_count = sum(
        bool(row["machine_code_was_aligned"]) for row in maintenances
    )
    read_counts = {
        "machine": len(machine_rows),
        "incident": len(incident_rows),
        "maintenance": len(maintenance_rows),
        "telemetry": len(telemetry_rows),
    }
    written_counts = {
        "machine": len(machines),
        "incident": len(incidents),
        "maintenance": len(maintenances),
        "telemetry": len(telemetry),
    }
    metrics: dict[str, object] = {
        "read": read_counts,
        "written": written_counts,
        "rows_read": sum(read_counts.values()),
        "rows_written": sum(written_counts.values()),
        "maintenance_machine_codes_aligned": aligned_maintenance_count,
        "telemetry_duplicates_removed": telemetry_duplicate_count,
        "telemetry_rows_with_missing_measurement": telemetry_missing_count,
        "issues": len(issues),
    }
    if metrics["rows_read"] != metrics["rows_written"] + telemetry_duplicate_count:
        raise ValueError("Bilan de volumes Silver incohérent")

    return SilverDataset(
        machines=machines,
        incidents=incidents,
        maintenances=maintenances,
        telemetry=telemetry,
        issues=issues,
        metrics=metrics,
    )


def _latest_completed_batch(session: Session, source_file: str) -> IngestionBatch:
    batch = session.scalar(
        select(IngestionBatch)
        .where(
            IngestionBatch.source_file == source_file,
            IngestionBatch.status == "completed",
        )
        .order_by(IngestionBatch.finished_at.desc(), IngestionBatch.started_at.desc())
        .limit(1)
    )
    if batch is None:
        raise ValueError(f"Aucun lot Bronze terminé pour {source_file}")
    return batch


def _insert_in_chunks(session: Session, model: type[Any], rows: Sequence[dict[str, object]]) -> None:
    for start in range(0, len(rows), INSERT_CHUNK_SIZE):
        session.execute(model.__table__.insert(), rows[start : start + INSERT_CHUNK_SIZE])


def _rejected_issue(error: SilverDataQualityError, run_id: UUID) -> dict[str, object]:
    raw = error.raw_row
    return {
        "run_id": run_id,
        "source_batch_id": raw.batch_id,
        "source_table": error.source_table,
        "source_row_number": raw.source_row_number,
        "source_record_hash": raw.record_hash,
        "target_table": error.target_table,
        "rule_code": error.rule_code,
        "severity": "rejected",
        "action": "pipeline_failed",
        "reason": str(error),
        "original_payload": _raw_payload(raw),
    }


def build_silver(session_factory: sessionmaker[Session]) -> SilverBuildResult:
    """Construit et publie Silver intégralement dans une transaction atomique."""

    with session_factory.begin() as session:
        batches = {
            source_file: _latest_completed_batch(session, source_file)
            for source_file in SOURCE_FILES
        }
        run = PipelineRun(
            pipeline_version=PIPELINE_VERSION,
            transformation_version=TRANSFORMATION_VERSION,
            status="running",
        )
        session.add(run)
        session.flush()
        run_id = run.run_id
        session.add_all([
            PipelineRunSource(run_id=run_id, batch_id=batch.batch_id)
            for batch in batches.values()
        ])
        batch_ids = {source_file: batch.batch_id for source_file, batch in batches.items()}

    try:
        with session_factory() as session:
            machine_rows = list(
                session.scalars(
                    select(MachineRaw)
                    .where(MachineRaw.batch_id == batch_ids["machine.sql"])
                    .order_by(MachineRaw.source_row_number)
                )
            )
            maintenance_rows = list(
                session.scalars(
                    select(MaintenanceRaw)
                    .where(MaintenanceRaw.batch_id == batch_ids["machine.sql"])
                    .order_by(MaintenanceRaw.source_row_number)
                )
            )
            incident_rows = list(
                session.scalars(
                    select(IncidentRaw)
                    .where(IncidentRaw.batch_id == batch_ids["releves_incidents.csv"])
                    .order_by(IncidentRaw.source_row_number)
                )
            )
            telemetry_rows = list(
                session.scalars(
                    select(TelemetryRaw)
                    .where(TelemetryRaw.batch_id == batch_ids["telemetry.csv"])
                    .order_by(TelemetryRaw.source_row_number)
                )
            )
            dataset = transform_bronze_rows(
                machine_rows=machine_rows,
                incident_rows=incident_rows,
                maintenance_rows=maintenance_rows,
                telemetry_rows=telemetry_rows,
                run_id=run_id,
            )

        with session_factory.begin() as session:
            for model in (Telemetry, Maintenance, Incident, Machine):
                session.execute(delete(model))
            _insert_in_chunks(session, Machine, dataset.machines)
            _insert_in_chunks(session, Incident, dataset.incidents)
            _insert_in_chunks(session, Maintenance, dataset.maintenances)
            _insert_in_chunks(session, Telemetry, dataset.telemetry)
            _insert_in_chunks(session, TransformationIssue, dataset.issues)
            session.execute(
                update(PipelineRun)
                .where(PipelineRun.run_id == run_id)
                .values(
                    status="completed",
                    metrics=dataset.metrics,
                    finished_at=func.now(),
                )
            )
        return SilverBuildResult(run_id=run_id, metrics=dataset.metrics)
    except Exception as error:
        with session_factory.begin() as session:
            if isinstance(error, SilverDataQualityError):
                session.execute(
                    TransformationIssue.__table__.insert(),
                    [_rejected_issue(error, run_id)],
                )
            session.execute(
                update(PipelineRun)
                .where(PipelineRun.run_id == run_id)
                .values(
                    status="failed",
                    error_message=str(error)[:4000],
                    finished_at=func.now(),
                )
            )
        raise
