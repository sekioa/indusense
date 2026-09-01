"""Tables brutes de la couche Bronze."""

from indusense.db.models.bronze.incident_raw import IncidentRaw
from indusense.db.models.bronze.machine_raw import MachineRaw
from indusense.db.models.bronze.maintenance_raw import MaintenanceRaw
from indusense.db.models.bronze.telemetry_raw import TelemetryRaw

__all__ = ["IncidentRaw", "MachineRaw", "MaintenanceRaw", "TelemetryRaw"]
