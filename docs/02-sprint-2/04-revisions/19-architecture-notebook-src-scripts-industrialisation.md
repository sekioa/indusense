# Architecture notebook / src / scripts : industrialiser un projet ML

## Objectif concret et point de départ

Cette fiche explique pourquoi et comment séparer un projet ML en trois couches — **notebook**, **`src/`**,
**`scripts/`** — à partir de l'exemple réel du TP B7 : le passage des notebooks `01`→`07` (logique mêlée à
l'affichage) au package [`src/indusense/fault/`](../../../src/indusense/fault/) orchestré par
[`scripts/run_fault_pipeline.py`](../../../scripts/run_fault_pipeline.py).

**Point de départ observable.** Avant ce refactor, toute la logique de maintenance prédictive (chargement,
split temporel, entraînement, seuils, Optuna) vivait dans des cellules de notebook, avec des chemins parfois
supposés relatifs au dossier courant et un ordre d'exécution des cellules qui pouvait changer les scores
obtenus.

## 1. Le problème qu'un notebook seul ne résout pas

Un notebook mélange trois responsabilités différentes : **calculer**, **afficher**, **raconter**. Cela pose
trois problèmes concrets, tous rencontrés dans les notebooks B5/B6 de ce projet avant refactor :

1. **Impossible à rejouer en CLI.** Il faut ouvrir Jupyter, exécuter les cellules dans le bon ordre, et
   espérer qu'aucune n'a été modifiée entre deux exécutions.
2. **Impossible à tester.** `pytest`/`unittest` ne peuvent pas facilement isoler « la fonction qui choisit le
   seuil F2 » d'un notebook : elle est mélangée à `display()` et `plt.show()`.
3. **Chemins fragiles.** Un chemin écrit en dur (`C:\Users\...`) ou relatif à un dossier de lancement suppose
   que tout le monde ouvre le notebook depuis le même endroit — faux dès qu'un collègue clone le dépôt
   ailleurs, ou qu'une CI l'exécute depuis un autre répertoire de travail.

## 2. La règle des trois couches

```
notebook.ipynb          → explore, raconte, affiche des figures ; IMPORTE la logique, ne la contient pas
src/indusense/fault/     → LOGIQUE réutilisable et testable : fonctions pures, sans print ni figure
scripts/run_*.py          → PIPELINE : orchestre les briques src/ en une commande, arguments CLI, aucun calcul
```

**Notebook.** Explore et raconte : commentaires pédagogiques, `display()`, `plt.show()`, décisions
argumentées. Il *importe* `indusense.fault.*` et *appelle* ses fonctions ; il ne redéfinit jamais leur
logique dans une cellule.

**`src/`.** Contient les fonctions et classes réutilisables, chacune avec une responsabilité claire :
`data.py` (chargement + split), `model.py` (fabrique de pipeline), `evaluate.py` (métriques et seuils),
`train.py` (entraînement + journalisation), `tune.py` (recherche Optuna), `carbon.py` (mesure CodeCarbon),
`explain.py` (SHAP). Ces fonctions **renvoient** des valeurs ou des objets (`dataclass`, `DataFrame`,
`shap.Explanation`) ; elles n'appellent jamais `print()` de manière décorative ni `plt.show()`.

**`scripts/`.** Le point d'entrée exécutable : `python scripts/run_fault_pipeline.py --horizon 24 --tune`.
Il *orchestre* — appelle les fonctions de `src/` dans l'ordre, gère les arguments CLI (`argparse`), écrit les
artefacts sur disque. Il ne contient **aucun calcul métier** : si une ligne du script calcule une métrique
plutôt que d'appeler une fonction de `src/`, c'est un signe que cette ligne devrait être déplacée.

## 3. Où couper une cellule qui mélange calcul et affichage

Une cellule de notebook typique avant refactor :

```python
scores = model.predict_proba(X_val)[:, 1]
threshold = choose_threshold(y_val, scores)          # calcul
metrics = measure(y_val, scores, threshold)           # calcul
print(f"F2 = {metrics['F2']:.4f}")                    # affichage
display(pd.DataFrame([metrics]))                       # affichage
```

Après refactor : `choose_threshold` et `evaluate_at_threshold` (les deux premières lignes) vivent dans
`indusense.fault.evaluate`, testées indépendamment (voir `tests/unit/test_fault_evaluate.py`) ; le notebook
ne garde que l'appel et l'affichage :

```python
from indusense.fault import evaluate

threshold = evaluate.choose_threshold(y_val, scores)
metrics = evaluate.evaluate_at_threshold(y_val, scores, threshold)
display(pd.DataFrame([metrics.as_dict()]))
```

Règle pratique : une fonction `src/` **ne prend jamais de décision d'affichage** (pas de `print` narratif,
pas de `plt.show()`) ; elle peut renvoyer un objet que l'appelant choisit ensuite d'afficher ou non.

## 4. Pas de chemin en dur : `config.py` ou constantes relatives

Deux conventions coexistent dans ce projet selon les packages : `indusense/vision/` (Deep Learning) utilise
des constantes `DEFAULT_*` avec des chemins **relatifs à la racine du dépôt** (`Path("datas/deep-learning")`),
en supposant que le code s'exécute avec la racine du projet comme répertoire courant — ce que garantissent
`uv run python scripts/...` et les notebooks (qui remontent l'arborescence jusqu'à trouver `pyproject.toml`).
`indusense/fault/` (ce TP) suit la même convention pour rester cohérent avec le reste du projet, plutôt que
d'introduire un `config.py` centralisé qui n'existe pas ailleurs dans le dépôt.

```python
DEFAULT_DATA_PATH = Path("datas/gold_dataset_20260622-080603.csv")  # relatif à la racine du dépôt
```

Peu importe la convention retenue (constantes relatives ou `config.py`), la règle reste : **jamais** un
chemin absolu propre à une machine (`C:\Users\SeKioA\...`) écrit en dur dans une fonction `src/`. Le code doit
tourner à l'identique sur la machine d'un collègue et en CI, quel que soit le dossier de lancement — d'où
l'ancrage systématique sur `pyproject.toml` (`Path(__file__).resolve().parents[N]` dans un script, recherche
ascendante dans un notebook).

## 5. Reproductibilité : graine fixée et artefacts non écrasés

Deux exigences distinctes pour qu'une pipeline soit rejouable :

- **Même graine partout** (`seed=42` propagé à `RandomForestClassifier`, au sampler Optuna, aux découpages
  aléatoires) : deux exécutions avec les mêmes données et les mêmes paramètres doivent produire le même score.
- **Artefacts horodatés, jamais écrasés silencieusement** : `scripts/run_fault_pipeline.py` construit un
  `run_name` unique (`fault-pipeline-h{horizon}-{timestamp_utc}`), utilisé à la fois comme nom de run MLflow
  parent et comme **dossier de sortie dédié** `outputs/fault/{run_name}/` (résumé JSON, figures SHAP, tableau
  d'arbitrage, `emissions.csv` brut de CodeCarbon). Relancer deux fois la commande produit donc deux dossiers
  distincts, jamais une écriture silencieuse par-dessus le résultat précédent. Seul
  `outputs/fault/emissions_summary.csv` est **partagé entre exécutions** par conception : c'est un journal
  cumulatif de comparaison inter-runs, dont chaque ligne porte elle-même la colonne `run_name` qui l'identifie
  — voir [`carbon.append_summary_row`](../../../src/indusense/fault/carbon.py).

## 6. Tests : la vraie récompense du refactor

Une fonction `src/` qui ne dépend que de ses arguments (pas de fichier lu en dur, pas d'état global) devient
testable avec des données synthétiques minuscules, sans charger le Gold dataset complet :

```python
def test_excludes_ids_and_all_leakage_columns_for_the_chosen_horizon(self):
    features = select_features(gold_frame(), horizon=24)
    self.assertEqual(sorted(features), ["feat_a", "feat_b"])
```

Voir [`tests/unit/test_fault_data.py`](../../../tests/unit/test_fault_data.py) et
[`tests/unit/test_fault_evaluate.py`](../../../tests/unit/test_fault_evaluate.py). Ce projet exécute ses
tests avec `python -m unittest` (aucune dépendance `pytest` n'est installée ici), en cohérence avec les
tests déjà présents dans `tests/unit/` pour les autres modules.

## 7. Erreurs fréquentes et bonnes pratiques

- **Un notebook qui redéfinit une fonction déjà présente dans `src/`** : signe que l'import a été oublié ou
  que le refactor est incomplet — une seule définition doit faire foi.
- **Un script qui calcule** (ex. une métrique recalculée à la main dans `scripts/run_*.py` au lieu d'appeler
  `evaluate.py`) : à déplacer vers `src/`.
- **Un chemin qui marche « chez moi »** : toujours vérifier qu'il est ancré sur la racine du dépôt, pas sur
  le répertoire courant du terminal au moment du lancement.
- **Pas de graine, ou une graine différente à chaque étape** (ex. split aléatoire vs modèle) : rend deux
  exécutions incomparables.
- **Écraser silencieusement un artefact précédent** : nommer les artefacts et les runs de façon unique
  (horodatage) plutôt que d'utiliser toujours le même nom de fichier.

## 8. Points à retenir pour le QCM

- Les trois couches sont : notebook (explore/raconte), `src/` (logique testable), `scripts/` (pipeline).
- Une fonction `src/` ne doit ni imprimer de message décoratif, ni tracer de figure : elle renvoie des
  valeurs ou des objets.
- Un chemin en dur propre à une machine casse la reproductibilité sur une autre machine ou en CI.
- Un artefact d'exécution doit être identifiable (horodatage, nom de run unique), pas écrasé silencieusement.

## 9. Points à savoir expliquer lors de la soutenance

- Pourquoi un notebook seul ne suffit pas pour un livrable rejouable en production ou en CI.
- Comment identifier, dans une cellule existante, la frontière entre calcul et affichage.
- Pourquoi la même graine doit être propagée à chaque source d'aléa (modèle, sampler, split).
- Ce qui garantit qu'une deuxième exécution de la pipeline ne perd pas les résultats de la première.

## Sources officielles

- [Cookiecutter Data Science — structurer un projet ML](https://cookiecutter-data-science.drivendata.org/)
- [argparse — interfaces en ligne de commande](https://docs.python.org/3/library/argparse.html)

Correspondance exacte avec le référentiel C1 à C9 : à confirmer avec le Kit candidat local.
