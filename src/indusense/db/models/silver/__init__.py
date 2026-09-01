"""Tables métier typées de la couche Silver."""

from indusense.db.models.silver.incident import Incident
from indusense.db.models.silver.machine import Machine
from indusense.db.models.silver.maintenance import Maintenance
from indusense.db.models.silver.telemetry import Telemetry

__all__ = ["Incident", "Machine", "Maintenance", "Telemetry"]
