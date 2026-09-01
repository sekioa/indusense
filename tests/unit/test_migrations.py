import unittest
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class MigrationTests(unittest.TestCase):
    def test_silver_migration_is_the_single_head_after_bronze(self) -> None:
        config = Config(str(PROJECT_ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
        scripts = ScriptDirectory.from_config(config)
        silver_revision = scripts.get_revision("20260901_01")

        self.assertEqual(scripts.get_heads(), ["20260901_01"])
        self.assertIsNotNone(silver_revision)
        self.assertEqual(silver_revision.down_revision, "20260831_01")


if __name__ == "__main__":
    unittest.main()
