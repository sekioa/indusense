import argparse
from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from indusense.db.config import DatabaseConfigurationError
from indusense.db.engine import create_database_engine


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
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parsed_arguments = parser.parse_args(arguments)

    if parsed_arguments.command == "db-check":
        return _check_database()

    parser.error(f"Commande inconnue : {parsed_arguments.command}")
    return 2
