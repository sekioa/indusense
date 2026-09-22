# POC ML : choix de baseline, coût métier et plan d'expérience

## Définition et objectif

Un **POC** (*proof of concept*) en Machine Learning vise à démontrer, sur un périmètre limité, qu'un problème métier est solvable par l'apprentissage automatique, avant d'investir dans une solution complète. Cette fiche couvre trois briques d'un POC : le choix d'algorithmes **baseline**, la traduction des métriques en **coût métier**, et la structuration d'un **plan d'expérience** aboutissant à une **note d'arbitrage**.

Objectif à l'issue de la séance : savoir justifier trois algorithmes de départ, relier une matrice de confusion à un coût en euros et en heures, puis documenter une décision de modèle de façon reproductible et défendable à l'oral.

## Notions essentielles

### La règle des 3 baselines

Toujours comparer au minimum trois algorithmes avant de complexifier :

| Critère | Logistic Regression | Random Forest | XGBoost |
|---|---|---|---|
| Complexité | Faible | Moyenne | Haute |
| Interprétabilité | Haute | Moyenne | Faible |
| Performance tabulaire | Moyenne | Bonne | Très bonne |
| Coût calcul | Faible | Moyen | Moyen–haut |
| Robustesse aux outliers | Faible | Bonne | Bonne |
| Gestion du déséquilibre | `class_weight` manuel | `class_weight` | `scale_pos_weight` |

Démarche recommandée par le support : commencer par Random Forest (robuste, peu de réglage), challenger avec XGBoost si le temps de réglage est disponible, garder la régression logistique comme référence interprétable.

**Dans ce dépôt**, XGBoost n'est pas installé et n'a jamais été entraîné : les notebooks 01 à 07 de `notebooks/02-sprint-2/01-maintenance-predictive/` retiennent Logistic Regression, Random Forest et **HistGradientBoosting** (l'équivalent natif scikit-learn du gradient boosting) comme triplet de baselines, avec `class_weight='balanced'` pour gérer le déséquilibre. C'est une substitution assumée et déjà documentée dans ces notebooks, pas un oubli.

### Le piège de l'accuracy et la matrice de confusion

Sur un jeu déséquilibré (ex. 2 % de pannes), un modèle qui prédit toujours « pas de panne » atteint une accuracy élevée sans détecter aucune panne. Se reporter à la matrice de confusion (VP/FN/FP/VN) et aux métriques dérivées — voir la [fiche de référence des métriques](03-metriques-evaluation-modeles-machine-learning.md), qui couvre déjà accuracy, precision, recall, F1, ROC-AUC et PR-AUC en détail.

### Coût métier : FN et FP ne coûtent pas pareil

Traduire chaque type d'erreur en coût opérationnel, avant de choisir une métrique :

- **Faux négatif (panne manquée)** : arrêt non planifié, dommages matériels, pénalités client, coût humain. Ordre de grandeur donné en séance : 5 000 € à 50 000 € par incident.
- **Faux positif (fausse alarme)** : intervention inutile, arrêt préventif injustifié, perte de confiance des équipes si les alarmes se répètent. Ordre de grandeur donné en séance : 200 € à 500 € par fausse alarme.
- Le support en déduit un ratio indicatif : un FN coûterait 10 à 100× plus cher qu'un FP pour de la maintenance prédictive → **maximiser le rappel** reste l'objectif prioritaire, sans faire s'effondrer la précision au point de noyer les équipes sous les fausses alertes.

Ces montants sont des ordres de grandeur pédagogiques du support Aelion, pas des chiffres mesurés sur les données Indusense : à ne pas présenter comme un coût réel sans le faire valider par un expert métier.

### Traduire les métriques pour le Product Owner

Le support propose une correspondance technique → métier, utile pour préparer une restitution :

| Métrique technique | Formulation métier |
|---|---|
| Recall = 85 % | Sur 100 pannes, 85 sont détectées ; 15 passent inaperçues. |
| FN = 30 | 30 pannes manquées sur 200 = 30 arrêts non planifiés potentiels. |
| FP = 48 | 48 fausses alarmes = 48 interventions inutiles. |
| F1 = 0,78 | Score global de fiabilité — acceptable pour un POC. |
| AUC = 0,92 | Le modèle distingue bien les machines saines des malades. |

### Ordres de grandeur d'hyperparamètres évoqués à l'oral

Points précisés en séance, en complément des slides :

- **Random Forest** : nombre d'arbres de l'ordre « des dizaines à quelques centaines » — monter à 500-1000 devient redondant si le dataset n'est pas très volumineux (les arbres se ressemblent). La profondeur maximale ne doit pas non plus être trop élevée : une profondeur de 15, par exemple, peut aboutir à un seul élément par feuille — la profondeur maximale est justement un critère d'arrêt, pas un objectif à maximiser.
- **Méthode en deux passes** : Random Search sur un espace large, suivi d'un Grid Search ou d'un Optuna resserré autour du meilleur point trouvé, pour affiner. Présentée comme une façon de « grappiller » un peu de performance en fin de campagne, pas comme la méthode à utiliser en première intention.
- **Early stopping en boosting** : arrêter l'ajout d'arbres quand la loss sur le jeu de validation cesse de s'améliorer pendant un certain nombre d'itérations consécutives (« patience »), plutôt que de fixer un nombre d'arbres a priori. Le formateur a donné des ordres de grandeur du nombre d'arbres retenus dans ses propres exemples (quelques unités pour un boosting par pondération, un peu plus pour un boosting par erreur résiduelle type XGBoost) : ces chiffres, très bas pour du gradient boosting en usage réel, sont **à vérifier avant de les réutiliser** — seul le principe de l'early stopping (arrêt sur stagnation de la loss de validation) est à retenir avec certitude.

### Plan d'expérience : démarche scientifique

1. **Hypothèse** : formuler une attente vérifiable avant de lancer un entraînement (ex. « XGBoost aura un meilleur rappel que RF sur des données déséquilibrées »).
2. **Expérience** : entraîner les modèles comparés avec les **mêmes** splits et le **même** prétraitement.
3. **Mesure** : recall, F1, precision, temps d'entraînement — définies *a priori*, pas choisies après coup pour valoriser un résultat.
4. **Décision** : choisir un modèle et documenter les raisons et les limites.

L'objectif n'est pas de trouver le modèle parfait, mais de prendre une décision informée et documentée, reproductible par un tiers.

### Note d'arbitrage — structure attendue

Un document (`arbitrage_modele.md`) qui contient au minimum :

- **Contexte** : besoin métier, taille et déséquilibre du dataset.
- **Métrique principale** retenue et son seuil cible (ex. « Recall panne ≥ 0,80 »).
- **Résultats des expériences**, sous forme de tableau comparatif (modèle, métrique principale, métriques secondaires, temps).
- **Modèle retenu** et la métrique qui a motivé le choix.
- **Limites identifiées** : validation sur un seul split, hyperparamètres non optimisés, absence de test de stabilité temporelle, etc.

Précision apportée à l'oral, en réponse à une question d'apprenant : l'arbitrage précision/rappel ne se pose **pas** au métier après coup (« j'ai le choix entre ce modèle et cet autre, vous préférez quoi ? »). C'est au data scientist de connaître et de fixer son arbitrage, à partir d'une discussion *préalable* avec le métier sur le coût des erreurs — pas de faire porter la décision technique sur le Product Owner au moment de la restitution. C'est un point explicite à savoir formuler à l'oral de soutenance.

### Reproductibilité

- Fixer toutes les graines : `random_state` scikit-learn/XGBoost, `np.random.seed`, `random.seed`, `os.environ['PYTHONHASHSEED']`.
- Journaliser les versions de librairies (`sklearn.__version__`, etc.).
- Utiliser le même split train/test pour tous les modèles comparés.
- Versionner le code (commit Git) avant chaque campagne d'entraînement.

## Démarche

1. Poser le problème métier et la classe positive (ex. « panne dans les 24 h »).
2. Choisir trois baselines et les justifier par le tableau de critères.
3. Entraîner les trois modèles sur un split identique, en fixant les graines.
4. Construire la matrice de confusion de chacun et en déduire coût FN/FP estimé.
5. Choisir la métrique principale en fonction du coût métier (recall en priorité pour une panne rare et coûteuse).
6. Remplir le tableau du plan d'expérience *avant* de lancer les entraînements.
7. Rédiger la note d'arbitrage à partir des résultats obtenus.

## Exemple concret

Sur le dataset pédagogique InduSense (10 000 échantillons, 200 pannes soit 2 %) : un modèle Random Forest atteint Recall = 85 %, Precision = 78 %, F1 = 0,78, avec TP = 170, FN = 30, FP = 48, TN = 9 752. Accuracy = 99 %, présentée comme trompeuse car elle masque les 30 pannes manquées. Ce même jeu de résultats est utilisé pour illustrer le tableau technique → métier ci-dessus.

Le TP correspondant à cette approche méthodologique, exécuté sur les données réelles Indusense, se trouve dans `notebooks/02-sprint-2/01-maintenance-predictive/04-maintenance-comparaison-trois-modeles.ipynb` (comparaison LR / RF / HistGradientBoosting) et dans les campagnes MLflow des notebooks 06 et 07 — voir la [fiche MLflow](13-mlflow-tracking-autolog-model-registry.md).

## Erreurs fréquentes et bonnes pratiques

- Choisir la métrique principale *après* avoir vu les résultats, pour justifier le modèle qui arrange — définir la métrique cible avant l'expérience.
- Comparer des modèles entraînés sur des splits différents : rend la comparaison invalide.
- Présenter un F1 ou une accuracy seule sans matrice de confusion ni contexte de déséquilibre.
- Confondre `class_weight` (scikit-learn) et `scale_pos_weight` (XGBoost) : ne sont pas paramétrées de la même façon.
- Oublier de chiffrer, même approximativement, le coût d'un FN et d'un FP avant de choisir un seuil de décision.

## Points à retenir pour le QCM

- La règle des 3 baselines : comparer au minimum trois algorithmes avant de complexifier.
- `scale_pos_weight = nb_négatifs / nb_positifs` pour XGBoost ; `class_weight='balanced'` pour scikit-learn.
- Pour une panne rare et coûteuse, le rappel est généralement priorisé sur la précision.
- Un plan d'expérience se remplit *avant* de lancer les entraînements (hypothèse → expérience → mesure → décision).
- Une note d'arbitrage documente le modèle retenu **et** ses limites, pas seulement son score.

## Points à savoir expliquer lors de la soutenance

- Pourquoi trois baselines plutôt qu'un seul modèle d'emblée.
- Comment un FN et un FP se traduisent concrètement en coût pour Indusense, et pourquoi ce coût oriente le choix de métrique.
- Pourquoi XGBoost n'a pas été retenu dans ce dépôt et ce qui le remplace.
- Ce que garantit — et ne garantit pas — la reproductibilité par graines fixées.
- Les limites explicitement assumées dans la note d'arbitrage du POC Indusense.
- Pourquoi l'arbitrage précision/rappel doit être fixé par le data scientist en amont, et non demandé au métier au moment de présenter les résultats.

## Sources du cours

- `07_poc_ml.pdf`, support Aelion « POC ML & métriques métier » (Séance 11), diapositives 1 à 26.
- [Transcription de la séance](../02-transcriptions/07-jour-3-poc-ml-metriques-roc-pr-auc.txt) et de sa [suite](../02-transcriptions/08-jour-3-revue-tp-transition-deep-learning.txt).

## Pour aller plus loin

- [scikit-learn — class_weight](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html)
- [XGBoost — Parameters](https://xgboost.readthedocs.io/en/stable/parameter.html)
