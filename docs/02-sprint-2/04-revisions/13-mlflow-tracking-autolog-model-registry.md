# MLflow : architecture, tracking, autolog et Model Registry

## Définition et objectif

**MLflow** est un outil de **MLOps léger** : il trace automatiquement les expériences de Machine Learning (paramètres, métriques, artefacts, modèles) pour remplacer le suivi manuel par notebooks dupliqués (`model_v3_final_bis.ipynb`) qui rend impossible de retrouver « le modèle de la semaine dernière et ses paramètres ».

Cette fiche décrit l'outil MLflow lui-même (composants, concepts, API) de façon générale. Pour la méthode et les résultats concrets des campagnes déjà exécutées sur les données Indusense (Random Search puis Optuna), voir [MLflow et optimisation reproductible](../../revisions/mlflow-et-optimisation-reproductible.md), qui reste la référence pour la procédure pas-à-pas et les chiffres obtenus.

## Notions essentielles

### Les 4 composants de l'architecture MLflow

| Composant | Rôle | API principale |
|---|---|---|
| **Tracking Server** | Enregistre paramètres, métriques, tags, runs | `log_param()`, `log_metric()` |
| **Artifact Store** | Stocke les fichiers (modèles, graphiques, CSV) | `log_artifact()`, `log_model()` |
| **Model Registry** | Versionne les modèles, cycle de vie Staging → Production → Archived | `register_model()`, `load_model()` |
| **MLflow UI** | Interface web de comparaison visuelle des runs | commande `mlflow ui` |

### Vocabulaire

- **Experiment** : groupe logique de runs (ex. `InduSense_Panne_Detection`). `mlflow.set_experiment(...)`.
- **Run** : une exécution d'entraînement isolée, horodatée et identifiée par un `run_id`. `mlflow.start_run()`.
- **Params** : hyperparamètres fixes, enregistrés une fois par run. `mlflow.log_param(k, v)`.
- **Metrics** : valeurs numériques pouvant varier au cours du run (epoch, step). `mlflow.log_metric(k, v)`.
- **Artifacts** : fichiers produits (`.pkl`, `.png`, `.csv`). `mlflow.log_artifact(path)`.
- **Tags** : métadonnées libres (auteur, dataset, branche). `mlflow.set_tag(k, v)`.

MLflow capture aussi automatiquement, sans code supplémentaire : l'identifiant du run, l'horodatage de début/fin, la durée, le hash du commit Git et l'utilisateur.

### Code de base (log manuel)

```python
import mlflow
import mlflow.sklearn
from sklearn.metrics import recall_score, f1_score

mlflow.set_experiment("InduSense_Panne_Detection")
with mlflow.start_run(run_name="RF_baseline_v1"):
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 10)
    mlflow.log_param("random_seed", 42)

    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)

    mlflow.log_metric("recall", recall_score(y_test, y_pred))
    mlflow.log_metric("f1", f1_score(y_test, y_pred))
    mlflow.sklearn.log_model(rf, "model")
    mlflow.set_tag("author", "...")
```

### Autolog : capturer sans effort

`mlflow.sklearn.autolog()` (ou `mlflow.xgboost.autolog()`) capture automatiquement, dans le `with mlflow.start_run():`, les paramètres du constructeur, les métriques standard, le modèle sérialisé, la feature importance (RF) et les courbes d'entraînement (XGBoost). Limite : certains modèles ou métriques personnalisées ne sont pas couverts — combiner autolog avec `log_metric()` manuel si besoin.

**Dans ce dépôt**, les notebooks 06 et 07 désactivent explicitement l'autolog (`mlflow.sklearn.autolog(disable=True)`) et loguent manuellement chaque paramètre et métrique : ce choix pédagogique donne un contrôle plus fin sur ce qui est tracé pendant une recherche d'hyperparamètres à de nombreux essais (éviter de saturer le stockage d'artefacts à chaque essai).

### Comparer les runs

```python
runs = mlflow.search_runs(
    experiment_names=["InduSense_Panne_Detection"],
    order_by=["metrics.recall DESC"],
)
best_run = runs.loc[runs['metrics.recall'].idxmax()]
best_model = mlflow.sklearn.load_model(f"runs:/{best_run['run_id']}/model")
```

Dans l'UI MLflow : *Parallel Coordinates Plot* (impact de chaque hyperparamètre sur la métrique), *Scatter Plot* (ex. recall vs f1), tableau triable/filtrable.

### Model Registry : cycle de vie

`None` (run non enregistré) → `Staging` (candidat validé, en test) → `Production` (modèle actif) → `Archived` (modèle retiré).

```python
# Enregistrer un modèle depuis un run
with mlflow.start_run():
    mlflow.sklearn.log_model(rf, "model", registered_model_name="InduSense_PanneDetection")

# Promouvoir en staging
client = mlflow.MlflowClient()
client.transition_model_version_stage(name="InduSense_PanneDetection", version=1, stage="Staging")

# Charger depuis le registry
model = mlflow.pyfunc.load_model("models:/InduSense_PanneDetection/Staging")
```

`transition_model_version_stage` est l'API du support (MLflow ≤ 2.x) ; à vérifier contre la version installée, MLflow 3.x introduit des **alias** de modèle (`set_registered_model_alias`) qui remplacent progressivement les stages nommés — se référer à `mlflow.__version__` et à la documentation de la version effectivement installée avant d'écrire du code contre cette API.

### Valider un candidat avec pytest

Avant de promouvoir un modèle en `Staging`/`Production`, le valider programmatiquement : le modèle se charge, prédit sur un exemple isolé, prédit sur un batch, et atteint un seuil minimal de rappel sur le jeu de test.

```python
import mlflow, pytest
from sklearn.metrics import recall_score

MODEL_URI = "models:/InduSense_PanneDetection/Staging"

@pytest.fixture(scope="module")
def model():
    return mlflow.pyfunc.load_model(MODEL_URI)

def test_model_recall_above_threshold(model):
    recall = recall_score(y_test, model.predict(X_test))
    assert recall >= 0.70
```

### Bonnes pratiques de reproductibilité (rappel, cf. fiche POC ML)

Seeds fixées (`random_state`, `np.random.seed`, `PYTHONHASHSEED`), hash du dataset d'entraînement en tag (`dataset_hash`), versions de librairies en tag, convention de nommage claire pour experiment/run, et log des paramètres **avant** l'entraînement plutôt qu'après.

## Démarche

1. `mlflow.set_experiment(...)` puis `with mlflow.start_run():` pour chaque configuration comparée.
2. Logger paramètres avant l'entraînement, métriques et artefacts après.
3. Comparer les runs (`mlflow.search_runs()` ou UI) et sélectionner le meilleur sur la métrique principale.
4. Enregistrer ce run dans le Model Registry et le promouvoir en `Staging`.
5. Écrire des tests pytest qui valident le modèle chargé depuis le registry.
6. Documenter le modèle candidate dans un `README.md` dédié (contexte, métriques, limites).

## Exemple concret dans ce dépôt

Les notebooks [06 — optimisation et MLflow](../../../notebooks/02-sprint-2/01-maintenance-predictive/06-maintenance-optimisation-mlflow.ipynb) (Random Search) et [07 — Optuna et MLflow](../../../notebooks/02-sprint-2/01-maintenance-predictive/07-maintenance-optimisation-optuna-mlflow.ipynb) tracent chaque essai (params, métriques CV/test, matrices de confusion en artefacts) dans un store SQLite local (`.mlflow/mlflow.db`, exclu de Git) et une expérience MLflow dédiée par campagne (`indusense-random-search-pedagogique`, `indusense-optuna-pedagogique`).

**Écart avec le TP S13** : ces deux notebooks couvrent le Tracking Server et l'Artifact Store, mais **pas encore** le Model Registry (promotion en `Staging`) ni les tests pytest de validation du candidat, ni un `README.md` de modèle candidate — livrables explicitement demandés par le support de la séance 13. `pytest` n'est d'ailleurs pas installé dans l'environnement `.venv` principal au moment de la rédaction de cette fiche. C'est un travail restant, distinct de ce qui est déjà validé.

## Erreurs fréquentes et bonnes pratiques

- Logger les paramètres après l'entraînement : perd la trace des réglages exacts utilisés si l'entraînement échoue en cours de route.
- Utiliser l'autolog sans vérifier ce qu'il capture réellement pour un modèle donné ; certains modèles ou métriques métier restent à logger manuellement.
- Promouvoir un modèle en `Production` sans être passé par un `Staging` testé.
- Oublier de tagger la version des librairies : un modèle rechargé plus tard avec une version différente de scikit-learn peut se comporter différemment ou refuser de se charger.
- Confondre `run_id` (une exécution) et `registered_model_name` (une famille de versions de modèle dans le registry) : ce ne sont pas le même identifiant.

## Points à retenir pour le QCM

- Les 4 composants MLflow : Tracking Server, Artifact Store, Model Registry, UI.
- Un run appartient à un experiment ; un modèle enregistré (`registered_model_name`) a plusieurs versions.
- Cycle de vie du Model Registry : None → Staging → Production → Archived.
- `mlflow.sklearn.autolog()` capture params, métriques, modèle et feature importance en une ligne, mais a des limites.
- Un modèle candidate se valide par des tests programmatiques (pytest) avant promotion.

## Points à savoir expliquer lors de la soutenance

- Pourquoi MLflow remplace avantageusement des notebooks nommés manuellement (`_v3_final_bis`).
- La différence entre logger manuellement et utiliser l'autolog, et pourquoi ce projet a désactivé l'autolog pour les campagnes d'hyperparamètres.
- Ce que garantit le passage par `Staging` avant `Production`, et ce qu'un test pytest vérifie concrètement.
- L'état d'avancement réel de ce dépôt vis-à-vis du TP S13 : tracking fait, registry et tests pytest restant à faire.

## Sources du cours

- `08_mlflow_aelion.pdf`, support Aelion « MLOps léger : tracking & artefacts — MLflow » (Sprint 2, US2.1, Séance 13), diapositives 1 à 21.

## Pour aller plus loin

- [MLflow — Tracking Quickstart](https://mlflow.org/docs/latest/ml/tracking/tutorials/local-database)
- [MLflow — Model Registry](https://mlflow.org/docs/latest/ml/model-registry/)
- [Fiche notebook-spécifique : MLflow et optimisation reproductible](../../revisions/mlflow-et-optimisation-reproductible.md)
