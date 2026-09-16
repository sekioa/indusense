# Classification binaire et découpage temporel

## Définition et objectif

Une **classification binaire supervisée** consiste à apprendre, à partir d'exemples étiquetés, à choisir entre deux classes. Pour Indusense, la cible peut valoir `1` lorsqu'une panne survient dans les 24 heures suivantes et `0` sinon.

La **régression logistique**, malgré son nom, est un modèle de classification : elle estime une probabilité comprise entre 0 et 1, puis un seuil de décision permet de produire une classe.

## Notions essentielles

- Une **feature** est une variable fournie au modèle pour réaliser une prédiction.
- La **cible**, souvent nommée `y`, est la valeur que le modèle doit apprendre à prédire.
- Une **fuite de données** (*data leakage*) se produit lorsqu'une feature révèle une information qui ne serait pas disponible à l'instant réel de la prédiction.
- Le jeu d'**entraînement** sert à ajuster le modèle, le jeu de **validation** à choisir le modèle ou le seuil, et le jeu de **test** à réaliser l'évaluation finale.
- Un **découpage temporel** place les observations anciennes avant les observations récentes. Il reproduit mieux le futur usage du modèle qu'un découpage aléatoire lorsque les données dépendent du temps.

## Démarche pour Indusense

1. Choisir un seul horizon de prédiction, par exemple `label_failure_next_24h`.
2. Identifier l'ancre de prédiction. Dans le Gold Indusense, `window_start` ouvre la fenêtre de features et `window_end` est l'instant où ces features sont disponibles : l'ancre est donc `window_end`.
3. Trier les lignes par machine et par ancre, puis vérifier le découpage `train`, `validation`, `test` déjà fourni.
4. Séparer la cible des features.
5. Exclure des features les autres labels, les comptes d'incidents futurs, les identifiants et les métadonnées de découpage.
6. Ajuster l'imputation, la standardisation et le modèle uniquement sur le jeu d'entraînement.
7. Utiliser la validation pour choisir le seuil de décision, puis conserver le test pour l'évaluation finale.

### Comparer plusieurs classifieurs sans changer le protocole

Pour prolonger la baseline `LogisticRegression`, les deux candidats retenus sont `RandomForestClassifier` et `HistGradientBoostingClassifier`. La régression **linéaire** ne convient pas directement à cette cible binaire : elle prédit une valeur continue qui n'est pas bornée entre 0 et 1. La régression **logistique**, malgré son nom, est le classifieur linéaire déjà utilisé comme baseline ; sa limite est de produire une frontière de décision linéaire sans représenter spontanément les interactions entre capteurs.

La **Random Forest** agrège de nombreux arbres entraînés sur des tirages différents : elle teste des interactions et relations non linéaires tout en réduisant l'instabilité d'un arbre unique. Le **Histogram Gradient Boosting** construit des arbres successifs qui corrigent les erreurs des précédents ; il apporte donc une famille de modèle complémentaire, le *boosting*, adaptée à ce volume de données tabulaires. Ces deux modèles peuvent donc dépasser la limite linéaire de la baseline tout en traitant les mêmes 88 features numériques et la même cible binaire « panne dans les 24 heures ».

Les trois modèles doivent recevoir exactement les mêmes 88 features autorisées et les mêmes partitions temporelles. L'imputation reste apprise sur le train ; le seuil F2 et les hyperparamètres sont comparés sur la validation. La PR-AUC de validation est la métrique principale ; précision, rappel, F2 et matrice de confusion décrivent ensuite les conséquences du seuil retenu. Le jeu de test ne doit être consulté qu'une fois les deux candidats et leurs seuils figés. Si ses résultats ont déjà été lus pendant un TP précédent, il ne constitue plus un test entièrement vierge : il reste utile pour l'exercice, mais une évaluation réellement finale demanderait une période future réservée.

## Pipeline de la baseline

Un **Pipeline** scikit-learn exécute toujours les mêmes transformations dans le même ordre. Celui du TP contient :

1. une imputation par la médiane pour remplacer les valeurs manquantes ;
2. une standardisation pour centrer et réduire les features ;
3. une régression logistique avec `class_weight="balanced"`.

La pondération `balanced` donne davantage de poids aux erreurs sur la classe minoritaire. Sur le train observé, les poids théoriques sont d'environ `0,599` pour la classe 0 et `3,013` pour la classe 1.

L'ensemble du pipeline est ajusté uniquement avec `X_train` et `y_train`. Cette règle empêche les médianes, moyennes et écarts-types de validation ou de test de fuiter dans l'entraînement.

## Lien avec l'optimisation et la régularisation

La **descente de gradient** ajuste les coefficients du modèle afin de réduire une **fonction de coût**, c'est-à-dire une mesure de l'erreur pendant l'entraînement. Le **taux d'apprentissage** définit la taille des ajustements : trop petit, l'entraînement devient lent ; trop grand, la fonction de coût peut osciller ou diverger. C'est un **hyperparamètre**, donc un réglage choisi avant l'entraînement, à la différence des coefficients qui sont appris.

La standardisation du Pipeline met les features sur une échelle comparable. Elle facilite l'optimisation d'un modèle linéaire et rend les coefficients plus comparables. Comme elle apprend une moyenne et un écart-type, elle doit être ajustée uniquement sur le train.

La **régularisation** pénalise les coefficients trop grands afin de limiter le **surapprentissage** (*overfitting*), c'est-à-dire une qualité apparente trop élevée sur le train mais insuffisante sur de nouvelles données. La régression logistique scikit-learn utilise par défaut une pénalité L2, ou Ridge. Son paramètre `C` est l'inverse de la force de régularisation : un `C` plus petit impose une pénalisation plus forte. La valeur de `C` doit être comparée sur la validation, jamais choisie à partir du test.

Le **sous-apprentissage** (*underfitting*) est l'excès inverse : le modèle est trop contraint ou trop simple pour représenter même les données d'entraînement. La séparation train/validation/test permet de rechercher le compromis qui généralise le mieux.

## Métriques et seuil de décision

La **PR-AUC** résume la courbe précision-rappel. Elle est retenue comme métrique principale, car elle examine directement la capacité à retrouver la classe positive quand celle-ci est minoritaire. La référence naïve de la PR-AUC correspond approximativement au taux de positifs.

- La **précision** est la proportion de vraies pannes parmi les alertes émises.
- Le **rappel** est la proportion de pannes réellement détectées.
- Le **score F1** équilibre précision et rappel de façon symétrique.
- Le **score F2** donne davantage d'importance au rappel. Il convient à une première hypothèse où manquer une panne coûte plus cher que déclencher une fausse alerte.
- La **matrice de confusion** compte les vrais négatifs, faux positifs, faux négatifs et vrais positifs.

Le seuil de décision doit être choisi sur la validation, jamais sur le test. Dans ce TP, il maximise le F2. Cette règle technique reste à remplacer par une fonction de coût lorsque le métier aura chiffré le coût des fausses alertes et des pannes manquées.

## Exemple concret observé

Le fichier Gold actuellement disponible contient 134 280 lignes et 15 machines. Il fournit 93 990 lignes d'entraînement, 20 145 de validation et 20 145 de test, dans cet ordre chronologique. Pour `label_failure_next_24h`, le taux de positifs observé est d'environ 16,60 % sur l'entraînement, 17,24 % sur la validation et 17,26 % sur le test.

Après exclusion des identifiants, des timestamps bruts, de la colonne de découpage, des quatre labels futurs et des quatre comptages futurs, 88 features numériques ou booléennes restent disponibles. Des valeurs manquantes subsistent : 185 053 dans la matrice d'entraînement, 37 875 dans la validation et 37 739 dans le test. Elles sont imputées par un prétraitement ajusté uniquement sur l'entraînement.

La régression logistique converge en 121 itérations. Sur la validation, sa PR-AUC atteint `0,586`, contre une référence naïve de `0,172`, soit un résultat environ 3,4 fois supérieur. Le seuil F2 choisi sur cette validation est `0,3416`.

Sur le test resté à l'écart, les résultats observés sont :

| Métrique | Résultat |
| --- | ---: |
| PR-AUC | 0,577 |
| ROC-AUC | 0,762 |
| Précision | 0,303 |
| Rappel | 0,698 |
| F1 | 0,423 |
| F2 | 0,554 |
| Faux positifs | 5 573 |
| Faux négatifs | 1 050 |

Le test contient 3 478 pannes : le modèle en détecte 2 428 et en manque 1 050. Avec les 5 573 faux positifs, il déclenche donc 8 001 alertes au total. La précision de `0,303` signifie qu'environ trois alertes sur dix correspondent à une panne ; près de sept sur dix seraient inutiles si une alerte déclenchait directement une intervention. Cette lecture opérationnelle doit être confrontée au coût d'une panne manquée, au coût d'une inspection et à la capacité des équipes à traiter les alertes.

Le modèle dépasse nettement la référence naïve du test (`0,173`) pour classer les risques. Le seuil choisi privilégie le rappel, mais produit beaucoup de fausses alertes. Le résultat valide la baseline pédagogique sur ce dataset ; il ne démontre ni une causalité des features ni une performance garantie en production.

La pondération `balanced` peut aussi dégrader la calibration : les scores ordonnent les risques et permettent d'appliquer le seuil validé, mais ne doivent pas être annoncés comme des probabilités parfaitement fidèles à la fréquence réelle. Les snapshots horaires voisins utilisent en outre des fenêtres qui se recouvrent ; le découpage temporel évite leur mélange aléatoire entre passé et futur, sans rendre les observations statistiquement indépendantes.

## Erreurs fréquentes et bonnes pratiques

- Ne pas utiliser `train_test_split` avec mélange aléatoire sur cette série temporelle.
- Ne jamais inclure `future_incident_count_*` ou un autre `label_failure_next_*` parmi les features : ces colonnes contiennent de l'information future.
- Ne pas ajuster l'imputation ou la standardisation sur l'ensemble du dataset, car cela ferait apprendre au pipeline des informations issues de validation ou de test.
- Ne pas se limiter à l'accuracy lorsque les classes sont déséquilibrées ; examiner des métriques adaptées et la matrice de confusion.
- Ne pas choisir le seuil sur le test : cela transformerait le test en second jeu de validation.
- Ne pas interpréter un coefficient de régression logistique comme la preuve qu'une feature cause une panne.
- Ne pas présenter automatiquement les scores d'un modèle pondéré comme des probabilités calibrées.

### Complément — revue du TP du 15 septembre 2026

La revue insiste sur une règle opérationnelle simple : à l'**instant T** de la prédiction, une feature doit être réellement disponible. Les agrégats de capteurs ou d'incidents calculés sur le passé sont autorisés ; un `future_incident_count_*` ou un autre `label_failure_next_*` doit être exclu, car il renseigne le futur. Cette exclusion s'applique de la même façon aux matrices `X_train`, `X_validation` et `X_test` ; seule la colonne de label choisie devient `y`.

`fit` signifie apprendre les paramètres d'une transformation. Imputer par la médiane ou standardiser impose donc un `fit` sur le train seulement, suivi d'un `transform` sur validation et test. `class_weight="balanced"` pondère la fonction de coût pendant l'entraînement ; il ne pondère pas les métriques d'évaluation. Enfin, la baseline B5 est une **régression logistique**, pas une régression linéaire : elle réalise bien une classification binaire.

## Points à retenir pour le QCM

- La régression logistique est un classifieur probabiliste.
- Sur des données temporelles, le passé doit servir à prédire le futur.
- Le prétraitement doit être ajusté uniquement sur les données d'entraînement.
- Une colonne calculée à partir du futur est une fuite, même si elle améliore fortement les scores.
- `class_weight="balanced"` compense le déséquilibre pendant l'entraînement ; il ne crée pas de nouvelles observations.
- La PR-AUC est adaptée à l'évaluation d'une classe positive minoritaire.
- Le seuil transforme une probabilité en décision et doit être choisi selon un objectif métier explicite.

## Points à savoir expliquer lors de la soutenance

- Pourquoi le besoin métier correspond à une classification binaire.
- Pourquoi le découpage temporel est préférable à un découpage aléatoire.
- Quelles colonnes ont été exclues pour prévenir les fuites et pourquoi.
- Comment les jeux d'entraînement, de validation et de test ont chacun un rôle différent.
- Pourquoi la PR-AUC est la métrique principale et pourquoi l'accuracy seule serait trompeuse.
- Pourquoi le seuil `0,3416` privilégie le rappel et quelles conséquences opérationnelles ont les faux positifs.
- Pourquoi les coefficients du modèle représentent des associations et non des relations causales.
