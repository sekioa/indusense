"""Entraînement (CV + refit) avec journalisation MLflow optionnelle."""

from dataclasses import dataclass
from time import perf_counter
from typing import Any

import pandas as pd

from indusense.fault.data import CrossValidationFolds
from indusense.fault.evaluate import CrossValidationResult, cross_validate_ap
from indusense.fault.model import build_pipeline


@dataclass
class TrainResult:
    """Modèle réentraîné sur tout le train, ses métriques CV et (si activé) sa référence MLflow."""

    params: dict
    cv_result: CrossValidationResult
    model: Any
    cv_seconds: float
    refit_seconds: float
    run_id: str | None = None
    model_uri: str | None = None


def fit_and_log(
    params: dict,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    folds: CrossValidationFolds,
    *,
    role: str,
    seed: int = 42,
    logged_params: dict | None = None,
    mlflow_run: Any = None,
) -> TrainResult:
    """Valide croisée un jeu de paramètres, réentraîne sur tout le train, journalise si un run est fourni.

    ``mlflow_run`` est un context manager déjà ouvert par l'appelant (ex. ``mlflow.start_run(...)``) ; passer
    ``None`` désactive toute journalisation MLflow, pour un usage hors tracking (tests, exploration rapide).
    Ce découplage garde la logique d'entraînement indépendante d'un backend de tracking particulier.
    """
    start = perf_counter()
    cv_result = cross_validate_ap(params, X_train, y_train, folds, seed=seed)
    cv_seconds = perf_counter() - start

    start = perf_counter()
    model = build_pipeline(params, seed=seed).fit(X_train, y_train)
    refit_seconds = perf_counter() - start

    run_id, model_uri = None, None
    if mlflow_run is not None:
        import mlflow
        import mlflow.sklearn

        with mlflow_run as run:
            mlflow.set_tag("role", role)
            mlflow.log_params(logged_params if logged_params is not None else params)
            mlflow.log_params({"seed": seed, "folds": len(folds.folds)})
            for fold_number, (fold_val, fold_train) in enumerate(
                zip(cv_result.fold_scores, cv_result.fold_train_scores), 1
            ):
                mlflow.log_metrics({f"fold_{fold_number}_ap": fold_val, f"fold_{fold_number}_train_ap": fold_train})
            mlflow.log_metrics({
                "cv_ap": cv_result.cv_ap, "cv_std": cv_result.cv_std, "train_ap": cv_result.train_ap,
                "gap_ap": cv_result.gap_ap, "cv_seconds": cv_seconds, "refit_seconds": refit_seconds,
            })
            signature = mlflow.models.infer_signature(X_train, model.predict(X_train.iloc[:5]))
            model_info = mlflow.sklearn.log_model(
                model, name="modele", signature=signature, serialization_format="cloudpickle",
            )
            run_id, model_uri = run.info.run_id, model_info.model_uri

    return TrainResult(
        params=params, cv_result=cv_result, model=model, cv_seconds=cv_seconds,
        refit_seconds=refit_seconds, run_id=run_id, model_uri=model_uri,
    )


def log_cv_result(
    cv_result: CrossValidationResult,
    logged_params: dict,
    *,
    role: str,
    mlflow_run: Any,
    tags: dict | None = None,
) -> str:
    """Journalise un résultat de validation croisée déjà calculé, sans réentraîner ni sauver de modèle.

    Utilisé pour chaque essai Optuna : recalculer et resauvegarder un modèle par essai serait coûteux et
    inutile (seul l'essai gagnant est réentraîné et journalisé avec ``fit_and_log``).
    """
    import mlflow

    with mlflow_run as run:
        mlflow.set_tag("role", role)
        if tags:
            mlflow.set_tags(tags)
        mlflow.log_params(logged_params)
        for fold_number, (fold_val, fold_train) in enumerate(
            zip(cv_result.fold_scores, cv_result.fold_train_scores), 1
        ):
            mlflow.log_metrics({f"fold_{fold_number}_ap": fold_val, f"fold_{fold_number}_train_ap": fold_train})
        mlflow.log_metrics({
            "cv_ap": cv_result.cv_ap, "cv_std": cv_result.cv_std,
            "train_ap": cv_result.train_ap, "gap_ap": cv_result.gap_ap,
        })
        return run.info.run_id
