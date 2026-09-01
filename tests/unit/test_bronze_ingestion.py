import tempfile
import unittest
from pathlib import Path

from indusense.ingestion.bronze import (
    read_csv_rows,
    read_sql_insert_rows,
    source_record_hash,
    source_sha256,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class BronzeIngestionTests(unittest.TestCase):
    def test_reader_preserves_empty_cells_and_physical_row_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_file = Path(temporary_directory) / "source.csv"
            source_file.write_text("id,comment\n1,\n2,ok\n", encoding="utf-8")

            rows = list(read_csv_rows(source_file))

        self.assertEqual(rows, [(2, {"id": "1", "comment": ""}), (3, {"id": "2", "comment": "ok"})])

    def test_hashes_are_stable_for_the_same_source_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_file = Path(temporary_directory) / "source.csv"
            source_file.write_text("id\n1\n", encoding="utf-8")

            first_hash = source_sha256(source_file)
            second_hash = source_sha256(source_file)

        self.assertEqual(first_hash, second_hash)
        self.assertEqual(len(first_hash), 64)
        self.assertEqual(source_record_hash({"id": "1"}), source_record_hash({"id": "1"}))

    def test_sql_reader_extracts_quoted_values_nulls_and_defaults(self) -> None:
        sql_content = """INSERT INTO maintenance (maintenance_id, description, related_incident_id)
VALUES
(1, 'Contrôle, puis test', NULL),
(2, 'L''élément est remplacé', 'INC-000002')
ON CONFLICT (maintenance_id) DO NOTHING;
"""
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_file = Path(temporary_directory) / "source.sql"
            source_file.write_text(sql_content, encoding="utf-8")

            rows = list(
                read_sql_insert_rows(
                    source_file,
                    table_name="maintenance",
                    defaults={"source_kind": "sql"},
                )
            )

        self.assertEqual(
            rows,
            [
                (
                    3,
                    {
                        "maintenance_id": "1",
                        "description": "Contrôle, puis test",
                        "related_incident_id": "",
                        "source_kind": "sql",
                    },
                ),
                (
                    4,
                    {
                        "maintenance_id": "2",
                        "description": "L'élément est remplacé",
                        "related_incident_id": "INC-000002",
                        "source_kind": "sql",
                    },
                ),
            ],
        )

    def test_machine_sql_contains_the_expected_two_bronze_grains(self) -> None:
        source_file = PROJECT_ROOT / "datas" / "machine.sql"

        machine_rows = list(
            read_sql_insert_rows(
                source_file,
                table_name="machine",
                defaults={"is_active": "true"},
            )
        )
        maintenance_rows = list(
            read_sql_insert_rows(source_file, table_name="maintenance")
        )

        self.assertEqual(len(machine_rows), 15)
        self.assertEqual(len(maintenance_rows), 1562)
        self.assertEqual(machine_rows[0][1]["machine_code"], "MACH-01")
        self.assertEqual(machine_rows[-1][1]["is_active"], "true")
        self.assertEqual(maintenance_rows[0][1]["related_incident_id"], "")
        self.assertEqual(
            maintenance_rows[-1][1]["related_incident_id"],
            "INC-001245",
        )
