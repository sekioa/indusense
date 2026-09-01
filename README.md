# Indusense

## Contexte

Projet réalisé pendant le parcours IT de la formation certifiante « Concevoir et implémenter une solution d'intelligence artificielle ».

Le notebook `data-exercice-1.ipynb` explore des relevés d'incidents saisis par les opérateurs d'une usine fonctionnant 24 h/24 selon les trois-huit. Il utilise principalement `pandas` pour :

- examiner la structure du fichier CSV et ses dix premières lignes ;
- déterminer et adapter les types des colonnes ;
- calculer les valeurs minimales et maximales de la sévérité et de la date ;
- compter les machines, opérateurs et commentaires distincts ;
- produire un rapport lisible en texte brut ;
- calculer, en bonus, les moyennes et médianes de la télémétrie.

Les fichiers du dossier `datas/` sont considérés comme des données Bronze : ils sont lus sans être modifiés.

Le notebook [build-data-bronze.ipynb](build-data-bronze.ipynb) documente le passage de ces CSV vers PostgreSQL : contrat Bronze, modèles SQLAlchemy, migration Alembic, ingestion par lot et contrôle de l'idempotence.

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

1. ouvrir `data-exercice-1.ipynb` ;
2. vérifier que le kernel affiché en haut à droite est `Python 3 (ipykernel)` ;
3. utiliser **Run > Run All Cells** pour exécuter toutes les cellules dans l'ordre ;
4. vérifier que la dernière cellule affiche `Validation réussie`.

## Arrêter JupyterLab

1. Enregistrer le notebook avec `Ctrl + S`.
2. Revenir dans la fenêtre PowerShell qui exécute JupyterLab.
3. Appuyer sur `Ctrl + C` et confirmer l'arrêt si nécessaire.

Fermer uniquement l'onglet du navigateur n'arrête pas toujours le serveur Jupyter.
