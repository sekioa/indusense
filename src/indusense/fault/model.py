"""Fabrique du pipeline de détection de panne (imputation + RandomForest)."""

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


BASELINE_PARAMS: dict = {
    "n_estimators": 300,
    "max_depth": 12,
    "min_samples_leaf": 5,
    "min_samples_split": 2,
    "max_features": "sqrt",
}

MAX_FEATURE_CHOICES = ("sqrt", "15%", "25%", "35%", "50%")


def decode_params(sampled: dict) -> dict:
    """Traduit un tirage Optuna (``max_features_choice`` catégoriel) en paramètres RandomForest valides."""
    params = dict(sampled)
    choice = params.pop("max_features_choice")
    params["max_features"] = "sqrt" if choice == "sqrt" else float(choice.rstrip("%")) / 100
    return params


def build_pipeline(params: dict, *, seed: int = 42) -> Pipeline:
    """Construit le pipeline imputation médiane + RandomForest, pondéré pour les pannes rares.

    ``class_weight='balanced_subsample'`` recalcule la pondération des classes à chaque arbre à partir
    du tirage bootstrap : c'est l'équivalent RandomForest du ``scale_pos_weight`` de XGBoost.
    """
    return Pipeline([
        ("imputation", SimpleImputer(strategy="median")),
        ("model", RandomForestClassifier(
            **params, random_state=seed, class_weight="balanced_subsample", bootstrap=True, n_jobs=-1,
        )),
    ])
