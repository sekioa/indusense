import unittest

from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import configure_mappers

from indusense.db.models import Incident, Machine, Maintenance, Telemetry


LINEAGE_COLUMNS = {
    "source_batch_id",
    "source_row_number",
    "source_record_hash",
    "pipeline_run_id",
    "transformation_version",
    "silver_processed_at",
}


class SilverModelTests(unittest.TestCase):
    def test_mappers_and_business_relationships_are_configurable(self) -> None:
        configure_mappers()

        self.assertEqual(Machine.incidents.property.back_populates, "machine")
        self.assertEqual(Machine.maintenances.property.back_populates, "machine")
        self.assertEqual(Machine.telemetry.property.back_populates, "machine")
        self.assertTrue(Incident.maintenances.property.viewonly)
        self.assertTrue(Maintenance.incident.property.viewonly)

    def test_each_silver_table_contains_the_lineage_contract(self) -> None:
        for model in (Machine, Incident, Maintenance, Telemetry):
            with self.subTest(model=model.__name__):
                self.assertTrue(LINEAGE_COLUMNS.issubset(model.__table__.columns.keys()))
                unique_sets = {
                    tuple(constraint.columns.keys())
                    for constraint in model.__table__.constraints
                    if isinstance(constraint, UniqueConstraint)
                }
                self.assertIn(("source_batch_id", "source_row_number"), unique_sets)

    def test_telemetry_is_unique_per_machine_and_timestamp(self) -> None:
        unique_sets = {
            tuple(constraint.columns.keys())
            for constraint in Telemetry.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }

        self.assertIn(("machine_code", "measured_at"), unique_sets)

    def test_maintenance_uses_a_composite_incident_machine_foreign_key(self) -> None:
        foreign_keys = [
            constraint
            for constraint in Maintenance.__table__.constraints
            if isinstance(constraint, ForeignKeyConstraint)
        ]
        composite_targets = {
            tuple(element.target_fullname for element in constraint.elements)
            for constraint in foreign_keys
            if len(constraint.elements) == 2
        }

        self.assertIn(
            ("silver.incident.incident_id", "silver.incident.machine_code"),
            composite_targets,
        )

    def test_incident_model_keeps_operational_comment_but_excludes_personal_columns(self) -> None:
        incident_columns = set(Incident.__table__.columns.keys())

        self.assertTrue(
            {"operator_name", "operator_badge", "shift"}.isdisjoint(incident_columns)
        )
        self.assertIn("comment", incident_columns)


if __name__ == "__main__":
    unittest.main()
