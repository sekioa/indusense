import os
from dataclasses import dataclass

from sqlalchemy import URL


class DatabaseConfigurationError(ValueError):
    """Signale une configuration PostgreSQL absente ou incohérente."""


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    drivername: str
    username: str
    password: str
    host: str
    port: int
    database: str

    @classmethod
    def from_environment(cls) -> "DatabaseSettings":
        required_variables = ("DB_USER", "DB_PASSWORD", "DB_NAME")
        missing_variables = [
            variable
            for variable in required_variables
            if not os.environ.get(variable)
        ]
        if missing_variables:
            missing = ", ".join(missing_variables)
            raise DatabaseConfigurationError(
                f"Variables PostgreSQL manquantes : {missing}"
            )

        port_value = os.environ.get("DB_PORT", "5432")
        try:
            port = int(port_value)
        except ValueError as error:
            raise DatabaseConfigurationError(
                "DB_PORT doit contenir un nombre entier."
            ) from error

        if not 1 <= port <= 65535:
            raise DatabaseConfigurationError(
                "DB_PORT doit être compris entre 1 et 65535."
            )

        return cls(
            drivername="postgresql+psycopg",
            username=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ.get("DB_HOST", "localhost"),
            port=port,
            database=os.environ["DB_NAME"],
        )

    @property
    def url(self) -> URL:
        return URL.create(
            drivername=self.drivername,
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )
