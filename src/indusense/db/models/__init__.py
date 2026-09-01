"""Modèles ORM enregistrés dans les métadonnées SQLAlchemy."""

from indusense.db.models.bronze.incident_raw import IncidentRaw
from indusense.db.models.bronze.machine_raw import MachineRaw
from indusense.db.models.bronze.maintenance_raw import MaintenanceRaw
from indusense.db.models.bronze.telemetry_raw import TelemetryRaw
from indusense.db.models.ops.ingestion_batch import IngestionBatch
from indusense.db.models.ops.pipeline_run import PipelineRun
from indusense.db.models.ops.pipeline_run_source import PipelineRunSource
from indusense.db.models.ops.transformation_issue import TransformationIssue
from indusense.db.models.silver.incident import Incident
from indusense.db.models.silver.machine import Machine
from indusense.db.models.silver.maintenance import Maintenance
from indusense.db.models.silver.telemetry import Telemetry

__all__ = [
    "IncidentRaw",
    "Incident",
    "IngestionBatch",
    "MachineRaw",
    "Machine",
    "MaintenanceRaw",
    "Maintenance",
    "PipelineRun",
    "PipelineRunSource",
    "TelemetryRaw",
    "Telemetry",
    "TransformationIssue",
]
