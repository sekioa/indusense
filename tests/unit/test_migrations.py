import unittest
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class MigrationTests(unittest.TestCase):
    def test_comment_migration_is_the_single_head_after_silver(self) -> None:
        config = Config(str(PROJECT_ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
        scripts = ScriptDirectory.from_config(config)
        comment_revision = scripts.get_revision("20260901_02")

        self.assertEqual(scripts.get_heads(), ["20260901_02"])
        self.assertIsNotNone(comment_revision)
        self.assertEqual(comment_revision.down_revision, "20260901_01")


if __name__ == "__main__":
    unittest.main()
