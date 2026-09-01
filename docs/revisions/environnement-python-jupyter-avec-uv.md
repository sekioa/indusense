# Environnement Python et Jupyter avec UV

## Définition et objectif

UV gère les versions de Python, les environnements virtuels, les dépendances et leur verrouillage. Un **environnement virtuel** est un Python isolé avec ses propres bibliothèques. Un environnement par projet évite qu'un exercice modifie ou casse les dépendances d'un autre.

Jupyter sépare trois éléments :

- le **serveur Jupyter**, programme local qui fournit l'interface dans le navigateur ;
- le **notebook**, fichier `.ipynb` composé de blocs appelés cellules ;
- le **kernel**, processus Python qui exécute le code contenu dans les cellules.

L'objectif est de créer un projet reproductible et de vérifier que le notebook utilise bien le Python isolé de ce projet.

## Prérequis et point de départ

- UV doit être installé et la commande `uv --version` doit afficher une version.
- Ouvrir PowerShell dans `D:\source\A4U\FormationIA`.
- Une connexion Internet est nécessaire lors du premier téléchargement de Python et des bibliothèques.

## Démarche recommandée

### 1. Créer le dossier de l'exercice

```powershell
New-Item -ItemType Directory -Path exercices\premier-notebook
Set-Location exercices\premier-notebook
```

La première commande crée le dossier. La seconde déplace le terminal dans ce dossier. Vérifier l'emplacement courant avec :

```powershell
Get-Location
```

Le chemin affiché doit se terminer par `FormationIA\exercices\premier-notebook`.

### 2. Initialiser le projet Python

```powershell
uv python install 3.12
uv init --bare --python 3.12
uv add --dev ipykernel
```

- `uv python install 3.12` rend Python 3.12 disponible pour UV.
- `uv init --bare --python 3.12` crée un projet minimal décrit par `pyproject.toml`.
- `uv add --dev ipykernel` ajoute le composant qui permettra à Jupyter d'exécuter les cellules avec le Python du projet.

À la fin, le dossier doit contenir `pyproject.toml`, `uv.lock` et `.venv`. Le dossier caché `.venv` est l'environnement virtuel du projet.

### 3. Ajouter les bibliothèques utiles

Dans PowerShell, toujours depuis le dossier du projet :

```powershell
uv add numpy pandas matplotlib scikit-learn
```

Ces bibliothèques servent respectivement au calcul numérique, à la manipulation de données tabulaires, aux graphiques et au machine learning. UV les inscrit dans `pyproject.toml` et verrouille leurs versions dans `uv.lock`.

### 4. Enregistrer le kernel du projet

```powershell
$venvPath = (Resolve-Path .venv).Path
uv run ipython kernel install --user --env VIRTUAL_ENV $venvPath --name formation-ia-premier-notebook
```

La première ligne récupère le chemin absolu de `.venv`. La seconde enregistre auprès de Jupyter un kernel nommé `formation-ia-premier-notebook`, lié à cet environnement.

Le résultat attendu contient un message indiquant que le kernelspec a été installé. Un **kernelspec** est la petite configuration qui explique à Jupyter quel Python démarrer.

### 5. Démarrer JupyterLab

Dans PowerShell, saisir :

```powershell
uv run --with jupyter jupyter lab
```

UV lance Jupyter dans un environnement isolé sans l'installer globalement. Le terminal reste occupé : il affiche les journaux du serveur et doit rester ouvert pendant le travail.

L'absence de nouvelle invite `PS ...>` n'est donc pas un blocage. Elle signifie que le processus Jupyter continue de fonctionner au premier plan. Les messages `Serving notebooks from...` et `Jupyter Server ... is running at...`, sans trace d'erreur à leur suite, confirment que le serveur est prêt. Utiliser une nouvelle fenêtre PowerShell si d'autres commandes doivent être exécutées pendant que Jupyter fonctionne.

Le navigateur doit ouvrir automatiquement une adresse locale ressemblant à `http://localhost:8888/lab`. Une adresse `localhost` désigne la machine actuelle : le serveur Jupyter fonctionne sur le PC.

### 6. Créer le notebook dans l'interface

1. Dans la page **Launcher** de JupyterLab, repérer la section **Notebook**.
2. Sélectionner `formation-ia-premier-notebook`. Si un notebook est déjà ouvert avec un autre kernel, cliquer sur le nom du kernel en haut à droite et choisir celui du projet.
3. Jupyter crée un fichier notebook vide contenant une première cellule.
4. Une **cellule de code** est un bloc dans lequel saisir du Python. `Shift + Entrée` exécute la cellule et passe à la suivante.

### Créer une cellule Markdown

Une **cellule Markdown** contient du texte mis en forme plutôt que du code Python. Elle sert notamment à ajouter un titre, une explication ou les conclusions d'une analyse dans le notebook.

Dans l'interface JupyterLab ouverte dans le navigateur :

1. Cliquer dans la cellule à convertir afin de la sélectionner. Une barre bleue apparaît à sa gauche.
2. Dans la barre d'outils située en haut du notebook, ouvrir la liste qui affiche actuellement **Code**.
3. Sélectionner **Markdown**.
4. Saisir par exemple `# Mon premier notebook`.
5. Appuyer sur `Shift + Entrée` pour afficher le texte mis en forme et passer à la cellule suivante.

Le symbole `#` placé au début d'une ligne crée un titre Markdown. La cellule ne doit plus afficher le repère d'exécution `[ ]:` réservé aux cellules de code.

Raccourci équivalent : appuyer sur `Échap` pour passer en mode commande, puis sur `M` pour convertir la cellule sélectionnée en Markdown. Appuyer ensuite sur `Entrée` pour modifier son contenu.

## Vérification

Dans la première cellule, saisir puis exécuter avec `Shift + Entrée` :

```python
import sys
print(sys.executable)
```

Le chemin affiché doit se terminer par `premier-notebook\.venv\Scripts\python.exe`. Cela prouve que le kernel utilise l'environnement du projet et non l'alias Python de Windows.

Dans une nouvelle cellule, tester ensuite les imports déclarés :

```python
import numpy
import pandas
import sklearn

print("Environnement opérationnel")
```

Le résultat attendu est `Environnement opérationnel` sans message d'erreur.

### 7. Arrêter proprement Jupyter

1. Enregistrer le notebook avec `Ctrl + S` dans le navigateur.
2. Revenir dans le terminal PowerShell qui exécute Jupyter.
3. Appuyer sur `Ctrl + C` et confirmer l'arrêt si PowerShell ou Jupyter le demande.

Fermer seulement l'onglet du navigateur ne garantit pas l'arrêt du serveur.

## Fichiers importants

- `pyproject.toml` : décrit le projet et ses dépendances directes.
- `uv.lock` : verrouille les versions résolues pour rendre l'environnement reproductible.
- `.venv/` : contient l'environnement local généré ; il ne doit pas être versionné.
- `.python-version` : indique la version de Python attendue lorsqu'elle est créée par UV.

## Erreurs fréquentes et bonnes pratiques

- Installer des packages globalement mélange les dépendances de plusieurs projets.
- Un mauvais kernel peut exécuter le notebook avec un autre Python que celui du projet.
- `No module named ...` signifie généralement que le package n'est pas installé dans l'environnement utilisé par le kernel. Vérifier d'abord `sys.executable`, puis ajouter la dépendance avec `uv add` depuis PowerShell.
- Une page Jupyter qui ne s'ouvre pas automatiquement : copier dans le navigateur l'URL complète affichée par le terminal, y compris son éventuel jeton temporaire, sans partager ce jeton.
- Préférer `uv add paquet` à une installation manuelle : la dépendance est alors documentée et verrouillée.
- Utiliser une version de Python imposée par le formateur lorsqu'elle est précisée. Python 3.12 est ici un choix de compatibilité, pas une exigence du livret.

### Différence entre PowerShell et Bash

La commande suivante appartient à Bash et ne fonctionne pas dans PowerShell :

```bash
export UV_LINK_MODE=copy
```

Dans PowerShell, une variable d'environnement limitée au terminal courant s'écrit ainsi :

```powershell
$env:UV_LINK_MODE = "copy"
```

Le mode `copy` demande à UV de copier les fichiers au lieu de créer des liens physiques. Il supprime l'avertissement rencontré lorsque le cache UV et le projet se trouvent sur deux disques différents. Cet avertissement concerne les performances et ne signifie pas que l'installation a échoué.

### Commande `jupyter` non reconnue

Ajouter `ipykernel` au projet ne rend pas nécessairement la commande `jupyter` disponible globalement dans PowerShell. Il faut demander à UV de fournir temporairement Jupyter :

```powershell
uv run --with jupyter jupyter lab
```

### Refus d'accès au dossier d'exécution Jupyter

Jupyter écrit des fichiers temporaires dans un **dossier d'exécution**, notamment l'adresse et l'identifiant du serveur. Dans un terminal isolé, l'écriture dans `%APPDATA%\jupyter\runtime` peut être refusée avec `PermissionError: [Errno 13] Permission denied`.

La correction consiste à créer un dossier temporaire autorisé et à indiquer son chemin à Jupyter :

```powershell
$jupyterRuntimePath = Join-Path ([System.IO.Path]::GetTempPath()) "formationia-jupyter-runtime"
New-Item -ItemType Directory -Path $jupyterRuntimePath -Force
$env:JUPYTER_RUNTIME_DIR = (Resolve-Path $jupyterRuntimePath).Path
uv run --link-mode=copy --with jupyter jupyter lab --no-browser
```

- `JUPYTER_RUNTIME_DIR` désigne le dossier dans lequel Jupyter peut écrire ses fichiers temporaires.
- `--link-mode=copy` évite l'avertissement lié aux disques différents.
- `--no-browser` empêche l'ouverture automatique du navigateur ; il faut copier localement l'adresse affichée par Jupyter.

L'adresse peut contenir un **jeton d'accès** après `token=`. Ce jeton autorise l'accès au serveur local : ne pas le partager ni le placer dans une capture ou un dépôt Git.

## Points à retenir pour le QCM

- Un environnement virtuel isole les dépendances d'un projet.
- Le lockfile rend la résolution des dépendances reproductible.
- Le kernel exécute les cellules ; le serveur Jupyter fournit l'interface.

## Points à savoir expliquer lors de la soutenance

- Comment recréer l'environnement du projet sur une autre machine.
- Comment prouver que le notebook utilise le bon interpréteur et les bonnes dépendances.

## Pour aller plus loin

- [uv — Guide des projets](https://docs.astral.sh/uv/guides/projects/) : environnements, dépendances et lockfile reproductibles.
- [Jupyter — Documentation utilisateur](https://docs.jupyter.org/en/latest/) : rôle du serveur, des notebooks et des kernels.
