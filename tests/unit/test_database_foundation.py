import unittest

from sqlalchemy import create_engine

from indusense.db import models as _models  # noqa: F401
from indusense.db.base import Base, NAMING_CONVENTION
from indusense.db.session import create_session_factory


class DatabaseFoundationTests(unittest.TestCase):
    def test_base_has_naming_convention_and_registered_models(self) -> None:
        self.assertEqual(Base.metadata.naming_convention, NAMING_CONVENTION)
        self.assertEqual(
            set(Base.metadata.tables),
            {
                "bronze.incident_raw",
                "bronze.machine_maintenance_raw",
                "bronze.telemetry_raw",
                "ops.ingestion_batch",
            },
        )

    def test_session_factory_uses_given_engine(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:")
        session_factory = create_session_factory(engine)

        with session_factory() as session:
            self.assertIs(session.get_bind(), engine)

        engine.dispose()
