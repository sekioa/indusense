"""Instrumentation CodeCarbon : kWh et gCO2eq par étape, agrégés dans un tableau de synthèse."""

from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TypeVar

import pandas as pd


DEFAULT_OUTPUT_DIR = Path("outputs/fault")
DEFAULT_COUNTRY_ISO_CODE = "FRA"
SUMMARY_COLUMNS = (
    "run_name", "step", "duration_seconds", "energy_kwh", "emissions_kg", "metric_name", "metric_value",
)

T = TypeVar("T")


@dataclass(frozen=True)
class TrackedRun:
    """Coût mesuré d'une étape : durée, énergie (kWh) et émissions (kg CO2eq)."""

    step: str
    duration_seconds: float
    energy_kwh: float
    emissions_kg: float


def track_step(
    fn: Callable[[], T],
    *,
    step: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    project_name: str = "indusense-fault",
    country_iso_code: str = DEFAULT_COUNTRY_ISO_CODE,
) -> tuple[T, TrackedRun]:
    """Exécute ``fn`` sous un ``OfflineEmissionsTracker`` et renvoie son résultat plus le coût mesuré.

    Le mode *offline* (``country_iso_code`` fixé, ex. ``"FRA"``) évite tout appel réseau de géolocalisation
    et donne une estimation reproductible du mix électrique, adaptée à une salle de formation.
    """
    from codecarbon import OfflineEmissionsTracker

    output_dir.mkdir(parents=True, exist_ok=True)
    tracker = OfflineEmissionsTracker(
        project_name=project_name,
        country_iso_code=country_iso_code,
        output_dir=str(output_dir),
        output_file="emissions.csv",
        save_to_file=True,
        log_level="error",
        allow_multiple_runs=True,
    )
    tracker.start()
    try:
        result = fn()
    finally:
        tracker.stop()

    data = tracker.final_emissions_data
    run = TrackedRun(step=step, duration_seconds=float(data.duration), energy_kwh=float(data.energy_consumed),
                      emissions_kg=float(data.emissions))
    return result, run


def append_summary_row(
    csv_path: Path, run: TrackedRun, *, run_name: str,
    metric_name: str | None = None, metric_value: float | None = None,
) -> None:
    """Ajoute une ligne ``run → étape → durée, kWh, gCO2eq, perf obtenue`` au tableau de synthèse cumulatif.

    ``run_name`` identifie l'exécution qui a produit la ligne : ce tableau est destiné à être **complété**
    au fil des exécutions (script ou notebook), jamais réécrit ; sans cet identifiant, deux exécutions
    distinctes deviendraient indiscernables une fois leurs lignes mélangées.
    """
    row = {"run_name": run_name, **asdict(run), "metric_name": metric_name, "metric_value": metric_value}
    frame = pd.DataFrame([row], columns=SUMMARY_COLUMNS)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(csv_path, mode="a", header=not csv_path.exists(), index=False)


def cost_per_performance_point(baseline_metric: float, candidate_metric: float, candidate_emissions_kg: float) -> float:
    """Coût en kg CO2eq par point de métrique gagné par rapport à la référence.

    Une valeur élevée (voire infinie si le gain est nul ou négatif) signale un coût disproportionné par
    rapport au bénéfice ; c'est la question centrale de l'arbitrage frugal vs lourd (étape 6).
    """
    gain = candidate_metric - baseline_metric
    if gain <= 0:
        return float("inf")
    return candidate_emissions_kg / gain
