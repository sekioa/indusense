---
# Pour la référence sur les métadonnées de model card, voir la spec :
# https://github.com/huggingface/hub-docs/blob/main/modelcard.md?plain=1
# Guide : https://huggingface.co/docs/hub/model-cards
language: []
license: other
license_name: usage-interne-formation
library_name: scikit-learn
tags:
  - tabular-classification
  - predictive-maintenance
  - random-forest
  - indusense
pipeline_tag: tabular-classification
---

# Model Card for Indusense — Détection de pannes (RandomForest, horizon 24h)

<!-- Provide a quick summary of what the model is/does. -->

Classifieur binaire qui estime, pour une machine industrielle et une heure données, le risque qu'une
panne survienne dans les **24 heures suivantes**, à partir de mesures de télémétrie et de l'historique
d'incidents. Conçu pour prioriser les inspections de maintenance préventive, pas pour décider seul d'un arrêt.

## Model Details

### Model Description

<!-- Provide a longer summary of what this model is. -->

Le modèle est un `RandomForestClassifier` (scikit-learn) inséré dans un `Pipeline` avec une imputation
médiane des valeurs manquantes. Il prédit la colonne cible `label_failure_next_24h` du Gold dataset
Indusense : 1 si une panne est enregistrée dans les 24 heures suivant l'observation, 0 sinon. Une
observation est une **machine-heure** (état d'une machine pendant une heure) ; plusieurs machine-heures
positives peuvent correspondre à une seule panne réelle.

Trois familles de modèles ont été comparées à protocole égal (régression logistique, RandomForest,
HistGradientBoosting — voir `notebooks/02-sprint-2/01-maintenance-predictive/04-maintenance-comparaison-trois-modeles.ipynb`)
et la RandomForest a été retenue. Une étude Optuna bornée avec pruning a ensuite cherché à l'améliorer
(`notebooks/.../08-optimisation-carbone-explicabilite.ipynb`) : elle gagne en validation croisée interne
mais **ne se confirme pas sur le jeu de test** (voir [Results](#results) et
[Bias, Risks, and Limitations](#bias-risks-and-limitations)). Le modèle **retenu et décrit dans cette
fiche est donc la baseline manuelle**, plus simple et au moins aussi fiable sur données non vues pendant
le réglage.

- **Developed by:** Simon Fuger — parcours IT « Concevoir et implémenter une solution d'intelligence
  artificielle » (projet Indusense, formation certifiante)
- **Funded by [optional]:** Sans objet (projet pédagogique interne)
- **Shared by [optional]:** Sans objet
- **Model type:** Classification binaire supervisée sur données tabulaires — RandomForestClassifier
  (scikit-learn) dans un pipeline avec imputation médiane
- **Language(s) (NLP):** Sans objet (données tabulaires industrielles, aucun traitement de texte)
- **License:** Usage pédagogique interne — non publié, non couvert par une licence ouverte, non destiné
  en l'état à une exploitation commerciale ou à une mise en production sans validation supplémentaire
- **Finetuned from model [optional]:** Sans objet (entraîné from scratch)

### Model Sources [optional]

- **Repository:** [`src/indusense/fault/`](../../../src/indusense/fault/) (logique), [`scripts/run_fault_pipeline.py`](../../../scripts/run_fault_pipeline.py) (pipeline exécutable), suivi MLflow local (`.mlflow/`, expériences `indusense-optuna-pedagogique` et `indusense-fault-pipeline`)
- **Paper [optional]:** Sans objet
- **Demo [optional]:** Sans objet — voir les notebooks [`07-maintenance-optimisation-optuna-mlflow.ipynb`](../../../notebooks/02-sprint-2/01-maintenance-predictive/07-maintenance-optimisation-optuna-mlflow.ipynb) et [`08-optimisation-carbone-explicabilite.ipynb`](../../../notebooks/02-sprint-2/01-maintenance-predictive/08-optimisation-carbone-explicabilite.ipynb)

## Uses

<!-- Address questions around how the model is intended to be used, including the foreseeable users of the model and those affected by the model. -->

### Direct Use

À partir des mesures télémétriques horaires d'une machine (température, pression, tension, rotation —
moyennes/maximums/écarts-types sur 1h/6h/12h/24h), de son historique d'incidents récents et du temps
écoulé depuis sa dernière maintenance, le modèle produit un **score de risque de panne à 24 heures**. Ce
score, comparé au seuil retenu (`0,3299`), signale les machine-heures à faire inspecter en priorité par un
technicien de maintenance. Utilisateur direct visé : un technicien ou un planificateur de maintenance
préventive qui consulte ce score pour ordonner ses tournées d'inspection.

### Downstream Use [optional]

Le score peut alimenter un tableau de bord de supervision ou un système d'alerte qui le combine avec
d'autres signaux (règles métier, avis d'expert, criticité de la machine) avant toute décision. Il peut
aussi servir de point de départ pour un futur modèle par type de panne (`type_surchauffe`,
`type_vibration`, etc.), non traité dans cette version.

### Out-of-Scope Use

<!-- This section addresses misuse, malicious use, and uses that the model will not work well for. -->

- **Aucune décision automatique** d'arrêt de machine, de mise hors service ou d'action corrective sans
  validation humaine : la précision au seuil retenu n'est que de **35 % environ** (voir Evaluation), ce qui
  produit beaucoup de fausses alertes.
- **Pas validé pour un autre parc industriel** : entraîné sur 15 machines simulées d'un seul site
  (dataset Indusense) ; aucune preuve de généralisation à d'autres machines, capteurs ou usines.
- **Pas un outil de diagnostic causal** : les features SHAP (voir Model Examination) mesurent une
  corrélation apprise par le modèle, pas la cause mécanique réelle d'une panne.
- **Pas conçu pour un autre horizon** que 24 heures (le Gold dataset propose aussi 6h/12h/48h) sans
  réentraînement et revalidation complète.
- **Ne doit pas servir à évaluer la performance d'un opérateur ou d'une équipe** : les features utilisées
  décrivent l'état de la machine, pas le travail humain.

## Bias, Risks, and Limitations

<!-- This section is meant to convey both technical and sociotechnical limitations. -->

- **Signal faible.** Comme annoncé dans la consigne du TP, les features de ce jeu de données sont peu
  déterminantes : l'analyse SHAP (Model Examination) montre un impact **diffus** — la feature la plus
  importante (`hours_since_last_incident`) ne pèse que 26,2 % de la somme des dix impacts les plus forts.
  Aucune feature ne domine le classement.
- **Classes déséquilibrées.** Les pannes représentent environ 17 % des machine-heures (train : 16,6 % ;
  validation : 17,2 % ; test : 17,3 %). Le modèle est pondéré (`class_weight="balanced_subsample"`) et le
  seuil de décision est choisi pour maximiser le F2 (rappel pondéré plus fort que la précision), cohérent
  avec un coût métier où manquer une panne (faux négatif) coûte plus cher qu'une fausse alerte (faux
  positif) — mais cela se paie par une précision modeste (35 % environ, voir Results).
- **Le gain de l'optimisation Optuna ne se confirme pas sur le test.** L'étude bornée avec pruning trouve
  une configuration qui améliore l'AP en validation croisée interne (0,5657 contre 0,5575 pour la
  baseline), mais sur le jeu de test, cette même configuration est **moins bonne** que la baseline
  manuelle sur tous les indicateurs (AP 0,6026 contre 0,6151 ; F2 0,5583 contre 0,5689). C'est pourquoi la
  baseline, plus simple, est le modèle retenu et décrit ici — un rappel concret que « battre la baseline en
  CV » ne garantit pas de généraliser.
- **Test déjà partiellement consulté.** Le jeu de test a été regardé à plusieurs reprises au fil des TP
  précédents (comparaison de modèles, Random Search, Optuna) à des fins pédagogiques. Ses métriques ne
  constituent donc plus une mesure entièrement vierge de généralisation ; une confirmation sur une période
  réellement inédite est nécessaire avant tout déploiement réel.
- **Fuite de données non exclue par construction.** Une feature anormalement dominante en SHAP devrait
  toujours déclencher une vérification de fuite (corrélation avec le futur) ; ce n'est pas le cas ici
  (impact diffus), mais ce contrôle doit être répété si le jeu de données évolue.
- **Dérive (drift) non testée.** Le modèle n'a été évalué que sur la période couverte par le Gold dataset
  (juin 2025 à juin 2026, 15 machines). Son comportement sur une période ultérieure ou après un changement
  de procédé n'est pas connu.

### Recommendations

<!-- This section is meant to convey recommendations with respect to the bias, risk, and technical limitations. -->

Les utilisateurs (directs et en aval) doivent être informés du taux élevé de fausses alertes (précision
~35 % environ) et de l'absence de preuve de causalité des features mises en avant par SHAP. Toute alerte doit
être confirmée par un technicien avant toute action sur la machine. Avant un déploiement réel, il est
recommandé de : (1) évaluer le modèle sur une période de test réellement inédite, (2) envisager un
feature engineering complémentaire (lookback plus long, interactions) ou un changement d'horizon (48h) si
le rappel reste insuffisant, (3) répéter la mesure d'impact carbone si le modèle est réentraîné à plus
grande échelle.

## How to Get Started with the Model

```python
from indusense.fault import data, model

gold = data.load_gold(data.DEFAULT_DATA_PATH)
split = data.temporal_split(gold, horizon=24)

fitted = model.build_pipeline(model.BASELINE_PARAMS, seed=42).fit(
    split.X["train"], split.y["train"]
)
scores = fitted.predict_proba(split.X["test"])[:, 1]
alert = scores >= 0.3299  # seuil F2 retenu sur la validation, voir Evaluation
```

Le modèle entraîné est aussi journalisé dans MLflow (tracking SQLite local `.mlflow/mlflow.db`) et peut
être rechargé via `mlflow.sklearn.load_model(model_uri)` avec l'URI du run correspondant.

## Training Details

### Training Data

<!-- This should link to a Dataset Card, perhaps with a short stub of information on what the training data is all about as well as documentation related to data pre-processing or additional filtering. -->

Gold dataset Indusense (`datas/gold_dataset_20260622-080603.csv`, empreinte SHA-256
`2c6ee2408d6c764e57d7c7bacf17dc755954ca7b244a274363f07bf351203eee`) : 88 features tabulaires par
machine-heure (moyennes/maximums/écarts-types/tendances de température, pression, tension et rotation sur
des fenêtres de 1h/6h/12h/24h, compteurs et sévérité d'incidents récents, temps depuis la dernière
maintenance), pour 15 machines simulées, du 1er juin 2025 au 9 juin 2026. Cible : `label_failure_next_24h`.

| Rôle | Lignes | Positifs | Taux positif | Période |
| --- | --- | --- | --- | --- |
| Train | 93 630 | 15 545 | 16,60 % | 2025-06-01 → 2026-02-16 |
| Validation | 19 785 | 3 404 | 17,20 % | 2026-02-17 → 2026-04-13 |
| Test | 20 145 | 3 478 | 17,26 % | 2026-04-14 → 2026-06-09 |

Le split est **temporel** (train < validation < test), avec une **purge de 24 heures** à chaque frontière :
toute ligne dont la fenêtre se situe à moins de 24h (l'horizon prédit) du rôle suivant est retirée, pour
qu'aucun label ne dépende d'informations encore inconnues au moment de la prédiction. Voir
[`indusense.fault.data.temporal_split`](../../../src/indusense/fault/data.py).

### Training Procedure

#### Preprocessing [optional]

Imputation des valeurs manquantes par la **médiane** (`SimpleImputer(strategy="median")`), à l'intérieur
d'un `Pipeline` scikit-learn — jamais calculée avant le split ou en dehors des folds de validation
croisée, pour éviter toute fuite d'information entre train et validation.

#### Training Hyperparameters

- **Training regime:** CPU, précision flottante standard (pas d'entraînement en précision mixte : modèle
  à base d'arbres, non applicable).
- **Algorithme :** `RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=5, min_samples_split=2, max_features="sqrt", class_weight="balanced_subsample", bootstrap=True, random_state=42, n_jobs=-1)`
- **Validation croisée :** 3 folds chronologiques internes au train, gap de 24h à chaque frontière de
  fold (mêmes règles anti-fuite que le split principal).
- **Graine :** 42, fixée pour le modèle, le split et l'échantillonnage des folds.

Une étude Optuna bornée (TPE, pruning inter-fold, 15 essais tirés dont 10 menés à leur terme et 5 élagués,
budget 600 s) a été menée en parallèle ; son meilleur essai (`n_estimators=450, max_depth=6,
min_samples_leaf=30, min_samples_split=2, max_features=0.35`) améliore l'AP en validation croisée interne
mais pas sur le test (voir Limitations) — il n'est donc **pas** le modèle décrit par cette fiche.

#### Speeds, Sizes, Times [optional]

Entraînement complet (3 folds de validation croisée + réentraînement final) : **28,0 secondes**, mesuré
sur un poste CPU (AMD Ryzen 5 9600X, 6 cœurs / 12 threads, sans GPU — un RandomForest scikit-learn ne
tire pas parti d'un GPU). Voir aussi Environmental Impact.

## Evaluation

<!-- This section describes the evaluation protocols and provides the results. -->

### Testing Data, Factors & Metrics

#### Testing Data

Rôle `test` du même Gold dataset (20 145 machine-heures, 17,26 % positives, avril-juin 2026 — voir
Training Data). Jamais utilisé pour choisir les hyperparamètres ni le seuil, mais **déjà consulté** lors
de TP antérieurs à des fins pédagogiques (voir Limitations) : ses métriques restent donc indicatives, pas
une garantie de généralisation à une période totalement inédite.

#### Factors

Aucune désagrégation par sous-population dans cette version (les observations sont des états machine, pas
des personnes). Une désagrégation par machine individuelle ou par type de panne
(`type_surchauffe`, `type_vibration`, `type_blocage_mecanique`, ...) serait une amélioration future
pertinente, pour vérifier que la performance ne repose pas sur une seule machine ou un seul type d'incident.

#### Metrics

- **PR-AUC (Average Precision)** : métrique principale, retenue plutôt que l'accuracy car la classe
  positive (panne) est minoritaire (~17 %) — une accuracy élevée pourrait cacher un modèle qui ignore les
  pannes.
- **ROC-AUC** : mesure complémentaire de classement, moins sensible au déséquilibre des classes.
- **Précision, rappel, F2** au seuil retenu : le F2 pondère le rappel plus fort que la précision, cohérent
  avec un coût métier où une panne manquée (faux négatif) coûte plus cher qu'une fausse alerte (faux
  positif). Le seuil est choisi sur la **validation dédiée**, jamais sur le test.

### Results

Seuil retenu (choisi sur validation, maximisant le F2) : **0,3299**.

| Jeu | AP | ROC-AUC | Précision | Rappel | F2 | VP | FP | FN | VN |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Validation | 0,5941 | 0,7597 | 35,85 % | 63,66 % | 0,5511 | 2 167 | 3 878 | 1 237 | 12 503 |
| Test | 0,6151 | 0,7737 | 34,74 % | 67,68 % | 0,5689 | 2 354 | 4 423 | 1 124 | 12 244 |

Pour comparaison, la variante tunée par Optuna (non retenue), évaluée avec son **propre seuil F2**
(0,3249, choisi sur sa propre validation) : validation AP 0,5762/F2 0,5491 ; test AP 0,6026/F2 0,5583 —
inférieure à la baseline sur les deux jeux, alors même que sa procédure de choix de seuil est identique.

#### Summary

Le modèle détecte environ **2 machine-heures positives sur 3** (rappel 68 % sur le test), au prix d'un
grand nombre de fausses alertes : sur 3 alertes déclenchées, une seule en moyenne correspond à une vraie
panne (précision 35 %). C'est un compromis délibéré
(rappel > précision, cf. Recommendations) plutôt qu'un score brillant : conforme à l'avertissement de la
consigne selon lequel les features de ce jeu sont peu déterminantes.

## Model Examination [optional]

<!-- Relevant interpretability work for the model goes here -->

Explications SHAP (`TreeExplainer`, échantillon de 1000 lignes de validation) — top 5 des features par
impact moyen absolu :

| Feature | Impact moyen \|SHAP\| |
| --- | --- |
| `hours_since_last_incident` | 0,0548 |
| `incident_count_prev_24h` | 0,0495 |
| `incident_count_prev_7d` | 0,0244 |
| `temp_mean_24h` | 0,0227 |
| `temp_max_24h` | 0,0164 |

Les deux premières features (historique d'incidents récents) sont **plausibles métier** : une machine
ayant déjà eu un incident récent, ou peu de temps s'étant écoulé depuis, est un candidat raisonnable à une
panne future. Aucune feature ne domine le classement (la n°1 ne pèse que 26,2 % de la somme des dix
impacts les plus forts) : l'impact est **diffus**, cohérent avec l'avertissement de la consigne sur ce jeu
de données. Détail complet, waterfall d'un cas individuel et dependence plots :
[`docs/02-sprint-2/04-revisions/18-explicabilite-shap-treeexplainer.md`](../04-revisions/18-explicabilite-shap-treeexplainer.md).

## Environmental Impact

<!-- Total emissions (in grams of CO2eq) and additional considerations, such as electricity usage, go here. Edit the suggested text below accordingly -->

Carbon emissions can be estimated using the [Machine Learning Impact calculator](https://mlco2.github.io/impact#compute) presented in [Lacoste et al. (2019)](https://arxiv.org/abs/1910.09700).
Mesure directe avec [CodeCarbon](https://codecarbon.io/) (`OfflineEmissionsTracker`,
`indusense.fault.carbon`), sur l'entraînement complet du modèle retenu (3 folds CV + réentraînement final) :

- **Hardware Type:** CPU uniquement — AMD Ryzen 5 9600X (6 cœurs / 12 threads), pas de GPU utilisé
  (RandomForest scikit-learn)
- **Hours used:** 0,0078 h (28,0 secondes)
- **Cloud Provider:** Aucun — poste local
- **Compute Region:** France (mix électrique, `country_iso_code="FRA"`, fortement décarboné grâce au
  nucléaire)
- **Carbon Emitted:** ≈ 0,044 gCO2eq (0,00079 kWh consommé)

À titre de comparaison, l'étude Optuna bornée explorée en parallèle (15 essais, 10 menés à terme) a coûté
0,512 gCO2eq pour un gain de performance qui ne s'est pas confirmé sur le test — un exemple concret de coût
carbone non proportionné au bénéfice (voir
[la fiche CodeCarbon](../04-revisions/17-codecarbon-eco-conception-entrainements-ml.md)).

## Technical Specifications [optional]

### Model Architecture and Objective

Forêt aléatoire (`RandomForestClassifier`, scikit-learn) : ensemble de 300 arbres de décision entraînés
sur des tirages bootstrap du train, avec pondération `balanced_subsample` pour compenser le déséquilibre
des classes. Objectif d'entraînement : maximiser l'Average Precision (PR-AUC) en validation croisée
temporelle sur la classe positive (panne dans les 24h).

### Compute Infrastructure

Poste de développement local, sans infrastructure cloud ni cluster dédié.

#### Hardware

CPU AMD Ryzen 5 9600X (6 cœurs / 12 threads), 31 Go de RAM, Windows 11. Aucun GPU requis ni utilisé.

#### Software

Python 3.14, scikit-learn, pandas, NumPy, Optuna (étude comparative), MLflow (tracking), CodeCarbon
(mesure d'impact), SHAP (explicabilité). Gestion des dépendances via `uv` (`pyproject.toml`, groupe `ml`).

## Citation [optional]

Sans objet — projet pédagogique interne, non publié.

## Glossary [optional]

<!-- If relevant, include terms and calculations in this section that can help readers understand the model or model card. -->

- **Machine-heure** : état d'une machine pendant une heure donnée ; le grain d'une ligne du Gold dataset.
- **PR-AUC (Average Precision)** : aire sous la courbe précision-rappel ; métrique adaptée à une classe
  positive rare, contrairement à l'accuracy.
- **F2-score** : moyenne harmonique pondérée de la précision et du rappel, donnant quatre fois plus de
  poids au rappel qu'à la précision.
- **Gap anti-fuite** : zone d'exclusion temporelle (ici 24h) entre la fin d'un rôle (train, fold) et le
  début du suivant, empêchant qu'un label dépende d'informations encore futures au moment de la prédiction.
- **SHAP** : méthode d'explicabilité attribuant à chaque feature une contribution à une prédiction, par
  rapport à une valeur de base ; mesure une corrélation apprise par le modèle, pas une causalité.

## More Information [optional]

Contexte pédagogique complet, notebooks et fiches de révision associées :
[`docs/02-sprint-2/05-consignes/b7_optimisation_explicabilite.md`](../05-consignes/b7_optimisation_explicabilite.md),
[`docs/02-sprint-2/04-revisions/08-optimisation-hyperparametres-et-validation-croisee.md`](../04-revisions/08-optimisation-hyperparametres-et-validation-croisee.md),
[17](../04-revisions/17-codecarbon-eco-conception-entrainements-ml.md),
[18](../04-revisions/18-explicabilite-shap-treeexplainer.md),
[19](../04-revisions/19-architecture-notebook-src-scripts-industrialisation.md).

## Model Card Authors [optional]

Simon Fuger (formation IT — Indusense), avec l'assistance de Claude Code pour la rédaction.

## Model Card Contact

simon.fuger@alliance4u.fr
