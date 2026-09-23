# Optimisation des hyperparamètres et validation croisée

## Objectif concret et point de départ

Cette fiche permet de comprendre puis de comparer trois méthodes de réglage des hyperparamètres : `GridSearchCV`, `RandomizedSearchCV` et Optuna. À l'issue de la lecture, l'utilisateur doit pouvoir expliquer leur fonctionnement, choisir une stratégie adaptée et préparer l'optimisation de la `RandomForestClassifier` retenue dans le TP Indusense.

**Point de départ observable.** Trois classifieurs ont déjà été comparés avec le même protocole temporel. La Random Forest a obtenu la meilleure PR-AUC sur la validation (`0,5970`) et a été retenue. Le jeu de test a déjà servi à la comparaison pédagogique ; pour une future mesure réellement finale, il faudra réserver une nouvelle période encore jamais consultée.

**Prérequis.** Il faut connaître la différence entre train, validation et test, savoir qu'une PR-AUC élevée est souhaitable pour la classe positive minoritaire, et disposer de `X_train`, `y_train`, `X_validation`, `y_validation`, `X_test` et `y_test`. Le projet contient scikit-learn, SciPy et Optuna. Le notebook 07 exécute une étude Optuna distincte et la trace dans une nouvelle expérience MLflow.

## 1. Ce que l'on optimise

Un **paramètre appris** est déterminé par l'algorithme pendant `fit`. Dans un arbre, les règles de séparation et les valeurs prédites dans les feuilles sont des paramètres appris.

Un **hyperparamètre** est choisi avant l'entraînement et contrôle la manière d'apprendre. Pour une Random Forest :

- `n_estimators` : nombre d'arbres ;
- `max_depth` : profondeur maximale d'un arbre ;
- `min_samples_split` : nombre minimal d'observations pour diviser un nœud ;
- `min_samples_leaf` : nombre minimal d'observations dans une feuille ;
- `max_features` : nombre de features candidates à chaque séparation ;
- `max_samples` : fraction des observations tirée pour chaque arbre si le bootstrap est actif ;
- `class_weight` : poids donné aux classes pendant l'apprentissage.

L'**optimisation des hyperparamètres** cherche la configuration qui maximise une métrique estimée sur des données non utilisées pour ajuster le modèle. Une **configuration**, aussi appelée *candidate* ou *trial*, est un ensemble précis de valeurs d'hyperparamètres.

Cette optimisation ne « rend pas automatiquement le modèle meilleur ». Elle peut aussi suradapter les choix à la validation, augmenter fortement le temps de calcul ou retenir un gain trop faible pour être robuste.

## 2. Pourquoi une simple validation ne suffit pas toujours

Avec une seule séparation train/validation, le score dépend beaucoup de la période choisie. La **validation croisée**, ou *cross-validation*, répète l'entraînement sur plusieurs séparations appelées **folds** :

1. le modèle est entraîné sur la partie train du fold ;
2. il est évalué sur la partie validation du même fold ;
3. l'opération est répétée pour chaque fold ;
4. les scores sont agrégés, généralement par une moyenne et un écart-type.

Le score moyen estime la performance attendue. L'**écart-type** renseigne sur sa stabilité : deux configurations de moyenne voisine ne sont pas équivalentes si l'une varie beaucoup plus selon les périodes.

Exemple avec trois folds temporels :

```text
temps ───────────────────────────────────────────────────────>

fold 1 : [ entraînement ] [ gap ] [ validation ]
fold 2 : [       entraînement       ] [ gap ] [ validation ]
fold 3 : [              entraînement              ] [ gap ] [ validation ]
                                                    [ test final ]
```

Le **gap**, ou zone d'exclusion, sépare la fin de l'entraînement du début de la validation. Pour la cible « panne dans les 24 prochaines heures », un gap correspondant à 24 heures est une précaution cohérente : les labels situés juste avant la frontière dépendent eux-mêmes des 24 heures suivantes.

### Combien d'entraînements sont lancés ?

Le coût principal est approximativement :

`nombre de configurations × nombre de folds`

Si 120 configurations sont comparées avec 4 folds, 480 entraînements sont nécessaires. Avec `refit=True`, scikit-learn réalise ensuite un entraînement supplémentaire avec la meilleure configuration sur toutes les données transmises à `fit`.

## 3. Choisir le bon découpage de validation croisée

Le choix des folds dépend de la structure des données. Utiliser davantage de folds ne corrige pas un mauvais découpage.

| Situation | Splitter courant | Règle importante |
| --- | --- | --- |
| Observations indépendantes, classification déséquilibrée | `StratifiedKFold` | Conserver approximativement la proportion de classes dans chaque fold. |
| Plusieurs lignes appartiennent à un même patient, client ou machine indépendante | `GroupKFold` ou `StratifiedGroupKFold` | Un groupe ne doit jamais être à la fois dans train et validation. |
| Prédiction du futur à partir du passé | `TimeSeriesSplit` ou folds temporels personnalisés | Ne jamais entraîner sur une date postérieure à la validation. |

### Cas Indusense : la contrainte temporelle est prioritaire

Les snapshots horaires proches sont corrélés et leurs fenêtres se recouvrent. `KFold`, `StratifiedKFold` ou un mélange aléatoire placeraient des observations très proches dans train et validation et produiraient un score trop optimiste. Il faut conserver l'ordre chronologique.

Une subtilité supplémentaire existe : 15 machines peuvent partager le même timestamp. Les lignes d'un même instant doivent rester dans le même fold. Un `TimeSeriesSplit` appliqué aveuglément aux lignes peut couper un timestamp en deux selon leur ordre. La solution robuste consiste à :

1. trier les données par `window_end`, puis par machine ;
2. construire les frontières sur les timestamps uniques ;
3. reporter chaque frontière sur toutes les lignes qui portent ces timestamps ;
4. vérifier que `max(date_train) < min(date_validation)` pour chaque fold ;
5. appliquer un gap temporel de 24 h si la granularité reste horaire et si la cible regarde 24 h dans le futur.

`TimeSeriesSplit(gap=24)` compte des **lignes**, pas des heures. Il ne représente donc 24 h que s'il existe exactement une ligne par heure. Avec plusieurs machines par heure, il faut convertir la durée en lignes avec beaucoup de prudence ou, de préférence, créer des splits à partir des timestamps uniques.

### Protocole recommandé pour le TP actuel

**Application dans le notebook 06 (MLflow).** Le gap de 24 h doit aussi protéger les frontières entre train, validation dédiée et test : les splits fournis sont chronologiques mais jointifs. Le notebook 06 retire donc les 24 dernières heures du train et de la validation dédiée avant de recalculer la référence et le candidat avec le même protocole. Ses scores ne sont pas directement comparables aux anciens scores sans purge. Les essais, refits et sondes de sensibilité sont tracés dans MLflow ; voir la [fiche pratique](../../revisions/mlflow-et-optimisation-reproductible.md).

Afin de préserver les rôles existants :

1. lancer la recherche et ses folds temporels uniquement dans le `train` historique ;
2. laisser `refit=True` réentraîner la meilleure configuration sur tout ce train ;
3. choisir le seuil F2 sur le jeu de validation déjà réservé ;
4. figer hyperparamètres et seuil ;
5. n'utiliser le test qu'une seule fois pour l'évaluation finale.

Si le test actuel a déjà influencé une décision, il n'est plus entièrement vierge. Il faut alors présenter le résultat comme pédagogique et réserver une période future pour la confirmation finale.

## 4. Pipeline et prévention des fuites

Une **fuite de données** se produit lorsqu'une information indisponible au moment réel de la prédiction influence l'entraînement. La recherche doit recevoir un `Pipeline` contenant tous les prétraitements appris : imputation, encodage, sélection de features et modèle.

À chaque fold, le pipeline ajuste alors l'imputation uniquement sur le train du fold. Prétraiter tout `X_train` avant la validation croisée ferait connaître aux transformations les valeurs des folds de validation.

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        (
            "model",
            RandomForestClassifier(
                random_state=42,
                class_weight="balanced_subsample",
                n_jobs=-1,
            ),
        ),
    ]
)
```

Dans une `Pipeline`, les paramètres sont nommés avec la forme `nom_etape__nom_parametre`. Exemple : `model__max_depth`.

## 5. Grid Search : explorer une grille exhaustive

### Définition

`GridSearchCV` évalue toutes les combinaisons explicites d'une grille. Si la grille contient 3 valeurs de `n_estimators`, 4 profondeurs et 3 tailles minimales de feuille, elle comporte `3 × 4 × 3 = 36` configurations.

Avec 4 folds, cela produit `36 × 4 = 144` entraînements, plus le refit final si `refit=True`.

### Quand l'utiliser ?

Grid Search convient lorsque :

- l'espace de recherche est petit ;
- les valeurs pertinentes sont déjà bien ciblées ;
- on souhaite vérifier systématiquement les combinaisons proches d'une bonne zone ;
- le coût d'un entraînement reste acceptable.

Il devient inefficace lorsque plusieurs hyperparamètres possèdent beaucoup de valeurs : le nombre de combinaisons augmente de manière multiplicative, phénomène appelé **explosion combinatoire**.

### Exemple complet

L'exemple suppose que `temporal_cv` est un splitter ou un iterable de couples d'indices construit sans fuite temporelle.

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    "model__n_estimators": [200, 400, 600],
    "model__max_depth": [8, 12, 16, None],
    "model__min_samples_leaf": [2, 5, 10],
    "model__max_features": ["sqrt", 0.5],
}

grid_search = GridSearchCV(
    estimator=pipeline,
    param_grid=param_grid,
    scoring={
        "pr_auc": "average_precision",
        "roc_auc": "roc_auc",
    },
    refit="pr_auc",
    cv=temporal_cv,
    n_jobs=1,
    return_train_score=True,
    verbose=2,
)

grid_search.fit(X_train, y_train)

print(grid_search.best_params_)
print(grid_search.best_score_)
```

Ici, `scoring` calcule plusieurs métriques, mais `refit="pr_auc"` désigne la PR-AUC comme critère de sélection. Dans scikit-learn, le nom de scorer `average_precision` correspond à l'Average Precision, couramment utilisée pour résumer la courbe précision-rappel.

### Résultat visible attendu

Après succès :

- `best_params_` contient les hyperparamètres retenus ;
- `best_score_` contient la PR-AUC moyenne obtenue en validation croisée ;
- `best_estimator_` contient le pipeline réentraîné sur tout `X_train` ;
- `cv_results_` contient les scores et durées de toutes les configurations.

## 6. Random Search : échantillonner un budget fixe

### Définition

`RandomizedSearchCV` ne teste pas toutes les combinaisons. Il tire un nombre fixé de configurations, défini par `n_iter`, dans des listes ou des distributions.

Avec `n_iter=40` et 4 folds, le budget vaut `40 × 4 = 160` entraînements, quelle que soit la taille théorique de l'espace. `random_state` rend les tirages reproductibles.

### Pourquoi est-il souvent préférable en première exploration ?

Dans une grande grille, certains hyperparamètres influencent fortement le score tandis que d'autres ont peu d'effet. Random Search couvre davantage de valeurs différentes pour chaque dimension sans payer le produit cartésien complet. Il convient donc bien pour localiser rapidement une zone prometteuse.

### Exemple complet

```python
from scipy.stats import randint, uniform
from sklearn.model_selection import RandomizedSearchCV

param_distributions = {
    "model__n_estimators": randint(150, 801),
    "model__max_depth": [8, 12, 16, 24, None],
    "model__min_samples_split": randint(2, 21),
    "model__min_samples_leaf": randint(1, 16),
    "model__max_features": ["sqrt", "log2", 0.3, 0.5, 0.8],
    "model__max_samples": uniform(0.6, 0.4),
}

random_search = RandomizedSearchCV(
    estimator=pipeline,
    param_distributions=param_distributions,
    n_iter=40,
    scoring={
        "pr_auc": "average_precision",
        "roc_auc": "roc_auc",
    },
    refit="pr_auc",
    cv=temporal_cv,
    random_state=42,
    n_jobs=1,
    return_train_score=True,
    verbose=2,
)

random_search.fit(X_train, y_train)

print(random_search.best_params_)
print(random_search.best_score_)
```

`randint(150, 801)` tire un entier entre 150 et 800 inclus. `uniform(0.6, 0.4)` tire une valeur continue entre 0,6 inclus et 1,0 exclu. Utiliser une distribution continue évite de limiter artificiellement la recherche à quelques valeurs arbitraires.

### Résultat visible attendu

Les mêmes attributs principaux que pour Grid Search sont disponibles. La différence est que `cv_results_` ne contient que les `n_iter` configurations tirées.

## 7. Optuna : adapter la recherche aux essais précédents

### Définition

Optuna organise l'optimisation autour de quatre objets :

- une **objective function** reçoit un essai et retourne le score à optimiser ;
- un **trial** est une configuration évaluée ;
- un **sampler** choisit les prochaines valeurs à essayer à partir de l'historique ;
- une **study** conserve les essais, leurs paramètres et leurs scores.

Par défaut, Optuna utilise un `TPESampler`. TPE signifie *Tree-structured Parzen Estimator* : le sampler exploite les résultats passés pour proposer progressivement des zones susceptibles d'être meilleures. C'est la différence majeure avec le tirage indépendant de Random Search.

Le **pruning** arrête tôt un essai peu prometteur lorsqu'un algorithme fournit des résultats intermédiaires. Une Random Forest scikit-learn entraînée en un seul `fit` ne fournit pas naturellement ces étapes intermédiaires à Optuna (contrairement à XGBoost, qui rapporte un score après chaque itération de boosting) : il ne faut donc pas promettre un gain de pruning **automatique** avec cette Random Forest.

**Mise à jour (TP B7, `indusense.fault.tune`).** Un pruning reste possible sans modèle itératif, en changeant ce que Optuna considère comme une « étape » : au lieu de rapporter après chaque itération de boosting, on rapporte l'AP moyenne **après chaque fold** de la validation croisée temporelle (`trial.report(valeur_partielle, step=numero_fold)`), puis on interroge `trial.should_prune()`. Un essai nettement pire que la médiane des essais précédents, dès le premier ou le deuxième fold, est arrêté (`optuna.TrialPruned`) sans entraîner les folds restants. C'est un pruning **inter-fold**, pas inter-itération : il fonctionne avec n'importe quel modèle, y compris un modèle non itératif comme RandomForest, du moment que l'entraînement est répété plusieurs fois (ici, une fois par fold). Voir `make_objective` dans [`src/indusense/fault/tune.py`](../../../src/indusense/fault/tune.py) et le notebook [`08-optimisation-carbone-explicabilite.ipynb`](../../../notebooks/02-sprint-2/01-maintenance-predictive/08-optimisation-carbone-explicabilite.ipynb).

**Résultat réellement observé.** Sur 15 essais tirés (budget `n_trials=15, timeout=600s`), **5 ont été élagués** par le `MedianPruner` avant d'avoir entraîné leurs trois folds, et 10 sont allés à leur terme ; le meilleur essai complet atteint une AP CV de 0,5657 (baseline 0,5575). Comparée à une étude sans pruning de même taille (voir [la fiche CodeCarbon](17-codecarbon-eco-conception-entrainements-ml.md), section 5), le pruning fait économiser l'essentiel du coût de calcul sans perte mesurable de performance.

### Exemple complet

```python
import optuna
from sklearn.model_selection import cross_validate


def objective(trial):
    candidate = pipeline.set_params(
        model__n_estimators=trial.suggest_int(
            "n_estimators", 150, 800, step=50
        ),
        model__max_depth=trial.suggest_categorical(
            "max_depth", [8, 12, 16, 24, None]
        ),
        model__min_samples_split=trial.suggest_int(
            "min_samples_split", 2, 20
        ),
        model__min_samples_leaf=trial.suggest_int(
            "min_samples_leaf", 1, 15
        ),
        model__max_features=trial.suggest_categorical(
            "max_features", ["sqrt", "log2", 0.3, 0.5, 0.8]
        ),
        model__max_samples=trial.suggest_float(
            "max_samples", 0.6, 1.0
        ),
    )

    scores = cross_validate(
        candidate,
        X_train,
        y_train,
        cv=temporal_cv,
        scoring="average_precision",
        n_jobs=1,
        return_train_score=False,
    )
    return scores["test_score"].mean()


sampler = optuna.samplers.TPESampler(seed=42)
study = optuna.create_study(direction="maximize", sampler=sampler)
study.optimize(objective, n_trials=40)

print(study.best_params)
print(study.best_value)
```

`direction="maximize"` indique qu'une PR-AUC plus élevée est meilleure. `n_trials=40` fixe le budget. Pour rendre une étude durable et reprenable, on peut ensuite lui ajouter un stockage persistant ; ce n'est pas nécessaire pour comprendre le premier essai.

### Point de vigilance sur l'objet `pipeline`

scikit-learn clone les estimateurs dans `cross_validate`, mais appeler successivement `set_params` sur le même pipeline rend le code moins explicite. Dans une implémentation destinée à durer, créer une fonction `build_pipeline(params)` ou cloner le pipeline avec `sklearn.base.clone` rend chaque essai indépendant et plus facile à relire.

## 8. Comparaison des trois techniques

| Critère | Grid Search | Random Search | Optuna |
| --- | --- | --- | --- |
| Choix des configurations | Toutes les combinaisons de la grille | Tirages dans des listes ou distributions | Suggestions adaptées aux essais précédents |
| Budget | Subi par la taille de la grille | Fixé par `n_iter` | Fixé par `n_trials` ou une durée |
| Reproductibilité | Déterministe pour une grille et des folds fixés | Nécessite `random_state` | Nécessite notamment une seed du sampler |
| Espace continu | Discrétisé manuellement | Bien pris en charge par des distributions | Natif avec `suggest_float` et `suggest_int` |
| Pruning | Non | Non | Automatique si le modèle est itératif (boosting) ; possible autrement via un pruning inter-fold (voir mise à jour B7 ci-dessus) |
| Dépendance supplémentaire | Non | Non, SciPy est déjà présent ici | Oui, Optuna |
| Usage recommandé | Affiner une petite zone | Première exploration sous budget | Recherche adaptative plus avancée et traçable |

### Recommandation pour le TP

Ne pas lancer les trois recherches en parallèle et ne pas leur accorder des budgets incomparables. L'ordre pédagogique recommandé est :

1. **Randomized Search** avec un budget réduit et explicite pour explorer largement ;
2. analyser les résultats, les temps et la stabilité entre folds ;
3. **Grid Search** autour de la meilleure zone pour comprendre l'exploration exhaustive locale ;
4. **Optuna** dans une expérience séparée, avec le même espace, les mêmes folds, la même métrique et un nombre d'essais comparable.

Pour une comparaison loyale, l'idéal est de fixer le même nombre maximal de configurations et les mêmes folds. Sinon, on compare autant le budget de calcul que la méthode.

## 9. Lire les résultats sans se limiter au gagnant

```python
import pandas as pd

results = pd.DataFrame(random_search.cv_results_)
columns = [
    "rank_test_pr_auc",
    "mean_test_pr_auc",
    "std_test_pr_auc",
    "mean_train_pr_auc",
    "mean_fit_time",
    "params",
]

print(results[columns].sort_values("rank_test_pr_auc").head(10))
```

Il faut examiner :

- `mean_test_pr_auc` : performance moyenne hors entraînement ;
- `std_test_pr_auc` : variabilité entre périodes ;
- `mean_train_pr_auc - mean_test_pr_auc` : indice de surapprentissage ;
- `mean_fit_time` : coût d'entraînement ;
- la proximité des meilleures configurations : une large zone stable est plus rassurante qu'un optimum isolé.

Une différence de `0,001` de PR-AUC n'est pas automatiquement significative. Si plusieurs configurations sont proches, préférer celle qui est plus simple, plus stable ou moins coûteuse.

## 10. Métrique d'optimisation et seuil de décision

La métrique d'optimisation doit être décidée avant de lire les résultats. Pour Indusense, `average_precision` est cohérente avec la PR-AUC utilisée pour comparer les classifieurs et avec le déséquilibre de la cible.

La recherche d'hyperparamètres et la recherche du seuil répondent à deux questions différentes :

- l'optimisation des hyperparamètres cherche un modèle qui **classe** bien les risques ;
- le réglage du seuil transforme les scores en alertes selon le compromis entre faux positifs et faux négatifs.

Le seuil F2 ne doit pas être choisi sur le test. Dans le protocole recommandé, il est optimisé sur la validation dédiée après la sélection des hyperparamètres sur les folds internes du train.

Une approche plus avancée, appelée **validation croisée imbriquée** ou *nested cross-validation*, utilise une boucle interne pour optimiser les hyperparamètres et une boucle externe pour estimer leur performance sans biais. Elle est utile pour une estimation scientifique plus rigoureuse, mais son coût est élevé et elle ne remplace pas un test temporel futur.

## 11. Ressources de calcul et parallélisme

`n_jobs=-1` utilise tous les cœurs disponibles. Une Random Forest peut paralléliser ses arbres et la recherche peut paralléliser les configurations. Activer `n_jobs=-1` aux deux niveaux peut provoquer une **sur-souscription** : trop de tâches se disputent les mêmes CPU et la mémoire.

Pour un premier essai reproductible :

- paralléliser un seul niveau ;
- réduire la grille et le nombre de folds ;
- mesurer le temps d'une configuration avant de lancer le budget complet ;
- conserver `random_state=42` ou une autre seed documentée ;
- sauvegarder `cv_results_` ou l'étude Optuna ;
- ne lancer qu'une technique d'optimisation à la fois, conformément à la consigne.

Le parallélisme interne d'une seule recherche n'est pas la même chose que lancer Grid Search, Random Search et Optuna simultanément. Il doit néanmoins être limité selon les ressources de la machine.

## 12. Démarche pratique reproductible

1. **Dans le notebook**, charger les partitions existantes et vérifier les dates minimales et maximales.
2. Exclure les identifiants, timestamps bruts, autres labels et compteurs futurs des features.
3. Construire les folds à partir des timestamps uniques du train et appliquer le gap décidé.
4. Afficher, pour chaque fold, dates, effectifs et taux de positifs ; ne pas continuer si une validation précède son train.
5. Construire un pipeline contenant l'imputation et la Random Forest.
6. Choisir une seule technique, une métrique principale et un budget.
7. Exécuter la recherche sur `X_train`, `y_train` seulement.
8. Examiner score moyen, dispersion, écart train-validation et durée des meilleurs candidats.
9. Réentraîner la meilleure configuration sur le train si l'outil ne l'a pas déjà fait.
10. Choisir le seuil F2 sur la validation dédiée.
11. Figer la configuration et le seuil, puis évaluer une fois sur une période de test vierge.
12. Documenter l'espace exploré, le budget, les folds, la seed, le temps et les limites.

## 13. Vérifications minimales avant de croire le résultat

Pour chaque fold, vérifier explicitement :

```python
for fold_id, (train_idx, valid_idx) in enumerate(temporal_cv.split(X_train)):
    train_dates = train_timestamps.iloc[train_idx]
    valid_dates = train_timestamps.iloc[valid_idx]

    assert train_dates.max() < valid_dates.min()
    assert set(train_idx).isdisjoint(set(valid_idx))

    print(
        fold_id,
        train_dates.min(),
        train_dates.max(),
        valid_dates.min(),
        valid_dates.max(),
    )
```

Cet exemple n'est suffisant que si le splitter travaille correctement au niveau des timestamps. Avec plusieurs machines par timestamp, vérifier également qu'aucun timestamp ne se trouve dans les deux parties.

Après la recherche, comparer le meilleur candidat au réglage manuel déjà testé. Une optimisation réussie techniquement peut ne produire aucun gain utile. Le résultat attendu n'est donc pas nécessairement « un score supérieur », mais une conclusion argumentée et reproductible.

## 14. Erreurs fréquentes et diagnostic

- **Utiliser le test dans `GridSearchCV.fit`.** Le test participe alors au choix et ne mesure plus honnêtement la généralisation.
- **Utiliser `cv=5` par défaut sur les données temporelles.** En classification, scikit-learn utilise généralement des folds stratifiés, mais ils ne respectent pas le futur.
- **Prétraiter avant la cross-validation.** L'imputation ou la sélection de features apprend alors sur les folds de validation ; placer ces étapes dans un `Pipeline`.
- **Couper un timestamp partagé entre train et validation.** Construire les frontières sur les dates uniques, pas seulement sur les numéros de lignes.
- **Oublier l'horizon de 24 h à la frontière.** Ajouter un gap temporel cohérent et vérifier ce que contient exactement le label.
- **Construire une grille immense.** Calculer le nombre de configurations et le multiplier par le nombre de folds avant le lancement.
- **Optimiser l'accuracy.** Sur une classe minoritaire, elle peut favoriser un modèle qui ignore les pannes ; conserver la PR-AUC comme métrique principale.
- **Choisir le seuil sur les mêmes prédictions qui servent au test final.** Utiliser la validation dédiée.
- **Comparer 20 essais aléatoires à 500 essais Optuna.** Fixer un budget comparable ou documenter clairement l'écart.
- **Interpréter `best_score_` comme une garantie de production.** Il s'agit d'une moyenne sur les folds historiques étudiés.
- **Activer le parallélisme partout.** En cas de machine saturée ou d'erreur mémoire, paralléliser un seul niveau et réduire `pre_dispatch` ou le budget.
- **Ne conserver que `best_params_`.** Sauvegarder aussi les scores, dispersions, temps, versions, seed et périodes.

## 15. Premier Grid Search observé sur Indusense

Le notebook `05-maintenance-random-forest-grid-search.ipynb` a exécuté une première grille bornée le 16 septembre 2026 :

- 3 folds chronologiques construits sur les timestamps uniques du train ;
- gap de 24 heures entre train et validation de chaque fold ;
- 8 configurations, soit 24 fits, puis le refit final ;
- durée réelle de 2,67 minutes sur la machine utilisée ;
- métrique de sélection : PR-AUC moyenne des folds internes.

La meilleure configuration interne est :

```python
RandomForestClassifier(
    n_estimators=150,
    max_depth=8,
    min_samples_leaf=10,
    max_features="sqrt",
    class_weight="balanced_subsample",
    random_state=42,
)
```

Sa PR-AUC moyenne en validation croisée est `0,5620`, avec un écart-type de `0,0603`. Cette dispersion n'est pas négligeable : les trois périodes ne présentent pas exactement la même difficulté ni la même prévalence.

Sur la validation dédiée, la configuration atteint une PR-AUC de `0,5869`, contre `0,5970` pour le réglage manuel précédent. Sur le test pédagogique, elle atteint `0,6093`, contre `0,6156`. Cette première grille n'améliore donc pas la capacité de classement. En revanche, avec le seuil F2 de `0,3663` choisi sur validation, son F2 test atteint `0,5727`, légèrement au-dessus du `0,5691` précédent.

La conclusion correcte n'est pas que Grid Search a échoué : il a montré qu'une forêt plus petite et plus régularisée reste compétitive, réduit le surapprentissage interne et coûte moins cher à l'inférence. Il a aussi établi qu'aucune des huit configurations testées ne justifie de remplacer le réglage manuel sur le seul critère principal. Une recherche ultérieure pourra explorer une autre zone, mais le test actuel ne devra pas servir à guider cette nouvelle grille.

## 16. Résultat Optuna réellement observé

Le notebook 07 a exécuté 20 trials avec `TPESampler(seed=42)` : 5 propositions initiales pour explorer l'espace, puis 15 propositions guidées par les scores déjà obtenus. Chaque trial utilise trois folds chronologiques du train avec un gap de 24 h. Le budget complet représente 84 fits : 20 × 3 fits de validation croisée, 20 refits des trials pour leur journalisation MLflow, 3 fits CV de la référence et son refit final.

Le trial 12 gagne la sélection interne avec `n_estimators=450`, `max_depth=6`, `min_samples_leaf=30`, `min_samples_split=2` et `max_features=0.35`. Son AP CV vaut 0,5657 contre 0,5575 pour la référence. Sur le test, son AP vaut toutefois 0,6026 contre 0,6151 pour la référence ; il ne faut donc pas remplacer automatiquement la référence. La baisse de l'écart train-CV de 0,3563 à 0,1712 réduit un signal de surapprentissage, mais le recul sur le test rappelle que cet écart n'est pas une preuve suffisante de généralisation.

La matrice de confusion test passe de `VN=12 244, FP=4 423, FN=1 124, VP=2 354` à `VN=11 668, FP=4 999, FN=1 101, VP=2 377`. Optuna détecte donc 23 machine-heures positives supplémentaires, avec 576 fausses alertes supplémentaires. Une machine-heure positive est une observation horaire dont l'horizon de 24 h contient une panne ; plusieurs lignes positives peuvent correspondre à une seule panne réelle.

L'importance fANOVA place `max_depth` en tête avec 72,95 %, puis `min_samples_leaf` avec 13,61 %. Cette analyse décrit seulement les 20 trials et l'espace choisis. Pour comparer honnêtement Random Search et Optuna comme algorithmes, il faudrait leur donner le même espace, le même nombre d'essais et une nouvelle période de test encore jamais consultée.

## 17. Éco-conception et explicabilité

Le tuning ne doit pas chercher le dernier millième de score sans considérer son coût. Le support de cours recommande un arbitrage entre **performance**, **coût de calcul** et **émissions carbone** : un gain marginal peut ne pas justifier une recherche beaucoup plus lourde.

**CodeCarbon** estime l'énergie consommée en kWh et les émissions en équivalent CO2 à partir notamment du mix électrique, du PUE et d'un facteur carbone. Les résultats peuvent être conservés dans un fichier `emissions.csv`. La bonne unité de décision est le coût par point de performance gagné, pas le score seul.

Bonnes pratiques :

- fixer un budget en nombre d'essais ou en durée ;
- utiliser l'early stopping ou le pruning lorsque le modèle expose des résultats intermédiaires ;
- commencer par le modèle le plus simple qui répond au besoin ;
- conserver et réutiliser les résultats d'expériences au lieu de relancer inutilement les mêmes calculs.

**SHAP** attribue à chaque feature une contribution à la prédiction par rapport à une valeur de base. Une vue globale résume les features qui comptent sur l'ensemble des observations ; une vue locale explique une prédiction précise. SHAP explique ce que le modèle utilise, pas la cause réelle d'une panne. Une feature qui explique presque tout doit faire rechercher une fuite de données.

Pour le détail pratique (API, code, résultats réellement observés), voir les fiches dédiées
[CodeCarbon et éco-conception](17-codecarbon-eco-conception-entrainements-ml.md) et
[Explicabilité SHAP](18-explicabilite-shap-treeexplainer.md), toutes deux écrites pour le TP B7.

## 18. Points à retenir pour le QCM

- Un paramètre est appris pendant `fit` ; un hyperparamètre est fixé avant l'entraînement.
- La validation croisée entraîne et évalue plusieurs fois le modèle sur des folds distincts.
- `GridSearchCV` teste toutes les combinaisons d'une grille.
- `RandomizedSearchCV` teste `n_iter` configurations échantillonnées.
- Optuna organise la recherche en studies et trials, avec un sampler adaptatif possible.
- Le pruning n'est pas automatique avec une Random Forest (modèle non itératif), mais reste possible en le déclenchant après chaque fold de la CV plutôt qu'après chaque itération de boosting.
- `refit=True` réentraîne le meilleur candidat sur toutes les données fournies à `fit`.
- Les transformations apprises doivent être placées dans un `Pipeline` pour éviter les fuites entre folds.
- `StratifiedKFold` préserve approximativement les proportions de classes mais ne respecte pas l'ordre temporel.
- Une série temporelle doit être validée du passé vers le futur.
- Le test final ne sert ni au choix des hyperparamètres ni au choix du seuil.
- Le coût est approximativement le nombre de configurations multiplié par le nombre de folds.
- La moyenne seule est insuffisante : il faut aussi lire la dispersion et le temps de calcul.
- CodeCarbon sert à estimer le coût énergétique et carbone d'une expérience.
- SHAP mesure des contributions aux prédictions ; il ne démontre pas une causalité.

## 19. Points à savoir expliquer lors de la soutenance

- Pourquoi la Random Forest a d'abord été choisie avant d'optimiser ses hyperparamètres.
- Pourquoi une validation croisée aléatoire serait trompeuse sur les snapshots Indusense.
- Comment les folds temporels et le gap de 24 h préviennent les fuites à la frontière.
- Pourquoi les lignes des 15 machines portant le même timestamp doivent rester ensemble.
- La différence entre recherche exhaustive, recherche aléatoire et recherche adaptative.
- Pourquoi Randomized Search est recommandé pour l'exploration initiale et Grid Search pour un affinage local.
- Pourquoi le pruning d'Optuna n'est pas automatique avec cette Random Forest, et comment un pruning inter-fold le rend malgré tout possible (TP B7).
- Pourquoi la PR-AUC est optimisée, puis le seuil F2 choisi séparément.
- Comment le budget de calcul a été défini et comment la reproductibilité est assurée.
- Pourquoi une nouvelle période vierge reste nécessaire si le test existant a déjà été consulté.
- Comment arbitrer entre gain de performance, temps de calcul et impact carbone.
- Pourquoi une explication SHAP ne constitue pas une preuve de causalité métier.

## 20. Formulation courte pour présenter la démarche

> Nous optimisons les hyperparamètres de la Random Forest uniquement sur le train, avec une validation croisée chronologique et une zone d'exclusion adaptée à l'horizon de 24 heures. La PR-AUC moyenne sert à comparer les configurations, tandis que sa dispersion mesure leur stabilité. Nous commençons par Randomized Search pour explorer l'espace sous un budget fixé, puis nous pouvons affiner localement avec Grid Search et comparer séparément Optuna à budget égal. Le seuil F2 est choisi sur la validation dédiée et la période de test reste hors de toute décision.

## Sources officielles

- [scikit-learn — GridSearchCV](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html)
- [scikit-learn — RandomizedSearchCV](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.RandomizedSearchCV.html)
- [scikit-learn — Cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html)
- [scikit-learn — TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
- [Optuna — Efficient Optimization Algorithms](https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/003_efficient_optimization_algorithms.html)
- [Support Aelion - Optimisation, éco-conception et explicabilité](../01-cours/09_Optimisation.pdf)
- [Transcription du cours Tuning](../02-transcriptions/06-tuning-des-hyperparametres.txt)

Correspondance exacte avec le référentiel C1 à C9 : à confirmer avec le Kit candidat local.
