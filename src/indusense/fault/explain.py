"""Explicabilité SHAP (TreeExplainer) : importance globale, cas locaux, dépendances.

Ce module ne trace aucune figure : il prépare des données (``shap.Explanation``, tableaux) que le
notebook ou le script appelant affichent avec ``shap.plots.*``. La classe expliquée est toujours la
classe positive (panne, index 1) d'un classifieur binaire.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shap
from sklearn.pipeline import Pipeline


POSITIVE_CLASS_INDEX = 1


def impute_features(pipeline: Pipeline, X: pd.DataFrame) -> pd.DataFrame:
    """Applique la seule étape d'imputation du pipeline, en conservant colonnes et index.

    SHAP explique le modèle d'arbres, pas l'imputeur : il lui faut donc des features déjà imputées,
    dans le même espace que celui vu par ``RandomForestClassifier.fit``.
    """
    imputed = pipeline.named_steps["imputation"].transform(X)
    return pd.DataFrame(imputed, columns=X.columns, index=X.index)


def build_explanation(pipeline: Pipeline, X_sample: pd.DataFrame) -> shap.Explanation:
    """Calcule les valeurs SHAP de la classe positive pour un échantillon de features.

    ``TreeExplainer`` est exact et rapide pour un modèle à base d'arbres (contrairement à
    ``KernelExplainer``, agnostique mais coûteux) : il exploite la structure interne des arbres.
    """
    X_imputed = impute_features(pipeline, X_sample)
    explainer = shap.TreeExplainer(pipeline.named_steps["model"])
    explanation = explainer(X_imputed)
    return shap.Explanation(
        values=explanation.values[..., POSITIVE_CLASS_INDEX],
        base_values=explanation.base_values[..., POSITIVE_CLASS_INDEX],
        data=explanation.data,
        feature_names=list(X_imputed.columns),
    )


def top_features(explanation: shap.Explanation, *, n: int = 10) -> pd.DataFrame:
    """Classe les features par impact moyen absolu (``|SHAP|``) et donne le sens moyen de l'effet.

    ``impact`` mesure l'ampleur (toujours positive) ; ``direction`` (signe de la moyenne signée) indique
    si la feature pousse en moyenne vers la panne (positif) ou vers l'absence de panne (négatif) — une
    lecture de corrélation, pas de causalité.
    """
    values = explanation.values
    table = pd.DataFrame({
        "feature": explanation.feature_names,
        "impact": np.abs(values).mean(axis=0),
        "direction": np.sign(values.mean(axis=0)),
    })
    return table.sort_values("impact", ascending=False).head(n).reset_index(drop=True)


@dataclass(frozen=True)
class FlaggedInstance:
    """Une prédiction individuelle choisie pour l'explication locale (waterfall)."""

    position: int
    index_label: object
    score: float


def pick_flagged_instance(y_scores: np.ndarray, X_sample: pd.DataFrame, *, threshold: float) -> FlaggedInstance:
    """Choisit, parmi les positions les plus au-dessus du seuil, un cas flagué à expliquer localement."""
    above_threshold = np.flatnonzero(y_scores >= threshold)
    if not len(above_threshold):
        raise ValueError("Aucune prédiction ne dépasse le seuil fourni.")
    position = int(above_threshold[np.argmax(y_scores[above_threshold])])
    return FlaggedInstance(
        position=position, index_label=X_sample.index[position], score=float(y_scores[position]),
    )


def dependence_pairs(top_features_table: pd.DataFrame, *, n: int = 3) -> list[str]:
    """Liste les ``n`` features les plus impactantes, pour tracer un dependence plot sur chacune."""
    return top_features_table["feature"].head(n).tolist()
