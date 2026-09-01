import argparse
from collections.abc import Sequence
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from indusense.db.config import DatabaseConfigurationError
from indusense.db.engine import create_database_engine
from indusense.db.session import create_session_factory
from indusense.ingestion.bronze import (
    BronzeSource,
    csv_target,
    ingest_source,
    sql_insert_target,
)
from indusense.ingestion.silver import build_silver


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _bronze_sources() -> dict[str, BronzeSource]:
    from indusense.db.models import IncidentRaw, MachineRaw, MaintenanceRaw, TelemetryRaw

    data_directory = PROJECT_ROOT / "datas"
    return {
        "machine": BronzeSource(
            "machine",
            data_directory / "machine.sql",
            (
                sql_insert_target(
                    MachineRaw,
                    "machine",
                    defaults={"is_active": "true"},
                ),
                sql_insert_target(MaintenanceRaw, "maintenance"),
            ),
        ),
        "incident": BronzeSource(
            "incident",
            data_directory / "releves_incidents.csv",
            (csv_target(IncidentRaw),),
        ),
        "telemetry": BronzeSource(
            "telemetry",
            data_directory / "telemetry.csv",
            (csv_target(TelemetryRaw),),
        ),
    }


def _check_database() -> int:
    try:
        engine = create_database_engine()
    except DatabaseConfigurationError as error:
        print(f"Configuration PostgreSQL invalide : {error}")
        return 1

    try:
        with engine.connect() as connection:
            database_name, database_user = connection.execute(
                text("SELECT current_database(), current_user")
            ).one()
    except SQLAlchemyError as error:
        print(f"Echec de la connexion PostgreSQL : {error}")
        return 1
    finally:
        engine.dispose()

    print(
        "Connexion PostgreSQL reussie : "
        f"base={database_name}, utilisateur={database_user}"
    )
    return 0


def _ingest_bronze(source_name: str) -> int:
    try:
        engine = create_database_engine()
    except DatabaseConfigurationError as error:
        print(f"Configuration PostgreSQL invalide : {error}")
        return 1

    sources = _bronze_sources()
    selected_sources = sources.values() if source_name == "all" else [sources[source_name]]
    session_factory = create_session_factory(engine)

    try:
        for source in selected_sources:
            status, row_count = ingest_source(session_factory, source)
            if status == "completed":
                print(f"Ingestion Bronze terminée : source={source.name}, lignes={row_count}")
            else:
                print(f"Ingestion Bronze ignorée : source={source.name}, empreinte déjà terminée")
    except (OSError, SQLAlchemyError, ValueError) as error:
        print(f"Echec de l'ingestion Bronze : {error}")
        return 1
    finally:
        engine.dispose()

    return 0


def _build_silver() -> int:
    try:
        engine = create_database_engine()
    except DatabaseConfigurationError as error:
        print(f"Configuration PostgreSQL invalide : {error}")
        return 1

    session_factory = create_session_factory(engine)
    try:
        result = build_silver(session_factory)
        print(
            "Construction Silver terminée : "
            f"run={result.run_id}, "
            f"lignes_lues={result.metrics['rows_read']}, "
            f"lignes_ecrites={result.metrics['rows_written']}, "
            f"doublons_telemetrie={result.metrics['telemetry_duplicates_removed']}, "
            f"maintenances_realignees={result.metrics['maintenance_machine_codes_aligned']}"
        )
    except (SQLAlchemyError, ValueError) as error:
        print(f"Echec de la construction Silver : {error}")
        return 1
    finally:
        engine.dispose()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="indusense",
        description="Commandes du projet Indusense.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "db-check",
        help="Vérifier la connexion à PostgreSQL sans modifier la base.",
    )
    ingest_parser = subparsers.add_parser(
        "ingest-bronze",
        help="Charger les fichiers Bronze dans PostgreSQL.",
    )
    ingest_parser.add_argument(
        "--source",
        choices=("all", "machine", "incident", "telemetry"),
        default="all",
        help="Source à ingérer ; toutes les sources par défaut.",
    )
    subparsers.add_parser(
        "build-silver",
        help="Transformer les derniers lots Bronze en tables Silver.",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parsed_arguments = parser.parse_args(arguments)

    if parsed_arguments.command == "db-check":
        return _check_database()
    if parsed_arguments.command == "ingest-bronze":
        return _ingest_bronze(parsed_arguments.source)
    if parsed_arguments.command == "build-silver":
        return _build_silver()

    parser.error(f"Commande inconnue : {parsed_arguments.command}")
    return 2
