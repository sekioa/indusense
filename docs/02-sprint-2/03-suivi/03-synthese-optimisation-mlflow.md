# Optimisation Indusense - synthèse pédagogique

## Question traitée

Peut-on améliorer méthodiquement la Random Forest retenue dans les notebooks précédents en optimisant ses hyperparamètres, sans utiliser le jeu de test pour faire les choix ? Un **hyperparamètre** est un réglage fixé avant l'apprentissage, par exemple la profondeur maximale des arbres.

L'unité observée est la **machine-heure** : l'état d'une machine pendant une heure. La cible vaut 1 lorsqu'une panne surviendra dans les 24 heures suivantes. Une même panne peut donc rendre positives plusieurs heures consécutives ; 3 478 lignes positives ne représentent pas 3 478 pannes distinctes.

## Méthode retenue et justification

La famille de modèles Random Forest était déjà sélectionnée, mais les arbres précédemment entraînés ne sont pas réutilisés : chaque configuration et chaque fold entraînent une nouvelle forêt depuis zéro.

La méthode choisie est un **Random Search** de 16 configurations tirées, avec une graine 42, parmi 64 combinaisons possibles. Ce choix fixe un budget de calcul tout en explorant les quatre réglages importants. Un Grid Search aurait entraîné les 64 combinaisons ; Optuna aurait adapté les essais selon leurs résultats précédents, mais aurait ajouté une logique disproportionnée pour ce petit espace discret. Le Random Search peut cependant manquer la meilleure combinaison.

Espace de recherche :

| Hyperparamètre | Valeurs | Effet recherché et risque |
|---|---|---|
| `n_estimators` | 150, 300 | Plus d'arbres stabilise parfois le score, mais augmente le temps et la taille du modèle. |
| `max_depth` | 6, 8, 12, 16 | Une grande profondeur apprend des règles fines, avec davantage de risque de surapprentissage. |
| `min_samples_leaf` | 2, 5, 10, 20 | Une feuille plus grande lisse les décisions et limite les règles trop spécifiques. |
| `max_features` | `sqrt`, 0,25 | Nombre de variables candidates à chaque séparation : 9 sur 88 avec `sqrt`, 22 avec 0,25. |

## Protocole sans fuite temporelle

1. La recherche utilise uniquement le train, découpé en trois folds chronologiques expansifs.
2. Les 15 machines d'un même timestamp restent ensemble et un gap de 24 heures sépare apprentissage et validation. Une purge de 360 lignes protège aussi les frontières train/validation/test puisque la cible regarde 24 heures dans le futur.
3. L'imputation médiane est apprise dans chaque fold, uniquement sur sa partie d'entraînement.
4. La configuration gagnante maximise l'**Average Precision (AP)** moyenne. L'AP évalue le classement précision-rappel de la classe positive ; une AP de 0,60 ne signifie pas 60 % de prédictions correctes.
5. Un seuil d'alerte est ensuite choisi sur la validation dédiée en maximisant le score F2, qui favorise le rappel. Le test n'est consulté qu'après le gel du modèle et du seuil.

La recherche représente 16 configurations × 3 folds = 48 entraînements. Avec la référence, les analyses de sensibilité et les réentraînements complets, la campagne atteint 23 configurations distinctes et 92 fits en 21,9 minutes. Un **fit** est un apprentissage complet d'un modèle.

## Résultats avant/après

La référence manuelle utilise 300 arbres, une profondeur de 12, 5 lignes minimum par feuille et `sqrt`. Le Random Search retient 150 arbres, une profondeur de 6, 10 lignes minimum par feuille et 25 % des variables.

| Indicateur | Référence | Modèle optimisé | Lecture |
|---|---:|---:|---|
| AP moyenne en validation croisée | 0,5575 | 0,5652 | Gain interne de +0,0077, utilisé pour sélectionner le gagnant. |
| Dispersion AP entre folds | 0,0552 | 0,0545 | Variabilité proche ; ce n'est pas un intervalle de confiance. |
| Écart AP train - validation croisée | 0,3563 | 0,1635 | Le risque de surapprentissage diminue, sans prouver la généralisation. |
| AP sur le test | 0,6151 | 0,5971 | Baisse de -0,0180 : le gain interne ne se confirme pas. |
| Précision sur le test | 34,74 % | 34,36 % | Une proportion légèrement plus faible des alertes est correcte. |
| Rappel sur le test | 67,68 % | 67,71 % | Une machine-heure positive supplémentaire est détectée. |
| F2 sur le test | 0,5689 | 0,5670 | L'équilibre orienté rappel se dégrade légèrement. |

Matrices de confusion sur 20 145 machine-heures de test, dont 3 478 positives :

| Modèle | Vrais négatifs | Faux positifs | Faux négatifs | Vrais positifs |
|---|---:|---:|---:|---:|
| Référence | 12 244 | 4 423 | 1 124 | 2 354 |
| Optimisé | 12 168 | 4 499 | 1 123 | 2 355 |

Le changement produit donc **76 fausses alertes supplémentaires pour une seule machine-heure positive supplémentaire détectée**. Cela ne signifie pas qu'une panne distincte supplémentaire a été détectée.

## Influence, décision et limites

La sensibilité locale identifie `max_depth` comme le réglage le plus influent dans les valeurs testées, avec une amplitude de 0,0103 point d'AP. Cette analyse fait varier un seul réglage autour du gagnant : elle ne couvre pas toutes les interactions et ne mesure pas l'importance des variables d'entrée.

**Décision : ne pas remplacer la référence sur la base de ce test.** Le modèle optimisé généralise moins bien selon l'AP test et augmente fortement les fausses alertes pour un bénéfice marginal. La baisse de l'écart train-CV est rassurante, mais ne démontre pas l'absence de surapprentissage. De plus, ce test avait déjà été consulté dans les exercices antérieurs : il faut confirmer sur une période future jamais utilisée, puis mesurer aussi la détection par panne distincte et la répétition des alertes.

MLflow conserve automatiquement les hyperparamètres, scores des folds, durées, modèles, versions logicielles et empreinte du CSV. Cela rend les essais comparables et reproductibles, mais ne garantit ni la qualité du protocole ni la performance du modèle. L'énergie et le CO2 n'ont pas été mesurés. Référence pédagogique : `09_Optimisation.pdf`, pages 4 à 10.
