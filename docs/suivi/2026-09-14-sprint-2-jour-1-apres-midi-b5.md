# Sprint 2 - Jour 1 après-midi : suite pratique B5

## Objectif concret

Cette séance relie les notions abordées dans le cours de l'après-midi au TP B5 Indusense : transformer des relevés de capteurs en une première alerte « panne dans les 24 heures ? ». À la fin, l'utilisateur sait expliquer le rôle du prétraitement, de la régression logistique, du découpage temporel, de la régularisation et du seuil de décision.

Le travail pratique correspondant est déjà présent dans `maintenance-ml-regression.ipynb`. Cette fiche décrit son déroulement et la lecture des résultats sans modifier le notebook exécuté.

## Point de départ vérifié

- Le support B5 demande une classification binaire supervisée, pas une régression de valeur continue.
- Le support cite `data/raw/indusense_gold.parquet`, mais le fichier Gold réellement présent et utilisé par le notebook est `datas/gold_dataset_20260622-080603.csv`.
- Le notebook contient 134 280 lignes, 15 machines et un découpage déjà fourni : `train`, `validation`, puis `test`.
- La transcription du cours est disponible dans [`../../../transcriptions/sprint-2-jour-1-cours-apres-midi.txt`](../../../transcriptions/sprint-2-jour-1-cours-apres-midi.txt). Les notions mobilisées sont notamment la descente de gradient, la normalisation, le sous-apprentissage, le surapprentissage et la régularisation.

## 1. Situer le problème métier

Une **classification binaire supervisée** apprend une décision entre deux classes à partir d'exemples dont la réponse est déjà connue. Ici, la cible `label_failure_next_24h` vaut `1` lorsqu'une panne est observée dans les 24 heures suivant l'instant de prédiction, et `0` sinon.

La **régression logistique** est malgré son nom un classifieur : elle retourne un score entre 0 et 1. Ce score ne devient une alerte qu'après l'application d'un seuil.

Dans JupyterLab, ouvrir `maintenance-ml-regression.ipynb`, puis exécuter les cellules dans l'ordre avec `Shift + Entrée`. La première cellule doit confirmer le fichier chargé, 134 280 lignes, 15 machines et l'absence de doublon sur `machine_id_std` et l'ancre temporelle.

## 2. Prévenir la fuite de données avant l'entraînement

Une **fuite de données** est une information qui serait inconnue au moment réel de la prédiction mais qui se retrouve, par erreur, dans les features. Elle produit souvent une évaluation artificiellement élevée.

Le notebook exclut :

- les identifiants et horodatages bruts ;
- `split_set`, qui indique à quel jeu appartient une ligne ;
- les quatre labels `label_failure_next_*` ;
- les quatre comptes `future_incident_count_*`, car ils décrivent le futur.

Le résultat attendu est de 88 features. Le split n'est pas mélangé : le train s'arrête le 17 février 2026 à 02:00, la validation couvre la période suivante, puis le test commence le 14 avril 2026 à 02:00. Ainsi, le passé sert réellement à prédire le futur.

## 3. Relier la standardisation à la descente de gradient

La **fonction de coût** mesure l'erreur à réduire pendant l'entraînement. La **descente de gradient** ajuste progressivement les paramètres du modèle pour diminuer cette erreur. Son **taux d'apprentissage** détermine la taille de chaque ajustement : trop petit, l'entraînement est lent ; trop grand, l'optimisation peut osciller ou diverger.

La **standardisation** met les features numériques sur une échelle comparable. Elle est importante pour une régression logistique : sans elle, une variable exprimée avec de grandes valeurs peut dominer les calculs et ralentir l'optimisation.

Le `Pipeline` du notebook applique, dans cet ordre :

1. `SimpleImputer(strategy="median")` pour remplacer les valeurs manquantes ;
2. `StandardScaler()` pour standardiser les features ;
3. `LogisticRegression(class_weight="balanced")` pour entraîner la baseline.

Point crucial : le `fit` du Pipeline est effectué seulement sur le train. Les médianes, moyennes et écarts-types du test ne doivent jamais influencer ces étapes.

## 4. Traiter le déséquilibre sans se laisser tromper par l'accuracy

Une classe est **déséquilibrée** lorsque l'une de ses valeurs est beaucoup moins fréquente que l'autre. Dans le train B5, les pannes représentent 16,60 % des lignes. Une règle qui répond toujours « pas de panne » obtiendrait donc 83,40 % d'accuracy, mais 0 % de rappel sur les pannes.

`class_weight="balanced"` augmente le poids des erreurs sur la classe minoritaire pendant l'entraînement. Ce paramètre ne crée pas de nouvelles données ; il rend l'objectif d'optimisation plus attentif aux pannes.

La mesure principale est la **PR-AUC** : elle résume le compromis entre précision et rappel pour une classe positive rare. La référence naïve est proche du taux de panne ; une PR-AUC supérieure indique que le modèle classe utilement les risques.

## 5. Vérifier la généralisation plutôt que mémoriser le train

Le **sous-apprentissage** (*underfitting*) correspond à un modèle trop simple qui échoue même sur les données d'entraînement. Le **surapprentissage** (*overfitting*) correspond à un modèle qui mémorise trop le train et perd en qualité sur des données futures.

La régularisation limite l'amplitude des coefficients pour réduire ce risque. Dans scikit-learn, la régression logistique utilise par défaut une régularisation L2, aussi appelée Ridge. Son intensité est contrôlée par l'hyperparamètre `C` : un `C` plus petit signifie une pénalisation plus forte.

Le notebook ne choisit ni les hyperparamètres ni le seuil sur le test : il entraîne sur le train, décide sur la validation, puis consulte le test une seule fois. Cette séparation est la preuve pratique recherchée contre le surapprentissage de décision.

## 6. Lire les résultats du TP B5

Les résultats déjà exécutés sont les suivants :

| Étape | Observation |
| --- | --- |
| Entraînement | Convergence de la régression logistique en 121 itérations |
| Validation | PR-AUC `0,586`, contre une référence naïve `0,172` |
| Décision | Seuil choisi sur la validation : `0,3416`, en maximisant F2 |
| Test final | PR-AUC `0,577`, ROC-AUC `0,762` |
| Alertes au seuil retenu | précision `0,303`, rappel `0,698`, F2 `0,554` |

Le score F2 donne davantage d'importance au **rappel**, donc au fait de ne pas manquer une panne. Son coût est visible : 5 573 faux positifs pour 1 050 faux négatifs sur le test. Le bon seuil reste une décision métier : il faut comparer le coût d'une intervention inutile avec celui d'une panne non détectée.

Les coefficients, par exemple l'association positive de `temp_mean_12h`, ne démontrent pas une causalité. Ils montrent seulement quelles variables contribuent au score dans cette baseline et avec ce dataset.

## À savoir expliquer à l'oral

1. Le besoin est une classification binaire par horizon, et non une régression de durée.
2. Le pipeline est ajusté uniquement sur le train pour empêcher la fuite de données.
3. La standardisation facilite l'optimisation et rend les coefficients comparables après transformation.
4. Le split temporel simule un modèle qui prédit sur une période future.
5. La PR-AUC, le rappel et la matrice de confusion sont plus utiles que l'accuracy seule avec des pannes rares.
6. La validation choisit le seuil ; le test sert seulement à l'évaluation finale.

## Validation et suite

Validé : le notebook exécute le flux B5 de bout en bout et ses sorties correspondent aux résultats indiqués ici. À valider avec le métier : le coût relatif des faux positifs et faux négatifs, donc la règle définitive de sélection du seuil.

Erreur fréquente : appeler le notebook « régression » au sens d'une valeur continue. Il utilise une régression logistique, qui est bien un classifieur binaire.
