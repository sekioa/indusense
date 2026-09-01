import unittest
from datetime import UTC
from uuid import uuid4

from indusense.db.models import IncidentRaw, MachineRaw, MaintenanceRaw, TelemetryRaw
from indusense.ingestion.silver import SilverDataQualityError, transform_bronze_rows


def lineage(source_row_number: int) -> dict[str, object]:
    return {
        "batch_id": uuid4(),
        "source_row_number": source_row_number,
        "record_hash": f"{source_row_number:064x}",
    }


def machine(machine_code: str, source_row_number: int) -> MachineRaw:
    return MachineRaw(
        **lineage(source_row_number),
        machine_code=machine_code,
        commissioning_date="2021-05-12",
        max_daily_capacity="770",
        max_hourly_capacity_pieces="48",
        model="InduPress-X2",
        production_line="Ligne-A",
        location="Atelier-2",
        criticality="MEDIUM",
        is_active="true",
    )


def incident() -> IncidentRaw:
    return IncidentRaw(
        **lineage(2),
        incident_id="INC-000001",
        date="2025-06-01",
        time="05:42",
        operator_name="Supprimé en Silver",
        machine_id="MACH-01",
        severity="4",
        operator_badge="OP1002",
        comment="Arrêt ligne signalé par l'opérateur",
        shift="nuit",
        type_surchauffe="1",
        type_baisse_pression="0",
        type_vibration="0",
        type_bruit_mecanique="0",
        type_surconsommation="0",
        type_blocage_mecanique="0",
        type_alarme_capteur="0",
        type_arret_urgence="0",
        type_defaut_qualite="0",
    )


def maintenance() -> MaintenanceRaw:
    return MaintenanceRaw(
        **lineage(60),
        maintenance_id="1",
        machine_code="MACH-02",
        maintenance_at="2025-06-02 10:00:00+00",
        maintenance_type="reactive",
        action_type="intervention_corrective",
        component="capteur température",
        description="Remplacement",
        related_incident_id="INC-000001",
        duration_hours="2.24",
    )


def telemetry(source_row_number: int, temperature: str) -> TelemetryRaw:
    return TelemetryRaw(
        **lineage(source_row_number),
        machine_id="MACH-01",
        timestamp="2025-06-01 00:00:00",
        temperature_c=temperature,
        pressure_bar="198.203",
        voltage_mean_v="227.568",
        rotation_mean_rpm="1541.787",
        pieces_produced="4",
    )


class SilverPipelineTests(unittest.TestCase):
    def test_transform_aligns_maintenance_and_deduplicates_telemetry(self) -> None:
        dataset = transform_bronze_rows(
            machine_rows=[machine("MACH-01", 18), machine("MACH-02", 19)],
            incident_rows=[incident()],
            maintenance_rows=[maintenance()],
            telemetry_rows=[telemetry(11, "46.332"), telemetry(10, "46.348")],
            run_id=uuid4(),
        )

        self.assertEqual(len(dataset.telemetry), 1)
        self.assertEqual(dataset.telemetry[0]["source_row_number"], 10)
        self.assertEqual(dataset.telemetry[0]["temperature_c"], 46.348)
        self.assertEqual(len(dataset.issues), 1)
        self.assertEqual(dataset.issues[0]["source_row_number"], 11)
        self.assertEqual(dataset.issues[0]["rule_code"], "TELEMETRY_BUS_DUPLICATE")
        self.assertEqual(dataset.maintenances[0]["source_machine_code"], "MACH-02")
        self.assertEqual(dataset.maintenances[0]["machine_code"], "MACH-01")
        self.assertTrue(dataset.maintenances[0]["machine_code_was_aligned"])
        self.assertIs(dataset.incidents[0]["occurred_at"].tzinfo, UTC)
        self.assertNotIn("operator_name", dataset.incidents[0])
        self.assertEqual(dataset.incidents[0]["comment"], "Arrêt ligne signalé par l'opérateur")
        self.assertEqual(dataset.metrics["maintenance_machine_codes_aligned"], 1)
        self.assertEqual(dataset.metrics["telemetry_duplicates_removed"], 1)

    def test_deduplication_prefers_the_most_complete_telemetry(self) -> None:
        incomplete = telemetry(10, "")
        complete = telemetry(11, "46.332")

        dataset = transform_bronze_rows(
            machine_rows=[machine("MACH-01", 18)],
            incident_rows=[],
            maintenance_rows=[],
            telemetry_rows=[incomplete, complete],
            run_id=uuid4(),
        )

        self.assertEqual(dataset.telemetry[0]["source_row_number"], 11)
        self.assertEqual(dataset.telemetry[0]["temperature_c"], 46.332)
        self.assertEqual(dataset.metrics["telemetry_duplicates_removed"], 1)

    def test_missing_sensor_measurement_is_preserved_as_null_and_warned(self) -> None:
        missing_rotation = telemetry(10, "46.348")
        missing_rotation.rotation_mean_rpm = ""

        dataset = transform_bronze_rows(
            machine_rows=[machine("MACH-01", 18)],
            incident_rows=[],
            maintenance_rows=[],
            telemetry_rows=[missing_rotation],
            run_id=uuid4(),
        )

        self.assertIsNone(dataset.telemetry[0]["rotation_mean_rpm"])
        self.assertEqual(dataset.issues[0]["rule_code"], "TELEMETRY_MISSING_MEASUREMENT")
        self.assertEqual(dataset.metrics["telemetry_rows_with_missing_measurement"], 1)

    def test_invalid_incident_boolean_is_blocking(self) -> None:
        invalid_incident = incident()
        invalid_incident.type_surchauffe = "unknown"

        with self.assertRaisesRegex(SilverDataQualityError, "Booléen invalide"):
            transform_bronze_rows(
                machine_rows=[machine("MACH-01", 18)],
                incident_rows=[invalid_incident],
                maintenance_rows=[],
                telemetry_rows=[],
                run_id=uuid4(),
            )

    def test_unknown_incident_machine_reports_the_matching_bronze_row(self) -> None:
        unknown_machine_incident = incident()
        unknown_machine_incident.machine_id = "MACH-99"

        with self.assertRaises(SilverDataQualityError) as context:
            transform_bronze_rows(
                machine_rows=[machine("MACH-01", 18)],
                incident_rows=[unknown_machine_incident],
                maintenance_rows=[],
                telemetry_rows=[],
                run_id=uuid4(),
            )

        self.assertIs(context.exception.raw_row, unknown_machine_incident)
        self.assertEqual(context.exception.rule_code, "UNKNOWN_MACHINE")


if __name__ == "__main__":
    unittest.main()
