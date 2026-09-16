# Comparer trois classifieurs pour la maintenance prédictive

## Définition et objectif

Une **comparaison équitable** de modèles conserve les mêmes observations, les mêmes variables explicatives, la même cible et les mêmes périodes d'entraînement, de validation et de test. Son objectif est de déterminer si un gain de performance justifie le temps de calcul, la complexité et la perte d'interprétabilité d'un modèle plus élaboré.

Dans le TP Indusense, la cible `label_failure_next_24h` est binaire. La baseline est une **régression logistique**, donc un classifieur linéaire, et non une régression linéaire qui prédirait une valeur continue non bornée.

## Protocole validé

- 134 280 observations horaires, 15 machines et 88 features numériques ou booléennes ;
- `train` : 93 990 lignes ; `validation` : 20 145 lignes ; `test` : 20 145 lignes ;
- découpage chronologique, sans mélange aléatoire ;
- imputation apprise uniquement sur le train ;
- pondération des classes pour les trois modèles ;
- hyperparamètres manuels, fixés sans recherche sur le test ;
- seuil F2 choisi séparément pour chaque modèle sur la validation ;
- PR-AUC principale, complétée par ROC-AUC, précision, rappel, F1, F2, faux positifs et faux négatifs.

## Modèles et hyperparamètres

### Régression logistique

`class_weight='balanced'`, `max_iter=2000`, solveur `lbfgs`, après imputation médiane et standardisation. Elle fournit une baseline rapide et directement interprétable par ses coefficients, mais représente difficilement les interactions et relations non linéaires.

### Random Forest

`n_estimators=300`, `max_depth=12`, `min_samples_leaf=5`, `max_features='sqrt'` et `class_weight='balanced_subsample'`. Ces réglages manuels limitent la complexité de chaque arbre, diversifient la forêt et traitent le déséquilibre des classes.

### Histogram Gradient Boosting

`learning_rate=0.08`, `max_iter=200`, `max_leaf_nodes=31`, `min_samples_leaf=20`, `l2_regularization=1.0` et `class_weight='balanced'`. `early_stopping=False` évite la validation interne automatique, qui ne respecterait pas nécessairement l'ordre temporel.

## Résultats sur la validation

### Comment lire les colonnes

- La **PR-AUC train** mesure le classement sur les données utilisées pour apprendre ; la **PR-AUC validation** mesure la généralisation sur la période suivante.
- La **ROC-AUC** estime la capacité à attribuer un score supérieur à une panne plutôt qu'à une non-panne.
- Le **F2** combine précision et rappel en donnant davantage de poids au rappel.
- L'**écart train-validation** aide à repérer le surapprentissage : plus il est grand, plus le modèle perd de performance hors des données apprises.
- Les nombres ne doivent pas être lus isolément : un meilleur classement peut s'accompagner de davantage de pannes manquées au seuil opérationnel.

| Modèle | PR-AUC train | PR-AUC validation | ROC-AUC validation | F2 au seuil choisi | Écart PR-AUC train-validation |
| --- | ---: | ---: | ---: | ---: | ---: |
| Régression logistique | 0,6064 | 0,5863 | 0,7627 | 0,5585 | 0,0202 |
| Random Forest | 0,8239 | **0,5970** | 0,7624 | 0,5513 | 0,2269 |
| Histogram Gradient Boosting | 0,9546 | 0,5924 | 0,7410 | 0,5356 | 0,3622 |

La Random Forest gagne `0,0107` de PR-AUC sur la baseline et ne perd que `0,0072` de F2. Le boosting ne gagne que `0,0061` de PR-AUC, perd `0,0229` de F2 et présente le plus grand écart train-validation. Le choix du modèle est donc effectué sur la validation en faveur de la Random Forest.

## Résultats sur le test

La **précision** est la proportion d'alertes justifiées ; le **rappel** est la proportion de pannes détectées. Les **FP** sont les fausses alertes et les **FN** les pannes manquées. Le temps de fit donne un ordre de grandeur local du coût d'entraînement, pas une garantie de latence en production.

| Modèle | PR-AUC | ROC-AUC | Précision | Rappel | F1 | F2 | FP | FN | Fit indicatif |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Régression logistique | 0,5769 | 0,7616 | 0,3035 | **0,6981** | 0,4230 | 0,5540 | 5 573 | **1 050** | 0,91 s |
| Random Forest | 0,6156 | **0,7755** | **0,3501** | 0,6745 | **0,4610** | **0,5691** | **4 354** | 1 132 | 9,77 s |
| Histogram Gradient Boosting | **0,6157** | 0,7717 | 0,3417 | 0,6622 | 0,4508 | 0,5576 | 4 436 | 1 175 | 10,53 s |

Le temps est une mesure indicative de l'exécution locale. La Random Forest coûte environ 10,7 fois le temps de fit de la baseline dans son notebook individuel ; le boosting environ 11,3 fois. Les deux restent rapides à cette échelle, mais demandent une interprétation indirecte, par exemple une importance par permutation.

## L'écart est-il significatif ?

Un **bootstrap par blocs** rééchantillonne des séquences temporelles plutôt que des lignes isolées afin de préserver une partie de la dépendance entre observations voisines. Les intervalles à 95 % de la différence de PR-AUC sur le test sont :

- Random Forest moins régression logistique : `[+0,0138 ; +0,0608]` ;
- boosting moins régression logistique : `[+0,0133 ; +0,0639]` ;
- Random Forest moins boosting : `[-0,0192 ; +0,0199]`.

Les deux modèles d'arbres dépassent donc la baseline de façon robuste dans ce bootstrap. En revanche, l'écart de `0,0001` entre leurs PR-AUC test n'est pas robuste : l'intervalle contient zéro. Cette estimation ne constitue pas une preuve définitive, car les fenêtres se recouvrent, seules 15 machines sont présentes et le test avait déjà été consulté lors du TP initial.

## Conclusion et recommandation

La **Random Forest est recommandée pour ce TP**. Elle obtient la meilleure PR-AUC sur la validation, améliore sur le test la PR-AUC, F1 et F2 de la baseline, et réduit les faux positifs de 5 573 à 4 354. Elle manque toutefois 82 pannes supplémentaires et reste moins interprétable que la régression logistique.

Le boosting n'est pas retenu avec ces hyperparamètres : sa PR-AUC test est virtuellement identique à celle de la forêt, sans écart robuste, tandis que son F2, son rappel et son écart train-validation sont moins favorables. La régression logistique reste pertinente lorsqu'une explication directe, une mise en œuvre minimale ou le rappel maximal priment sur le gain global de classement.

## Erreurs fréquentes et bonnes pratiques

- Ne pas sélectionner le modèle ou ses hyperparamètres à partir du test.
- Ne pas imposer le même seuil numérique à des modèles dont les scores ont des échelles différentes.
- Ne pas comparer uniquement l'accuracy sur une classe déséquilibrée.
- Ne pas confondre un écart observé avec un écart statistiquement robuste.
- Ne pas interpréter les coefficients ou importances comme des causes physiques.
- Conserver la période, les effectifs, les temps mesurés et les limites avec les métriques.

## Points à retenir pour le QCM

- La validation sert au choix du modèle, des hyperparamètres et du seuil ; le test évalue le choix figé.
- Le bagging de la Random Forest réduit la variance d'un arbre isolé.
- Le boosting ajoute des arbres successifs qui corrigent les erreurs précédentes.
- La PR-AUC est adaptée à l'évaluation du classement de la classe positive minoritaire.
- Une performance légèrement supérieure ne justifie pas automatiquement un modèle plus complexe.

## Points à savoir expliquer lors de la soutenance

- Pourquoi les trois modèles ont reçu les mêmes données et partitions temporelles.
- Comment les hyperparamètres ont été choisis sans utiliser le test.
- Pourquoi chaque modèle possède son propre seuil F2.
- Pourquoi la Random Forest est retenue malgré son coût et sa moindre interprétabilité.
- Pourquoi la PR-AUC presque identique du boosting ne suffit pas à le préférer à la forêt.
- Pourquoi cette conclusion reste pédagogique et doit être revalidée sur une période future vierge.
