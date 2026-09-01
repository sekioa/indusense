import unittest
import os
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from indusense.cli import _bronze_sources, build_parser, main


class CommandLineTests(unittest.TestCase):
    def test_db_check_command_is_available(self) -> None:
        parsed_arguments = build_parser().parse_args(["db-check"])

        self.assertEqual(parsed_arguments.command, "db-check")

    def test_ingest_bronze_command_defaults_to_all_sources(self) -> None:
        parsed_arguments = build_parser().parse_args(["ingest-bronze"])

        self.assertEqual(parsed_arguments.command, "ingest-bronze")
        self.assertEqual(parsed_arguments.source, "all")

    def test_build_silver_command_is_available(self) -> None:
        parsed_arguments = build_parser().parse_args(["build-silver"])

        self.assertEqual(parsed_arguments.command, "build-silver")

    def test_bronze_sources_resolve_inside_the_project(self) -> None:
        sources = _bronze_sources()

        self.assertTrue(all(source.path.is_file() for source in sources.values()))
        self.assertEqual(sources["machine"].path.name, "machine.sql")
        self.assertEqual(len(sources["machine"].targets), 2)
        self.assertEqual(sources["incident"].path.name, "releves_incidents.csv")
        self.assertEqual(sources["telemetry"].path.name, "telemetry.csv")

    def test_db_check_reports_missing_configuration_without_traceback(self) -> None:
        output = StringIO()

        with patch.dict(os.environ, {}, clear=True), redirect_stdout(output):
            exit_code = main(["db-check"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Configuration PostgreSQL invalide", output.getvalue())
