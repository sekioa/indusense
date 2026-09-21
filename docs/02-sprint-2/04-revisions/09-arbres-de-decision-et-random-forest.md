# Arbres de décision et Random Forest

## Définition et objectif

Un **arbre de décision** est un modèle supervisé qui enchaîne des questions binaires sur les features. Chaque question forme un **nœud**, chaque réponse suit une **branche** et une **feuille** contient la prédiction finale. Il peut servir à la classification, pour prédire une classe, ou à la régression, pour prédire une valeur numérique.

Une **Random Forest**, ou forêt aléatoire, agrège plusieurs arbres afin de produire une prédiction plus stable qu'un arbre isolé.

## Notions essentielles

- Un **split** est la séparation des observations selon une feature et un seuil.
- En classification, l'**impureté** mesure le mélange des classes dans un nœud. L'indice de Gini standard vaut `1 - Σ pᵢ²`, soit `Σ pᵢ(1 - pᵢ)` ; il vaut zéro lorsqu'un nœud ne contient qu'une seule classe.
- L'**entropie** est un autre critère d'impureté disponible pour construire l'arbre.
- L'algorithme compare des splits candidats et retient celui qui réduit le mieux l'impureté pondérée des nœuds enfants.
- En classification, une feuille prédit généralement la classe majoritaire ou des probabilités calculées à partir des proportions observées.
- En régression, une feuille prédit généralement la moyenne des valeurs cibles qu'elle contient.

## Construction et critères d'arrêt

Sans contrainte, un arbre peut se développer jusqu'à mémoriser presque parfaitement les données d'entraînement. Les principaux hyperparamètres de régularisation sont notamment :

- `max_depth` : profondeur maximale de l'arbre ;
- `min_samples_split` : nombre minimal d'observations pour diviser un nœud ;
- `min_samples_leaf` : nombre minimal d'observations dans une feuille ;
- `max_leaf_nodes` : nombre maximal de feuilles ;
- `ccp_alpha` : intensité de l'élagage par complexité de coût.

Un arbre trop profond risque le **surapprentissage** : il mémorise les particularités du train et généralise mal. Un arbre trop contraint risque le **sous-apprentissage** : il ne représente pas suffisamment les relations utiles.

## De l'arbre à la Random Forest

La Random Forest utilise le **bagging**, c'est-à-dire l'entraînement de plusieurs modèles sur des sous-échantillons différents du jeu d'entraînement. Elle introduit aussi de l'aléatoire dans les features proposées à chaque split. Cette diversité réduit la corrélation entre les arbres et diminue la variance de l'ensemble.

- En classification, les arbres contribuent à un vote ou à une moyenne de probabilités.
- En régression, leurs prédictions numériques sont moyennées.
- `n_estimators` contrôle le nombre d'arbres ; davantage d'arbres stabilise généralement le résultat mais augmente le coût de calcul.
- `max_features` contrôle le nombre de features candidates à chaque split.
- `bootstrap` indique si les arbres sont entraînés sur des tirages avec remise.

## Exemple Indusense

Pour prédire `target_stop_12h`, un arbre peut d'abord séparer les observations selon un seuil de température, puis selon la vibration ou la pression. Une Random Forest construit de nombreuses variantes de ces arbres sur des échantillons et sous-ensembles de features différents, puis agrège leurs prédictions.

La qualité doit être évaluée sur une période future non utilisée pour l'entraînement. Un score presque parfait sur le train ne prouve pas que le modèle fonctionnera en production.

## Erreurs fréquentes et bonnes pratiques

- **Laisser l'arbre croître sans limite :** contrôler notamment profondeur et taille minimale des feuilles.
- **Optimiser sur le test :** réserver le test à l'évaluation finale et régler les hyperparamètres par validation adaptée.
- **Croire que la standardisation est obligatoire :** les splits des arbres reposent sur des seuils et ne nécessitent généralement pas de mise à l'échelle.
- **Fournir directement des chaînes de caractères à scikit-learn :** les arbres scikit-learn classiques exigent des valeurs numériques ; les catégories doivent être encodées dans le pipeline.
- **Interpréter l'importance des features comme une causalité :** une importance élevée indique une utilité prédictive dans ce modèle, pas une cause métier démontrée.
- **Oublier les fuites temporelles :** supprimer les informations futures et conserver une validation du passé vers le futur pour Indusense.

## Points à retenir pour le QCM

- Un arbre de décision est un modèle supervisé utilisable en classification et en régression.
- Une feuille contient la prédiction ; un nœud interne contient une règle de séparation.
- L'indice de Gini mesure l'impureté d'un nœud de classification.
- Une Random Forest combine plusieurs arbres par bagging et sous-échantillonnage de features.
- Limiter la profondeur ou imposer une taille minimale aux feuilles réduit le risque de surapprentissage.
- Les arbres ne nécessitent généralement pas de standardisation, mais les catégories textuelles doivent être encodées avec scikit-learn.

## Points à savoir expliquer lors de la soutenance

- Comment un split est choisi et comment une observation traverse l'arbre jusqu'à une feuille.
- Pourquoi un arbre profond peut surapprendre et quels hyperparamètres limitent sa complexité.
- Pourquoi la diversité des arbres améliore la stabilité d'une Random Forest.
- Comment la forêt agrège les prédictions en classification et en régression.
- Pourquoi les performances doivent être mesurées sur des données temporellement futures pour le cas Indusense.

## Source du cours

- [Transcription du cours Arbres de décision](../02-transcriptions/05-arbres-de-decision.txt)
- [Support Aelion - Arbres de décision](../01-cours/04_Arbres_de_decisions_AELION.pdf)
- [Support Aelion - Random Forests](../01-cours/05_Random_Forests_AELION.pdf)

Correspondance exacte avec le référentiel C1 à C9 : à confirmer avec le Kit candidat local.
