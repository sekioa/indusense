import csv
import unittest
from pathlib import Path

from sqlalchemy import Text, UniqueConstraint

from indusense.db.models import IncidentRaw, MachineRaw, MaintenanceRaw, TelemetryRaw


TECHNICAL_COLUMNS = {
    "id",
    "batch_id",
    "source_row_number",
    "record_hash",
    "ingested_at",
}
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class BronzeModelTests(unittest.TestCase):
    def test_model_columns_follow_the_source_file_headers(self) -> None:
        source_files = {
            IncidentRaw: PROJECT_ROOT / "datas" / "releves_incidents.csv",
            TelemetryRaw: PROJECT_ROOT / "datas" / "telemetry.csv",
        }

        for model, source_file in source_files.items():
            with self.subTest(model=model.__name__):
                with source_file.open(encoding="utf-8", newline="") as csv_file:
                    source_header = next(csv.reader(csv_file))

                model_source_columns = [
                    column_name
                    for column_name in model.__table__.columns.keys()
                    if column_name not in TECHNICAL_COLUMNS
                ]

                self.assertEqual(model_source_columns, source_header)

    def test_source_columns_match_the_csv_contracts_and_use_text(self) -> None:
        expected_source_columns = {
            IncidentRaw: {
                "incident_id",
                "date",
                "time",
                "operator_name",
                "machine_id",
                "severity",
                "operator_badge",
                "comment",
                "shift",
                "type_surchauffe",
                "type_baisse_pression",
                "type_vibration",
                "type_bruit_mecanique",
                "type_surconsommation",
                "type_blocage_mecanique",
                "type_alarme_capteur",
                "type_arret_urgence",
                "type_defaut_qualite",
            },
            MachineRaw: {
                "machine_code",
                "commissioning_date",
                "max_daily_capacity",
                "max_hourly_capacity_pieces",
                "model",
                "production_line",
                "location",
                "criticality",
                "is_active",
            },
            MaintenanceRaw: {
                "maintenance_id",
                "machine_code",
                "maintenance_at",
                "maintenance_type",
                "action_type",
                "component",
                "description",
                "related_incident_id",
                "duration_hours",
            },
            TelemetryRaw: {
                "machine_id",
                "timestamp",
                "temperature_c",
                "pressure_bar",
                "voltage_mean_v",
                "rotation_mean_rpm",
                "pieces_produced",
            },
        }

        for model, expected_columns in expected_source_columns.items():
            with self.subTest(model=model.__name__):
                table = model.__table__
                source_columns = set(table.columns.keys()) - TECHNICAL_COLUMNS

                self.assertEqual(source_columns, expected_columns)
                for column_name in source_columns:
                    column = table.columns[column_name]
                    self.assertIsInstance(column.type, Text)
                    self.assertFalse(column.nullable)

    def test_each_bronze_table_traces_rows_without_deduplicating_hashes(self) -> None:
        for model in (IncidentRaw, MachineRaw, MaintenanceRaw, TelemetryRaw):
            with self.subTest(model=model.__name__):
                table = model.__table__
                foreign_key = next(iter(table.columns.batch_id.foreign_keys))
                unique_column_sets = {
                    tuple(constraint.columns.keys())
                    for constraint in table.constraints
                    if isinstance(constraint, UniqueConstraint)
                }

                self.assertEqual(foreign_key.target_fullname, "ops.ingestion_batch.batch_id")
                self.assertIn(("batch_id", "source_row_number"), unique_column_sets)
                self.assertNotIn(("record_hash",), unique_column_sets)


if __name__ == "__main__":
    unittest.main()
