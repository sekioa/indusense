"""Étude Optuna bornée (TPE + pruning + budget) sur l'espace de recherche RandomForest."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import optuna

from indusense.fault.data import CrossValidationFolds
from indusense.fault.evaluate import iter_fold_ap
from indusense.fault.model import decode_params


MAX_FEATURE_CHOICES = ("sqrt", "15%", "25%", "35%", "50%")


def suggest_params(trial: optuna.Trial) -> tuple[dict, dict]:
    """Échantillonne un jeu d'hyperparamètres RandomForest dans un espace **borné**.

    Un espace immense coûterait cher à explorer et trouverait souvent des optima fragiles, peu
    reproductibles d'une étude à l'autre ; les bornes ci-dessous restent dans des plages plausibles pour
    ce volume de données.
    """
    sampled = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 500, step=50),
        "max_depth": trial.suggest_int("max_depth", 4, 20),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 2, 30, log=True),
        "min_samples_split": trial.suggest_int("min_samples_split", 2, 20, log=True),
        "max_features_choice": trial.suggest_categorical("max_features_choice", MAX_FEATURE_CHOICES),
    }
    return sampled, decode_params(sampled)


def make_objective(
    X_train, y_train, folds: CrossValidationFolds, *, seed: int = 42,
    on_trial_complete: Callable[[optuna.Trial, dict, dict, list[float], list[float]], None] | None = None,
) -> Callable[[optuna.Trial], float]:
    """Construit la fonction objectif : moyenne l'AP de validation en CV temporelle, avec pruning par fold.

    Après chaque fold, l'AP moyenne partielle est rapportée au trial (``trial.report``) et comparée aux
    autres trials par le pruner : un essai nettement moins bon que la médiane des essais précédents, dès
    les premiers folds, est arrêté avant d'avoir entraîné les folds restants. C'est le pruning qui
    manquait à l'étude Optuna initiale (notebook 07, ``NopPruner``).

    ``on_trial_complete`` est un callback optionnel (ex. journalisation MLflow) appelé uniquement pour un
    trial mené à son terme, avec les scores complets par fold.
    """
    def objective(trial: optuna.Trial) -> float:
        sampled, params = suggest_params(trial)
        val_scores, train_scores = [], []
        for fold_number, val_ap, train_ap in iter_fold_ap(params, X_train, y_train, folds, seed=seed):
            val_scores.append(val_ap)
            train_scores.append(train_ap)
            trial.report(float(np.mean(val_scores)), step=fold_number)
            if trial.should_prune():
                raise optuna.TrialPruned()
        if on_trial_complete is not None:
            on_trial_complete(trial, sampled, params, val_scores, train_scores)
        return float(np.mean(val_scores))

    return objective


@dataclass(frozen=True)
class StudyBudget:
    """Budget borné d'une étude : nombre d'essais **et** durée maximale, quel que soit le premier atteint."""

    n_trials: int = 40
    timeout: float | None = 1800.0
    n_startup_trials: int = 5


def run_study(
    objective: Callable[[optuna.Trial], float],
    *,
    budget: StudyBudget = StudyBudget(),
    seed: int = 42,
    study_name: str = "indusense-fault-optuna",
    storage: str | None = None,
    sampler: optuna.samplers.BaseSampler | None = None,
    pruner: optuna.pruners.BasePruner | None = None,
) -> optuna.Study:
    """Lance une étude TPE + ``MedianPruner`` par défaut, reproductible et bornée en essais et en temps.

    ``sampler``/``pruner`` peuvent être fournis pour comparer des stratégies (ex. Partie B : étude
    lourde sans pruning vs étude frugale avec pruning agressif) sans dupliquer la boucle d'optimisation.
    """
    sampler = sampler or optuna.samplers.TPESampler(seed=seed, n_startup_trials=budget.n_startup_trials)
    pruner = pruner or optuna.pruners.MedianPruner(n_startup_trials=budget.n_startup_trials, n_warmup_steps=1)
    study = optuna.create_study(
        study_name=study_name, storage=storage, direction="maximize",
        sampler=sampler, pruner=pruner, load_if_exists=storage is not None,
    )
    study.optimize(objective, n_trials=budget.n_trials, timeout=budget.timeout, gc_after_trial=True)
    return study


def importance_table(study: optuna.Study, *, seed: int = 42) -> dict[str, float]:
    """Importance fANOVA des hyperparamètres : part de variation des scores associée à chacun.

    Ce n'est ni une causalité, ni l'importance des features du modèle (celle-ci vient de ``explain.py``) :
    c'est une lecture, sur les essais réalisés, de quels réglages ont le plus fait varier le score.
    """
    from optuna.importance import FanovaImportanceEvaluator, get_param_importances

    return get_param_importances(study, evaluator=FanovaImportanceEvaluator(seed=seed))
