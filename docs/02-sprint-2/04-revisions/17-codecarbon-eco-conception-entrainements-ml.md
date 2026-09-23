# CodeCarbon et éco-conception des entraînements ML

## Objectif concret et point de départ

Cette fiche permet de mesurer le coût énergétique d'un entraînement ou d'une étude Optuna avec
**CodeCarbon**, puis d'arbitrer entre gain de performance et coût carbone. À l'issue de la lecture,
l'utilisateur doit savoir instrumenter une fonction Python, lire un `emissions.csv`, et expliquer pourquoi
« plus d'essais » n'est pas automatiquement une bonne décision.

**Point de départ observable.** Le groupe de dépendances `ml` du projet (`uv sync --group ml`) installe
`codecarbon` (et `shap`). Le module [`src/indusense/fault/carbon.py`](../../../src/indusense/fault/carbon.py)
encapsule `codecarbon.OfflineEmissionsTracker` pour le TP B7 (maintenance prédictive).

**Prérequis.** Connaître la notion de kilowattheure (kWh) comme unité d'énergie, et de gCO2eq (grammes
d'équivalent CO2) comme unité d'émissions ramenant plusieurs gaz à effet de serre à un seul indicateur
comparable.

## 1. Pourquoi mesurer le coût, pas seulement le score

Un score de validation ne dit rien du **coût** pour l'obtenir. Deux études qui atteignent la même PR-AUC
n'ont pas la même valeur si l'une consomme dix fois plus d'énergie que l'autre. La démarche **Green AI**
consiste à considérer le coût de calcul (temps, énergie, émissions) comme une contrainte de conception au
même titre que la performance, pas comme un détail à mesurer après coup.

## 2. CodeCarbon : ce qu'il mesure et comment

`EmissionsTracker` (ou sa variante `OfflineEmissionsTracker`) échantillonne périodiquement la consommation
du CPU, du GPU et de la RAM pendant qu'un bloc de code s'exécute, puis convertit l'énergie consommée (kWh)
en émissions (kg CO2eq) à l'aide d'un facteur d'intensité carbone du réseau électrique.

Le mode **offline** (`OfflineEmissionsTracker`) évite tout appel réseau de géolocalisation IP : il exige de
préciser explicitement `country_iso_code` (ex. `"FRA"` pour la France, dont le mix électrique est fortement
décarboné grâce au nucléaire — un même entraînement émettrait bien plus avec un mix `"POL"` ou `"DEU"`, plus
carbonés). C'est le choix retenu ici, adapté à une salle de formation sans dépendre d'un service externe.

```python
from codecarbon import OfflineEmissionsTracker

tracker = OfflineEmissionsTracker(
    project_name="indusense-fault",
    country_iso_code="FRA",
    output_dir="outputs/fault",
    output_file="emissions.csv",
)
tracker.start()
try:
    model.fit(X_train, y_train)
finally:
    tracker.stop()

data = tracker.final_emissions_data
print(data.duration, data.energy_consumed, data.emissions)  # secondes, kWh, kg CO2eq
```

`tracker.stop()` renvoie les émissions totales (kg CO2eq) ; `tracker.final_emissions_data` donne le détail
(`duration`, `energy_consumed` en kWh, `emissions` en kg, plus la répartition CPU/GPU/RAM). Ce fichier
`emissions.csv` est un **journal brut** ; `indusense.fault.carbon.append_summary_row` en tire une ligne de
synthèse (`step, duration_seconds, energy_kwh, emissions_kg, metric_name, metric_value`) accumulée dans
`outputs/fault/emissions_summary.csv` — un format directement lisible pour comparer les étapes entre elles.

## 3. Encapsuler une étape avec `indusense.fault.carbon.track_step`

```python
from indusense.fault import carbon

result, run = carbon.track_step(
    lambda: build_pipeline(params, seed=42).fit(X_train, y_train),
    step="baseline",
    output_dir=Path("outputs/fault"),
)
print(run.duration_seconds, run.energy_kwh, run.emissions_kg)
```

`track_step` renvoie **deux** valeurs : le résultat de la fonction encapsulée (ici, le modèle entraîné) et
un `TrackedRun` (durée, kWh, kg CO2eq). Ce découplage permet d'instrumenter n'importe quelle étape —
entraînement seul, étude Optuna entière — sans changer sa signature ni son comportement.

## 4. Coût par point de performance

La question n'est pas « combien d'émissions ? » isolément, mais « combien d'émissions **pour quel gain** ? » :

```python
def cost_per_performance_point(baseline_metric, candidate_metric, candidate_emissions_kg):
    gain = candidate_metric - baseline_metric
    if gain <= 0:
        return float("inf")
    return candidate_emissions_kg / gain
```

Un coût par point de performance **infini** signale un candidat qui n'apporte aucun gain net : toute son
émission est un coût pur, sans contrepartie. Un coût élevé mais fini peut rester justifié si le gain est
stratégique (ex. un modèle mis en production à grande échelle) ; un coût faible pour un gain confirmé est le
cas le plus favorable.

## 5. Résultat réellement observé (TP B7, notebook `08-optimisation-carbone-explicabilite.ipynb`)

Étude principale (15 essais tirés, budget `n_trials=15, timeout=600s`, pruning `MedianPruner`) :

| Étape | Essais | Élagués | Durée (s) | Émissions (gCO2eq) | AP CV |
| --- | --- | --- | --- | --- | --- |
| Baseline (RandomForest, `n_estimators=300`) | 1 | 0 | 28,0 | 0,044 | 0,5575 |
| Étude bornée avec pruning | 15 tirés | 5 (10 complets) | 313,7 | 0,512 | 0,5657 |

Comparaison **étude lourde vs étude frugale** (même espace de recherche, 8 essais chacune — voir la nuance
méthodologique en section 3 du notebook) :

| Étude | Essais | Élagués | AP CV | Durée (s) | gCO2eq | Coût par point d'AP (gCO2eq) |
| --- | --- | --- | --- | --- | --- | --- |
| Lourde (`NopPruner`, sans pruning) | 8 | 0 | 0,5658 | 335,7 | 0,551 | 66,7 |
| Frugale (`MedianPruner`, pruning agressif) | 8 | 4 | 0,5644 | 128,7 | 0,210 | 30,9 |

La frugale perd 0,0014 d'AP CV (négligeable face à la dispersion habituelle entre folds) mais coûte **62 %
de moins en émissions** et **62 % de temps en moins**, avec la moitié de ses essais élagués avant d'avoir
entraîné tous les folds. Le coût par point d'AP gagné par rapport à la baseline est plus de deux fois plus
favorable pour la frugale (30,9 gCO2eq/point) que pour la lourde (66,7 gCO2eq/point) : ici, la parcimonie est
la meilleure décision Green AI, le pruning n'a pas coûté de performance mesurable.

Ces ordres de grandeur (dixièmes à quelques dixièmes de gramme de CO2eq pour un entraînement tabulaire de
cette taille) restent très faibles comparés à un entraînement Deep Learning sur GPU : la mesure sert ici
avant tout à installer le réflexe et la méthode, plus qu'à révéler un enjeu carbone massif sur ce jeu de
données précis. L'enjeu change d'échelle avec la taille du modèle, le nombre d'essais et le matériel utilisé
(GPU, datacenter cloud).

## 6. Erreurs fréquentes et bonnes pratiques

- **Mode en ligne par défaut** : sans `country_iso_code` explicite, `EmissionsTracker` tente une
  géolocalisation réseau — à éviter en salle de formation ou en environnement sans accès internet fiable ;
  préférer `OfflineEmissionsTracker` avec un code pays fixé.
- **Comparer des émissions sans comparer le gain** : toujours rapporter le coût à la métrique de performance
  (coût par point d'AP), pas seulement lire le total de gCO2eq.
- **Mesurer une seule fois puis généraliser** : la consommation dépend de la machine (CPU, présence d'un
  GPU) ; une mesure sur un poste ne se transpose pas telle quelle à un autre.
- **Oublier le hors-champ** : CodeCarbon mesure le calcul local, pas le stockage des données, ni le
  transfert réseau, ni l'inférence en production répétée à grande échelle.

## 7. Points à retenir pour le QCM

- CodeCarbon convertit une consommation mesurée (kWh) en émissions estimées (kg CO2eq) via un facteur
  d'intensité carbone du réseau électrique.
- Le mode offline nécessite un `country_iso_code` explicite et évite un appel réseau de géolocalisation.
- La bonne unité de décision est le coût par point de performance gagné, pas le total d'émissions seul.
- Une intensité carbone dépend fortement du pays : la France, à mix nucléaire dominant, est peu carbonée par
  kWh comparée à d'autres pays européens.

## 8. Points à savoir expliquer lors de la soutenance

- Pourquoi mesurer le coût énergétique fait partie d'une démarche de conception responsable (Green AI), pas
  d'une contrainte accessoire.
- Comment lire un `emissions_summary.csv` et argumenter un choix entre étude lourde et étude frugale.
- Les limites de la mesure (dépendance à la machine, périmètre local uniquement).

## Sources officielles

- [CodeCarbon — documentation](https://codecarbon.io/)
- [CodeCarbon — méthodologie de calcul](https://mlco2.github.io/codecarbon/methodology.html)

Correspondance exacte avec le référentiel C1 à C9 : à confirmer avec le Kit candidat local.
