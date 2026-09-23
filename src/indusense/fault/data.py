"""Chargement du Gold dataset, split temporel purgé et sélection des features par horizon."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_DATA_PATH = Path("datas/gold_dataset_20260622-080603.csv")
DEFAULT_HORIZON = 24
SPLIT_ROLES = ("train", "validation", "test")
ID_COLUMNS = ("machine_id_std", "window_start", "window_end", "split_set")
LEAKAGE_PREFIXES = ("label_failure_next_", "future_incident_count_")


def target_column(horizon: int) -> str:
    """Nom de la colonne cible pour un horizon donné, en heures (ex. 24 -> ``label_failure_next_24h``)."""
    return f"label_failure_next_{horizon}h"


def load_gold(path: Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Charge le Gold dataset, trié par fin de fenêtre puis machine, et vérifie son grain.

    Une ligne est une *machine-heure* : le couple ``(machine_id_std, window_end)`` est unique et chaque
    fenêtre dure une heure. Ces invariants conditionnent le split temporel : les violer romprait la
    chronologie utilisée pour la purge anti-fuite.
    """
    gold = pd.read_csv(path, parse_dates=["window_start", "window_end"])
    gold = gold.sort_values(["window_end", "machine_id_std"], kind="stable").reset_index(drop=True)
    if gold.duplicated(["machine_id_std", "window_end"]).any():
        raise ValueError("Doublons (machine_id_std, window_end) : le grain machine-heure est rompu.")
    if not (gold.window_end - gold.window_start).eq(pd.Timedelta(hours=1)).all():
        raise ValueError("Toutes les fenêtres doivent durer exactement une heure.")
    if set(gold["split_set"].unique()) != set(SPLIT_ROLES):
        raise ValueError(f"Rôles de split inattendus : {sorted(gold['split_set'].unique())}")
    return gold


def dataset_fingerprint(path: Path = DEFAULT_DATA_PATH) -> str:
    """Empreinte SHA-256 du fichier source, à journaliser pour tracer quel CSV a produit quel modèle."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select_features(gold: pd.DataFrame, horizon: int) -> list[str]:
    """Liste les colonnes utilisables comme features pour un horizon donné.

    Exclut les colonnes d'identification/temps (``ID_COLUMNS``) et toute colonne de fuite
    (``label_failure_next_*``, ``future_incident_count_*``) : ces colonnes regardent le futur, y compris
    pour un horizon différent de celui prédit, et ne doivent jamais servir de feature.
    """
    target = target_column(horizon)
    if target not in gold.columns:
        raise ValueError(f"Colonne cible absente : {target}")
    excluded = set(ID_COLUMNS)
    excluded.update(c for c in gold.columns if c.startswith(LEAKAGE_PREFIXES))
    features = [c for c in gold.columns if c not in excluded]
    non_numeric = gold[features].select_dtypes(exclude=["number", "bool"]).columns.tolist()
    if non_numeric:
        raise ValueError(f"Features non numériques inattendues : {non_numeric}")
    return features


@dataclass(frozen=True)
class TemporalSplit:
    """Jeux X/y par rôle (train/validation/test), purgés de toute fuite temporelle.

    ``window_end`` est conservé à part (hors de ``X``, qui ne doit contenir que des features) : c'est
    l'horodatage qui sert à découper le train en folds chronologiques (``build_cv_folds``).
    """

    features: list[str]
    target: str
    X: dict[str, pd.DataFrame]
    y: dict[str, pd.Series]
    window_end: dict[str, pd.Series]
    purged_rows: dict[str, int]
    gap: pd.Timedelta


def temporal_split(gold: pd.DataFrame, horizon: int = DEFAULT_HORIZON) -> TemporalSplit:
    """Reconstruit le split temporel purgé, comme dans le notebook B5/B7 de référence.

    Le **gap** égale l'horizon prédit : une ligne du train ou de la validation dont la fenêtre se situe
    à moins de ``horizon`` heures du rôle suivant est retirée, car son label pourrait dépendre
    d'informations qui, pour ce rôle suivant, appartiennent encore au futur.
    """
    target = target_column(horizon)
    features = select_features(gold, horizon)
    parts = {role: gold.loc[gold.split_set.eq(role)].copy() for role in SPLIT_ROLES}
    gap = pd.Timedelta(hours=horizon)
    purged_rows: dict[str, int] = {}
    for left, right in (("train", "validation"), ("validation", "test")):
        before = len(parts[left])
        cutoff = parts[right].window_end.min() - gap
        parts[left] = parts[left].loc[parts[left].window_end < cutoff].copy()
        purged_rows[left] = before - len(parts[left])
        if not (parts[left].window_end.max() + gap < parts[right].window_end.min()):
            raise ValueError(f"Purge insuffisante entre {left} et {right}.")

    X = {role: frame[features].reset_index(drop=True) for role, frame in parts.items()}
    y = {role: frame[target].astype(int).reset_index(drop=True) for role, frame in parts.items()}
    window_end = {role: frame["window_end"].reset_index(drop=True) for role, frame in parts.items()}
    for role, series in y.items():
        if series.nunique() != 2:
            raise ValueError(f"Le rôle {role!r} ne contient pas les deux classes après purge.")
    return TemporalSplit(
        features=features, target=target, X=X, y=y, window_end=window_end,
        purged_rows=purged_rows, gap=gap,
    )


@dataclass(frozen=True)
class CrossValidationFolds:
    """Découpage du train en folds chronologiques internes, avec leurs métadonnées d'audit."""

    folds: list[tuple[np.ndarray, np.ndarray]]
    metadata: list[dict]


def build_cv_folds(split: TemporalSplit, *, n_folds: int = 3) -> CrossValidationFolds:
    """Découpe le train en ``n_folds`` blocs chronologiques contigus, séparés par le gap anti-fuite.

    Contrairement à un ``KFold`` aléatoire, chaque fold de validation suit son fold d'entraînement dans
    le temps : un ``KFold`` mélangerait passé et futur et gonflerait artificiellement le score.
    """
    timestamps = split.window_end["train"]
    y_train = split.y["train"]
    blocks = np.array_split(np.sort(timestamps.unique()), n_folds + 1)
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    metadata: list[dict] = []
    for i in range(n_folds):
        validation_dates = blocks[i + 1]
        validation_start = pd.Timestamp(validation_dates[0])
        train_idx = np.flatnonzero((timestamps < validation_start - split.gap).to_numpy())
        validation_idx = np.flatnonzero(timestamps.isin(validation_dates).to_numpy())
        if not len(train_idx) or not len(validation_idx):
            raise ValueError(f"Fold {i + 1} vide : train={len(train_idx)}, validation={len(validation_idx)}.")
        if not (timestamps.iloc[train_idx].max() + split.gap < timestamps.iloc[validation_idx].min()):
            raise ValueError(f"Fold {i + 1} : gap anti-fuite non respecté.")
        if y_train.iloc[train_idx].nunique() != 2 or y_train.iloc[validation_idx].nunique() != 2:
            raise ValueError(f"Fold {i + 1} : une des deux parts ne contient qu'une seule classe.")
        folds.append((train_idx, validation_idx))
        metadata.append({
            "fold": i + 1,
            "train_rows": len(train_idx),
            "validation_rows": len(validation_idx),
            "train_end": str(timestamps.iloc[train_idx].max()),
            "validation_start": str(timestamps.iloc[validation_idx].min()),
            "validation_end": str(timestamps.iloc[validation_idx].max()),
        })
    return CrossValidationFolds(folds=folds, metadata=metadata)
