"""Seuil et métriques de détection d'anomalie par erreur de reconstruction.

Ce module est délibérément indépendant de tout framework Deep Learning : il ne
manipule que des tableaux NumPy, afin d'être réutilisable depuis TensorFlow et
PyTorch (deux environnements Python distincts dans ce projet).
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def reconstruction_error(originals: np.ndarray, reconstructions: np.ndarray) -> np.ndarray:
    """Calcule l'erreur quadratique moyenne par image entre original et reconstruction."""
    if originals.shape != reconstructions.shape:
        raise ValueError(f"Formes différentes : {originals.shape} vs {reconstructions.shape}")
    squared_error = (originals.astype(np.float64) - reconstructions.astype(np.float64)) ** 2
    return squared_error.mean(axis=tuple(range(1, originals.ndim)))


def choose_threshold(validation_errors: np.ndarray, *, n_std: float = 3.0) -> float:
    """Calibre le seuil d'anomalie sur les erreurs d'un jeu de validation sain.

    Le seuil vaut la moyenne plus ``n_std`` écarts-types des erreurs de
    reconstruction observées sur des images saines inédites : une image de
    test dont l'erreur dépasse ce seuil est jugée anormale.
    """
    return float(validation_errors.mean() + n_std * validation_errors.std())


def choose_threshold_percentile(validation_errors: np.ndarray, *, percentile: float = 95.0) -> float:
    """Calibre le seuil au ``percentile`` de l'erreur de reconstruction sur la validation saine.

    Interprétation directe, contrairement à ``moyenne + n_std`` : un seuil au 95e percentile
    tolère jusqu'à 5 % de fausses alertes sur des images saines de validation, quelle que soit
    la forme (gaussienne ou non) de la distribution des erreurs.
    """
    return float(np.percentile(validation_errors, percentile))


@dataclass(frozen=True)
class ThresholdMetrics:
    """Métriques de classification binaire à un seuil donné."""

    threshold: float
    precision: float
    recall: float
    f1: float
    true_positive: int
    true_negative: int
    false_positive: int
    false_negative: int


def evaluate_at_threshold(labels: np.ndarray, scores: np.ndarray, threshold: float) -> ThresholdMetrics:
    """Évalue précision/rappel/F1 et la matrice de confusion à un seuil fixé.

    ``labels`` vaut 1 pour une image défectueuse, 0 pour une image saine.
    """
    predictions = (scores >= threshold).astype(int)
    true_negative, false_positive, false_negative, true_positive = confusion_matrix(
        labels, predictions, labels=[0, 1]
    ).ravel()
    return ThresholdMetrics(
        threshold=threshold,
        precision=float(precision_score(labels, predictions, zero_division=0)),
        recall=float(recall_score(labels, predictions, zero_division=0)),
        f1=float(f1_score(labels, predictions, zero_division=0)),
        true_positive=int(true_positive),
        true_negative=int(true_negative),
        false_positive=int(false_positive),
        false_negative=int(false_negative),
    )


def ranking_metrics(labels: np.ndarray, scores: np.ndarray) -> dict[str, float]:
    """Calcule ROC-AUC et PR-AUC (average precision) à partir des scores d'anomalie."""
    return {
        "roc_auc": float(roc_auc_score(labels, scores)),
        "pr_auc": float(average_precision_score(labels, scores)),
    }


@dataclass
class TrainingRun:
    """Résultat d'un entraînement d'auto-encodeur, sérialisable en JSON."""

    framework: str
    device: str
    category: str
    image_size: int
    batch_size: int
    epochs: int
    trainable_parameters: int
    first_epoch_seconds: float
    train_seconds: float
    seconds_per_epoch: float
    final_train_loss: float
    validation_error_mean: float
    validation_error_std: float
    threshold: float
    roc_auc: float
    pr_auc: float
    metrics_at_threshold: ThresholdMetrics
    mean_error_by_defect: dict[str, float]

    def to_json(self, path: Path) -> None:
        payload = asdict(self)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def from_json(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))
