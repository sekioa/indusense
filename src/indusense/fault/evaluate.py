"""Métriques PR-AUC/ROC-AUC, validation croisée temporelle, seuil F2 et tableau d'arbitrage."""

from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    fbeta_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

from indusense.fault.data import CrossValidationFolds
from indusense.fault.model import build_pipeline


@dataclass(frozen=True)
class CrossValidationResult:
    """Résultat d'une validation croisée temporelle : AP par fold, moyenne et écart train-CV."""

    fold_scores: list[float]
    fold_train_scores: list[float]
    cv_ap: float
    cv_std: float
    train_ap: float
    gap_ap: float


def iter_fold_ap(
    params: dict, X_train: pd.DataFrame, y_train: pd.Series, folds: CrossValidationFolds, *, seed: int = 42,
) -> Iterator[tuple[int, float, float]]:
    """Entraîne un modèle par fold et cède ``(numéro de fold, AP validation, AP train)`` au fur et à mesure.

    Paresseux par construction : un appelant peut s'arrêter avant le dernier fold (ex. pruning Optuna)
    sans jamais entraîner les folds restants.
    """
    for fold_number, (train_idx, validation_idx) in enumerate(folds.folds, 1):
        fitted = build_pipeline(params, seed=seed).fit(X_train.iloc[train_idx], y_train.iloc[train_idx])
        validation_scores = fitted.predict_proba(X_train.iloc[validation_idx])[:, 1]
        train_scores = fitted.predict_proba(X_train.iloc[train_idx])[:, 1]
        val_ap = float(average_precision_score(y_train.iloc[validation_idx], validation_scores))
        train_ap = float(average_precision_score(y_train.iloc[train_idx], train_scores))
        yield fold_number, val_ap, train_ap


def cross_validate_ap(
    params: dict, X_train: pd.DataFrame, y_train: pd.Series, folds: CrossValidationFolds, *, seed: int = 42,
) -> CrossValidationResult:
    """Entraîne un modèle par fold et moyenne l'Average Precision de validation.

    L'**écart train-CV** (AP train moyenne moins AP validation moyenne) signale un risque de
    sur-apprentissage ; un écart faible ne prouve pas à lui seul la généralisation à toute période future.
    """
    fold_scores, fold_train_scores = [], []
    for _, val_ap, train_ap in iter_fold_ap(params, X_train, y_train, folds, seed=seed):
        fold_scores.append(val_ap)
        fold_train_scores.append(train_ap)
    cv_ap = float(np.mean(fold_scores))
    train_ap = float(np.mean(fold_train_scores))
    return CrossValidationResult(
        fold_scores=fold_scores, fold_train_scores=fold_train_scores,
        cv_ap=cv_ap, cv_std=float(np.std(fold_scores)), train_ap=train_ap, gap_ap=train_ap - cv_ap,
    )


def choose_threshold(y_true: pd.Series, scores: np.ndarray) -> float:
    """Choisit le seuil qui maximise le F2 (rappel pondéré plus fort que précision) sur les scores donnés.

    À utiliser uniquement sur la validation dédiée : jamais sur le test, pour ne pas ajuster une décision
    avec les données qui serviront ensuite à la juger.
    """
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    f2 = 5 * precision[:-1] * recall[:-1] / (4 * precision[:-1] + recall[:-1] + np.finfo(float).eps)
    return float(thresholds[np.argmax(f2)])


@dataclass(frozen=True)
class ThresholdMetrics:
    """Métriques de rang (AP, ROC-AUC) et de décision (précision/rappel/F2 + matrice de confusion)."""

    AP: float
    ROC_AUC: float
    precision: float
    recall: float
    F2: float
    TP: int
    FP: int
    FN: int
    TN: int
    threshold: float

    def as_dict(self) -> dict:
        return {
            "AP": self.AP, "ROC_AUC": self.ROC_AUC, "precision": self.precision, "recall": self.recall,
            "F2": self.F2, "TP": self.TP, "FP": self.FP, "FN": self.FN, "TN": self.TN,
            "threshold": self.threshold,
        }


def evaluate_at_threshold(y_true: pd.Series, scores: np.ndarray, threshold: float) -> ThresholdMetrics:
    """Évalue un jeu de scores à un seuil fixé : rang (AP/ROC-AUC) et décision (précision/rappel/F2)."""
    prediction = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, prediction, labels=[0, 1]).ravel()
    return ThresholdMetrics(
        AP=float(average_precision_score(y_true, scores)),
        ROC_AUC=float(roc_auc_score(y_true, scores)),
        precision=float(precision_score(y_true, prediction, zero_division=0)),
        recall=float(recall_score(y_true, prediction, zero_division=0)),
        F2=float(fbeta_score(y_true, prediction, beta=2, zero_division=0)),
        TP=int(tp), FP=int(fp), FN=int(fn), TN=int(tn), threshold=float(threshold),
    )


def arbitration_table(rows: list[dict]) -> pd.DataFrame:
    """Assemble le tableau d'arbitrage final (Partie E) : un candidat par ligne.

    Chaque ``row`` attend au moins les clés ``modele``, ``pr_auc``, ``gco2eq``, ``interpretabilite`` et
    ``decision`` (texte libre justifiant le choix retenu ou écarté).
    """
    columns = ["modele", "pr_auc", "gco2eq", "interpretabilite", "decision"]
    missing = [row for row in rows if not set(columns) <= set(row)]
    if missing:
        raise ValueError(f"Colonnes manquantes dans une ligne d'arbitrage : {missing[0]}")
    return pd.DataFrame(rows, columns=columns)
