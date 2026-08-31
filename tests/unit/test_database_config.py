import os
import unittest
from unittest.mock import patch

from indusense.db.config import (
    DatabaseConfigurationError,
    DatabaseSettings,
)


class DatabaseSettingsTests(unittest.TestCase):
    def test_builds_postgresql_psycopg_url_from_environment(self) -> None:
        environment = {
            "DB_USER": "indusense-user",
            "DB_PASSWORD": "secret-with-@-character",
            "DB_NAME": "indusense",
            "DB_HOST": "database.example",
            "DB_PORT": "55432",
        }

        with patch.dict(os.environ, environment, clear=True):
            settings = DatabaseSettings.from_environment()

        self.assertEqual(settings.drivername, "postgresql+psycopg")
        self.assertEqual(settings.host, "database.example")
        self.assertEqual(settings.port, 55432)
        self.assertEqual(settings.database, "indusense")
        self.assertNotIn(
            "secret-with-@-character",
            settings.url.render_as_string(),
        )

    def test_uses_localhost_and_postgresql_default_port(self) -> None:
        environment = {
            "DB_USER": "user",
            "DB_PASSWORD": "password",
            "DB_NAME": "database",
        }

        with patch.dict(os.environ, environment, clear=True):
            settings = DatabaseSettings.from_environment()

        self.assertEqual(settings.host, "localhost")
        self.assertEqual(settings.port, 5432)

    def test_rejects_missing_required_variables(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                DatabaseConfigurationError,
                "DB_USER, DB_PASSWORD, DB_NAME",
            ):
                DatabaseSettings.from_environment()

    def test_rejects_invalid_port(self) -> None:
        environment = {
            "DB_USER": "user",
            "DB_PASSWORD": "password",
            "DB_NAME": "database",
            "DB_PORT": "not-a-port",
        }

        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaisesRegex(
                DatabaseConfigurationError,
                "nombre entier",
            ):
                DatabaseSettings.from_environment()
