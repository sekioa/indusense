# Indusense

## Contexte

Projet réalisé pendant le parcours IT de la formation certifiante « Concevoir et implémenter une solution d'intelligence artificielle ».

Le notebook `notebooks/01-sprint-1/01-exercices/03-data-exercice-1.ipynb` explore des relevés d'incidents saisis par les opérateurs d'une usine fonctionnant 24 h/24 selon les trois-huit. Il utilise principalement `pandas` pour :

- examiner la structure du fichier CSV et ses dix premières lignes ;
- déterminer et adapter les types des colonnes ;
- calculer les valeurs minimales et maximales de la sévérité et de la date ;
- compter les machines, opérateurs et commentaires distincts ;
- produire un rapport lisible en texte brut ;
- calculer, en bonus, les moyennes et médianes de la télémétrie.

Les fichiers du dossier `datas/` sont considérés comme des données Bronze : ils sont lus sans être modifiés.

Le notebook [02-build-data-bronze.ipynb](notebooks/01-sprint-1/02-pipeline-donnees/02-build-data-bronze.ipynb) documente le passage de ces CSV vers PostgreSQL : contrat Bronze, modèles SQLAlchemy, migration Alembic, ingestion par lot et contrôle de l'idempotence.

## TP : optimisation et MLflow

Le [notebook 06](notebooks/02-sprint-2/01-maintenance-predictive/06-maintenance-optimisation-mlflow.ipynb) optimise la Random Forest avec une recherche aléatoire. Le [notebook 07](notebooks/02-sprint-2/01-maintenance-predictive/07-maintenance-optimisation-optuna-mlflow.ipynb) reprend le protocole avec Optuna et une expérience MLflow indépendante. La [fiche de révision](docs/revisions/mlflow-et-optimisation-reproductible.md) donne la procédure et les limites méthodologiques.

Livrables Random Search : [synthèse d'une page](output/pdf/synthese-optimisation-mlflow.pdf), [synthèse éditable](docs/02-sprint-2/03-suivi/03-synthese-optimisation-mlflow.md) et [matrices de confusion](outputs/optimisation/matrices-confusion.png). Livrables Optuna : [synthèse d'une page](output/pdf/synthese-optimisation-optuna-mlflow.pdf), [synthèse éditable](docs/02-sprint-2/03-suivi/04-synthese-optimisation-optuna-mlflow.md), [comparaison des deux recherches](output/pdf/comparaison-random-search-optuna.pdf) et [matrices de confusion](outputs/optimisation-optuna/matrices-confusion-optuna.png).

Depuis la racine du dépôt, après `uv sync --dev`, exécuter `./scripts/start-mlflow.ps1` dans PowerShell. Ouvrir ensuite [MLflow local](http://127.0.0.1:5000) et sélectionner l'expérience `indusense-random-search-pedagogique` ou `indusense-optuna-pedagogique`. La base, l'étude Optuna et les modèles sont conservés dans `.mlflow/`, exclu de Git. Le serveur reste local ; `Ctrl+C` l'arrête sans effacer les résultats.

## Prérequis

- Git ;
- [UV](https://docs.astral.sh/uv/) ;
- une connexion Internet lors de la première installation des dépendances.

Vérifier que UV est disponible dans PowerShell :

```powershell
uv --version
```

La commande doit afficher un numéro de version.

## Installation depuis PowerShell

Cloner le dépôt, entrer dans son dossier, puis recréer l'environnement Python à partir de `pyproject.toml` et `uv.lock` :

```powershell
git clone https://github.com/sekioa/indusense.git
Set-Location indusense
uv sync
```

`uv sync` installe la version de Python attendue et les dépendances dans l'environnement virtuel local `.venv`. La commande réussit lorsqu'elle se termine sans message `error`.

Si le dépôt est déjà présent sur la machine :

```powershell
Set-Location D:\source\A4U\FormationIA\indusense
uv sync
```

## Lancer JupyterLab

Depuis le dossier `indusense`, exécuter :

```powershell
uv run --with jupyter jupyter lab
```

L'option `--with jupyter` fournit temporairement JupyterLab, qui n'est pas installé comme dépendance directe du projet. Le terminal reste occupé pendant le fonctionnement du serveur : c'est le comportement attendu.

Dans l'interface ouverte dans le navigateur :

1. ouvrir `notebooks/01-sprint-1/01-exercices/03-data-exercice-1.ipynb` ;
2. vérifier que le kernel affiché en haut à droite est `Python 3 (ipykernel)` ;
3. utiliser **Run > Run All Cells** pour exécuter toutes les cellules dans l'ordre ;
4. vérifier que la dernière cellule affiche `Validation réussie`.

## Arrêter JupyterLab

1. Enregistrer le notebook avec `Ctrl + S`.
2. Revenir dans la fenêtre PowerShell qui exécute JupyterLab.
3. Appuyer sur `Ctrl + C` et confirmer l'arrêt si nécessaire.

Fermer uniquement l'onglet du navigateur n'arrête pas toujours le serveur Jupyter.
