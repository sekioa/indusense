from sqlalchemy import Engine, create_engine

from indusense.db.config import DatabaseSettings


def create_database_engine(
    settings: DatabaseSettings | None = None,
) -> Engine:
    """Créer l’Engine partagé par un processus applicatif."""

    database_settings = settings or DatabaseSettings.from_environment()
    return create_engine(database_settings.url, pool_pre_ping=True)
