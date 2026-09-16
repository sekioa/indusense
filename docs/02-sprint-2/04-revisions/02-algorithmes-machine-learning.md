# Rapport de référence des principaux algorithmes de Machine Learning

## Objectif du rapport

Ce rapport permet, pour chaque grande famille d'algorithmes, de répondre à trois questions :

1. **Comment fonctionne-t-il ?**
2. **À quel type de problème s'applique-t-il ?** Régression, classification, clustering ou autre.
3. **Dans quelle famille d'apprentissage se range-t-il ?** Supervisé ou non supervisé.

Il met également en évidence les algorithmes couramment rencontrés dans les projets de données tabulaires et ceux qui sont pertinents pour le cas d'usage **Indusense : prédire un arrêt machine dans les 6, 12 ou 24 heures**.

### Périmètre retenu

Ce rapport recense le **Machine Learning classique**. Même si le Deep Learning est techniquement un sous-ensemble du Machine Learning, les architectures de réseaux de neurones profonds sont exclues du catalogue afin de respecter le périmètre demandé.

Sont donc hors périmètre : MLP profonds, CNN, RNN, LSTM, TCN, Transformers et autoencodeurs. Ils pourront faire l'objet d'un rapport séparé consacré au Deep Learning. Random Forest, Gradient Boosting, XGBoost, LightGBM et CatBoost restent bien du Machine Learning classique : ils combinent des arbres de décision, pas des couches de neurones.

## Prérequis et vocabulaire

- Une **feature** est une information fournie au modèle, par exemple la température moyenne des six dernières heures.
- La **cible**, ou **label**, est la réponse attendue pendant l'entraînement.
- En **apprentissage supervisé**, chaque exemple d'entraînement possède une cible connue.
- En **apprentissage non supervisé**, les données ne possèdent pas de cible connue ; l'algorithme recherche leur structure ou leurs observations atypiques.
- La **classification** prédit une catégorie, par exemple `arrêt dans les 6 h : oui/non`.
- La **régression** prédit une valeur numérique continue, par exemple le nombre d'heures restant avant une panne.
- Le **clustering** regroupe des observations ressemblantes sans connaître les groupes à l'avance.
- La **détection d'anomalies** attribue un score d'atypisme ou distingue les observations normales des observations inhabituelles.

## Optimiser un modèle : notions du cours Sprint 2, jour 1 après-midi

### Objectif

L'entraînement cherche les valeurs des **paramètres** du modèle, par exemple les poids `W` ou `θ`, qui rendent ses prédictions aussi justes que possible sur les données d'entraînement. Une **fonction de coût** mesure l'erreur globale : plus sa valeur est faible, meilleure est l'adéquation du modèle aux exemples utilisés pour l'entraîner.

### Descente de gradient et taux d'apprentissage

La **descente de gradient** est une méthode d'optimisation : elle modifie progressivement chaque paramètre dans la direction qui diminue la fonction de coût. Son **taux d'apprentissage** (`learning rate`) est la taille de ce pas. C'est un **hyperparamètre**, donc une valeur choisie avant l'entraînement et non une valeur apprise automatiquement comme un poids `W`.

- Taux trop petit : la fonction de coût baisse, mais très lentement ; l'entraînement est inutilement long.
- Taux trop grand : le modèle peut dépasser le minimum, osciller ou diverger ; le coût ne se stabilise pas.
- Démarche : comparer plusieurs valeurs en suivant l'évolution de la fonction de coût, puis retenir une valeur qui descend de façon stable et suffisamment rapide.

Le même taux d'apprentissage s'applique aux paramètres du modèle. Des features dont les échelles sont très différentes rendent alors l'optimisation moins régulière.

### Prétraitement sans fuite de données

La **normalisation** ou la **standardisation** ramène les features sur des échelles comparables. Pour éviter une **fuite de données** — une information du jeu de test qui influence indirectement l'entraînement — les statistiques de transformation, par exemple moyenne et écart-type, sont calculées uniquement sur le jeu d'entraînement. La même transformation est ensuite appliquée au jeu de validation et au jeu de test.

### Sous-apprentissage et surapprentissage

- Le **sous-apprentissage** (*underfitting*) désigne un modèle trop simple ou insuffisamment entraîné : il a des erreurs élevées sur l'entraînement comme sur le test.
- Le **surapprentissage** (*overfitting*) désigne un modèle qui mémorise trop les particularités du jeu d'entraînement : le coût d'entraînement peut être proche de zéro alors que les performances sur de nouvelles données se dégradent.

Un faible coût sur le seul entraînement ne suffit donc jamais à conclure qu'un modèle est bon : les performances doivent être contrôlées sur des données non utilisées pour ajuster les paramètres.

### Points à retenir pour le QCM

- Les poids `W` ou `θ` sont des paramètres appris ; le taux d'apprentissage est un hyperparamètre fixé avant l'entraînement.
- La descente de gradient vise à réduire une fonction de coût.
- Standardiser avant le découpage des jeux crée une fuite de données.
- Underfitting et overfitting sont deux défauts distincts ; la validation sur des données non vues permet de les détecter.

### À savoir expliquer lors de la soutenance

Pour justifier un entraînement, expliquer la métrique ou fonction de coût suivie, les hyperparamètres testés, la séparation entraînement/validation/test et la règle utilisée pour prévenir la fuite de données et le surapprentissage.

## Comment lire le niveau d'usage

Il n'existe pas de classement universel et récent mesurant l'usage de chaque algorithme dans tous les secteurs. L'enquête Kaggle 2022 est trop ancienne pour justifier un classement « actuel » en 2026, et les rapports plus récents identifiés portent principalement sur les outils, l'adoption de l'IA ou l'IA générative plutôt que sur les algorithmes de Machine Learning classique.

Le repère ci-dessous est donc une **synthèse qualitative**, fondée sur la présence des méthodes dans la documentation actuelle de scikit-learn, leur maturité et leur rôle habituel dans un benchmark de données tabulaires. Il indique quels algorithmes il faut connaître et tester couramment ; il ne représente ni une part de marché, ni un nombre d'utilisateurs, ni un classement de performance.

- **★★★ Très courant** : fait partie des premiers modèles généralement testés.
- **★★ Courant** : régulièrement employé, mais plus dépendant du contexte.
- **★ Spécialisé** : pertinent pour un besoin ou un type de données particulier.

La taxonomie suit notamment le guide scikit-learn, qui sépare les modèles supervisés, le clustering, la réduction de dimension et la détection d'anomalies. Les mentions **★★★ Très courant** doivent se lire comme « méthode de référence fréquemment incluse dans les premiers essais », pas comme « trois premières places d'un sondage ».

## Vue d'ensemble

| Algorithme | Catégorie technique | Fonctionnement en une phrase | Problème | Apprentissage | Usage | Indusense |
|---|---|---|---|---|---|---|
| Régression linéaire | Modèle linéaire | Ajuste une combinaison linéaire des features pour minimiser l'erreur sur une valeur continue. | Régression | Supervisé | ★★★ | Utile seulement pour une durée ou une RUL, pas pour le label oui/non actuel. |
| Ridge, Lasso, Elastic Net | Modèle linéaire régularisé | Ajoutent une pénalité aux coefficients d'un modèle linéaire pour limiter le surapprentissage ou sélectionner des variables. | Régression ; classification avec variantes linéaires | Supervisé | ★★★ | Utile pour une baseline régularisée et interprétable. |
| Régression logistique | Modèle linéaire probabiliste | Transforme un score linéaire en probabilité d'appartenir à une classe. | Classification | Supervisé | ★★★ | **Baseline recommandée.** |
| Arbre de décision | Modèle à base d'arbre | Enchaîne des questions sur les features pour séparer progressivement les observations. | Classification, régression | Supervisé | ★★★ | Bon modèle explicatif, mais fragile s'il est utilisé seul. |
| Random Forest | Ensemble d'arbres par bagging | Entraîne de nombreux arbres sur des échantillons et features aléatoires, puis agrège leurs prédictions. | Classification, régression | Supervisé | ★★★ | **Candidat recommandé.** |
| Gradient Boosting | Ensemble d'arbres par boosting | Ajoute des arbres successifs qui corrigent les erreurs de l'ensemble précédent. | Classification, régression | Supervisé | ★★★ | **Candidat recommandé si les labels deviennent suffisants.** |
| XGBoost, LightGBM, CatBoost | Ensembles d'arbres par boosting optimisé | Implémentations optimisées du gradient boosting, avec des stratégies différentes de calcul et de traitement des catégories. | Classification, régression, ranking | Supervisé | ★★★ | À comparer après les baselines ; CatBoost est intéressant pour les catégories métier. |
| k plus proches voisins (k-NN) | Méthode de voisinage | Prédit à partir des observations d'entraînement les plus proches. | Classification, régression | Supervisé | ★★ | Comparaison secondaire ; sensible à l'échelle et au nombre de dimensions. |
| SVM / SVR | Méthode à marge et noyau | Cherche une frontière ou une fonction maximisant une marge, éventuellement dans un espace transformé par un noyau. | Classification, régression | Supervisé | ★★ | Comparaison possible sur un jeu modéré et standardisé. |
| Naive Bayes | Modèle probabiliste bayésien | Combine des probabilités conditionnelles en supposant les features indépendantes sachant la classe. | Classification | Supervisé | ★★ | Peu naturel pour la télémétrie corrélée ; baseline secondaire. |
| K-means | Clustering par centroïdes | Affecte chaque observation au centroïde le plus proche et déplace les centroïdes jusqu'à stabilisation. | Clustering | Non supervisé | ★★★ | Utile pour identifier des régimes de fonctionnement, pas pour prédire directement une panne. |
| Clustering hiérarchique | Clustering hiérarchique | Fusionne progressivement les groupes proches ou divise un groupe global pour former une hiérarchie. | Clustering | Non supervisé | ★★ | Utile pour explorer les familles de machines ou de régimes. |
| DBSCAN / HDBSCAN | Clustering par densité | Regroupe les zones denses et marque les points isolés comme bruit. | Clustering, repérage d'atypiques | Non supervisé | ★★ | Utile en exploration si les régimes ont des formes irrégulières. |
| Mélange gaussien (GMM) | Modèle probabiliste de mélange | Représente les données comme un mélange probabiliste de plusieurs distributions gaussiennes. | Clustering probabiliste, densité | Non supervisé | ★★ | Peut modéliser des régimes avec une probabilité d'appartenance. |
| Isolation Forest | Ensemble d'arbres aléatoires | Isole les observations par des coupures aléatoires ; les points isolés rapidement sont jugés atypiques. | Détection d'anomalies | Non supervisé | ★★★ | **Complément recommandé** pour produire un score d'anomalie. |
| Local Outlier Factor (LOF) | Détection par densité locale | Compare la densité locale d'un point à celle de ses voisins. | Détection d'anomalies ou de nouveauté | Non supervisé | ★★ | Complément possible, mais sensible au voisinage et à l'échelle. |
| One-Class SVM | Méthode à frontière et noyau | Apprend une frontière entourant les données considérées comme normales. | Détection de nouveauté | Non supervisé | ★★ | Possible si l'on dispose d'un historique majoritairement sain et bien standardisé. |
| PCA | Projection linéaire | Projette les features sur des axes orthogonaux conservant le plus de variance possible. | Réduction de dimension, visualisation | Non supervisé | ★★★ | Utile pour explorer les capteurs ; ne prédit pas seule les arrêts. |
| Modèle de survie, par exemple Cox ou Random Survival Forest | Analyse du temps avant événement | Estime la probabilité qu'un événement survienne au fil du temps en tenant compte des observations censurées. | Temps avant événement | Supervisé | ★ | Pertinent si Indusense passe de « panne dans h » à « quand surviendra la panne ? ». |

## Algorithmes supervisés : fonctionnement détaillé

### 1. Régression linéaire

Le modèle calcule une somme pondérée des features : chaque coefficient représente l'effet associé à une variable lorsque les autres restent fixes. L'entraînement choisit les coefficients qui minimisent généralement la somme des erreurs quadratiques.

- **Problème :** régression.
- **Apprentissage :** supervisé.
- **Forces :** rapide, interprétable, excellente baseline.
- **Limites :** représente mal les relations fortement non linéaires sans transformation préalable.
- **Exemple industriel :** estimer une consommation ou une durée restante continue.

### 2. Ridge, Lasso et Elastic Net

Ces modèles conservent le principe linéaire mais pénalisent les coefficients trop élevés. Ridge les réduit ; Lasso peut en ramener certains exactement à zéro ; Elastic Net combine les deux pénalités.

- **Problème :** surtout régression ; des principes de régularisation équivalents existent pour les classifieurs linéaires.
- **Apprentissage :** supervisé.
- **Forces :** limitent le surapprentissage et gèrent mieux des features nombreuses ou corrélées.
- **Limites :** restent essentiellement linéaires.

### 3. Régression logistique

Malgré son nom, c'est un algorithme de **classification**. Il calcule un score linéaire puis applique une fonction logistique, ou sigmoïde, pour obtenir une probabilité comprise entre 0 et 1. Un seuil transforme ensuite cette probabilité en décision.

- **Problème :** classification binaire ou multiclasse.
- **Apprentissage :** supervisé.
- **Forces :** rapide, probabiliste, coefficients interprétables, régularisation disponible.
- **Limites :** frontière de décision linéaire sans création d'interactions ou transformations.
- **Indusense :** première baseline pour `target_stop_6h`, `target_stop_12h` et `target_stop_24h`.

### 4. Arbre de décision

À chaque nœud, l'arbre choisit une feature et un seuil séparant au mieux les exemples. Une nouvelle observation suit les branches jusqu'à une feuille contenant la prédiction.

- **Problème :** classification et régression.
- **Apprentissage :** supervisé.
- **Forces :** règles lisibles, relations non linéaires, peu de préparation numérique.
- **Limites :** un arbre profond mémorise facilement les données et varie fortement si l'échantillon change.

### 5. Random Forest

La forêt aléatoire applique le **bagging** : elle entraîne de nombreux arbres sur des tirages différents des données et sur des sous-ensembles aléatoires de features. Le vote ou la moyenne réduit la variance d'un arbre seul.

- **Problème :** classification et régression.
- **Apprentissage :** supervisé.
- **Forces :** robuste, performant sur données tabulaires, capte interactions et non-linéarités.
- **Limites :** moins lisible qu'un seul arbre ; les probabilités peuvent nécessiter une calibration.
- **Indusense :** candidat solide après la régression logistique.

### 6. Gradient Boosting et variantes

Le **boosting** construit les arbres séquentiellement. Chaque nouvel arbre cherche à réduire les erreurs encore commises par l'ensemble. Contrairement à la Random Forest, les arbres ne sont donc pas indépendants.

- **Problème :** classification et régression.
- **Apprentissage :** supervisé.
- **Forces :** souvent très performant sur données tabulaires hétérogènes.
- **Limites :** réglage plus délicat et risque de surapprentissage sur des événements très rares.

Principales implémentations :

- **HistGradientBoosting** : version scikit-learn utilisant des histogrammes pour accélérer l'entraînement.
- **XGBoost** : système de tree boosting optimisé, régularisé et conçu pour monter en charge.
- **LightGBM** : implémentation efficace sur de grands volumes, avec discrétisation des valeurs et support des catégories.
- **CatBoost** : boosting ordonné et traitement natif des variables catégorielles, utile pour `model`, `production_line`, `criticality` ou `maintenance_type`.

### 7. k-NN

k-NN ne construit pas une équation globale : il conserve les exemples. Pour prédire, il recherche les `k` observations les plus proches et agrège leurs cibles.

- **Problème :** classification et régression.
- **Apprentissage :** supervisé.
- **Forces :** principe simple, relations locales non linéaires.
- **Limites :** prédiction coûteuse, forte sensibilité à l'échelle des features, aux variables inutiles et à la haute dimension.

### 8. SVM et SVR

Le SVM recherche une frontière laissant la marge la plus large possible entre les classes. Un **noyau** peut représenter une séparation non linéaire sans construire explicitement toutes les nouvelles dimensions. SVR applique une idée proche à la régression.

- **Problème :** classification avec SVC ; régression avec SVR.
- **Apprentissage :** supervisé.
- **Forces :** efficace sur des jeux petits ou moyens et des frontières complexes.
- **Limites :** nécessite généralement une standardisation ; devient coûteux sur de grands volumes ; probabilité moins directe.

### 9. Naive Bayes

Le classifieur estime la probabilité de chaque classe à partir des features et applique le théorème de Bayes. Il suppose que les features sont conditionnellement indépendantes sachant la classe.

- **Problème :** classification.
- **Apprentissage :** supervisé.
- **Forces :** très rapide, efficace notamment sur certains textes ou comptages.
- **Limites :** hypothèse d'indépendance peu réaliste pour des capteurs physiques corrélés.

## Algorithmes non supervisés : fonctionnement détaillé

### 10. K-means

K-means choisit `k` centroïdes, affecte chaque observation au centroïde le plus proche, recalcule les centroïdes et répète ces étapes jusqu'à stabilisation.

- **Problème :** clustering.
- **Apprentissage :** non supervisé.
- **Forces :** simple, rapide et facile à interpréter lorsque les groupes sont compacts.
- **Limites :** `k` doit être choisi ; sensible à l'échelle, aux valeurs atypiques et aux groupes non sphériques.
- **Indusense :** peut découvrir des régimes de fonctionnement, mais un cluster ne signifie pas automatiquement « panne ».

### 11. Clustering hiérarchique

L'approche agglomérative commence avec une observation par groupe puis fusionne les groupes les plus proches. Le résultat peut être visualisé sous forme de dendrogramme.

- **Problème :** clustering.
- **Apprentissage :** non supervisé.
- **Forces :** explore plusieurs niveaux de regroupement sans fixer immédiatement un unique découpage.
- **Limites :** dépend fortement de la distance et de la règle de liaison choisies.

### 12. DBSCAN et HDBSCAN

Ces algorithmes repèrent les zones denses. DBSCAN relie les points ayant suffisamment de voisins dans un rayon donné ; HDBSCAN étudie plusieurs niveaux de densité. Les points ne rejoignant aucune zone dense sont marqués comme bruit.

- **Problème :** clustering et repérage d'observations atypiques.
- **Apprentissage :** non supervisé.
- **Forces :** découvre des groupes de forme irrégulière et ne force pas chaque point dans un cluster.
- **Limites :** sensible à l'échelle et aux paramètres de densité ; DBSCAN gère mal des densités très différentes.

### 13. Mélanges gaussiens

Un GMM suppose que les données proviennent d'un mélange de distributions gaussiennes. Il estime leurs paramètres et retourne une probabilité d'appartenance à chaque composante.

- **Problème :** clustering probabiliste et estimation de densité.
- **Apprentissage :** non supervisé.
- **Forces :** groupes souples et appartenance probabiliste.
- **Limites :** dépend de la forme gaussienne supposée et du nombre de composantes.

### 14. Isolation Forest

Isolation Forest crée des arbres utilisant des coupures aléatoires. Une observation très différente des autres est isolée en peu de coupures et reçoit un score d'anomalie élevé.

- **Problème :** détection d'anomalies.
- **Apprentissage :** non supervisé.
- **Forces :** adapté à de nombreuses features, rapide et sans calcul exhaustif de distances.
- **Limites :** le score signale une rareté statistique, pas la cause ni la certitude d'une panne.
- **Indusense :** bon complément pour résumer l'état inhabituel de la télémétrie ; le score peut ensuite devenir une feature du classifieur supervisé.

### 15. Local Outlier Factor

LOF compare la densité locale d'une observation à celle de ses voisins. Un point situé dans une zone nettement moins dense que son voisinage obtient un fort score d'atypisme.

- **Problème :** détection d'anomalies ; détection de nouveauté avec une configuration adaptée.
- **Apprentissage :** non supervisé.
- **Forces :** détecte des anomalies locales que des méthodes globales peuvent manquer.
- **Limites :** sensible à la distance, au nombre de voisins et à la dimension ; le mode de prédiction sur de nouvelles données doit être configuré explicitement.

### 16. One-Class SVM

One-Class SVM apprend une frontière qui englobe la majorité des observations normales dans l'espace des features. Les nouvelles observations placées hors de cette frontière sont considérées comme inhabituelles.

- **Problème :** détection de nouveauté ou d'anomalies.
- **Apprentissage :** non supervisé.
- **Forces :** frontière non linéaire possible grâce aux noyaux.
- **Limites :** standardisation indispensable, réglage sensible et coût important lorsque le volume augmente.

### 17. PCA

L'analyse en composantes principales crée de nouveaux axes, appelés composantes, qui capturent autant que possible la variance des features d'origine.

- **Problème :** réduction de dimension et visualisation.
- **Apprentissage :** non supervisé.
- **Forces :** réduit les variables corrélées et facilite certaines visualisations.
- **Limites :** les composantes sont des combinaisons linéaires moins faciles à expliquer ; une forte variance n'est pas forcément utile pour prévoir une panne.

## Cas particulier : prédire le temps avant panne

Le besoin Indusense actuel demande « un arrêt surviendra-t-il dans les prochaines heures ? ». C'est une classification binaire par horizon. Une autre formulation serait « dans combien de temps surviendra l'arrêt ? » :

- une régression peut estimer une **Remaining Useful Life (RUL)**, ou durée de vie restante ;
- une analyse de survie estime une probabilité d'événement au cours du temps et sait représenter la **censure**, c'est-à-dire le fait que certaines machines n'ont pas encore connu de panne à la fin de l'observation.

Ces formulations demandent un contrat de données et des métriques différents. Elles ne doivent pas être mélangées silencieusement avec les trois labels binaires actuels.

## Recommandation pour Indusense

### État observable des données

Au 14 septembre 2026, les fichiers locaux contiennent :

- 135 626 relevés de télémétrie avec température, pression, tension moyenne, vitesse de rotation et pièces produites ;
- 1 245 incidents ;
- 19 incidents marqués comme arrêts d'urgence ;
- trois horizons prévus : 6 h, 12 h et 24 h ;
- une définition V1 de l'arrêt : `type_arret_urgence = 1`, normalisée en Silver par `is_emergency_stop = true`.

Les labels Gold ne sont pas encore construits ni persistés. Les 19 arrêts sont des événements distincts ; la création de snapshots pourra produire davantage de lignes positives, mais elle ne créera pas davantage de pannes indépendantes. Un découpage aléatoire des snapshots risquerait donc de placer des observations liées au même arrêt dans l'entraînement et le test.

### Modèles à tester dans l'ordre

1. **Baseline métier sans ML** : toujours prédire « pas d'arrêt », puis règle simple fondée sur des seuils de capteurs. Elle donne le niveau minimal à dépasser.
2. **Régression logistique régularisée** : baseline ML interprétable et probabiliste.
3. **Arbre de décision peu profond** : visualiser des règles simples et détecter rapidement des interactions.
4. **Random Forest** : capturer les relations non linéaires avec une robustesse supérieure à l'arbre seul.
5. **Gradient boosting** avec HistGradientBoosting, puis éventuellement XGBoost, LightGBM ou CatBoost : rechercher une meilleure performance lorsque le nombre d'événements et le protocole de validation le permettent.
6. **Isolation Forest** en parallèle : obtenir un score d'anomalie non supervisé, sans le présenter comme une probabilité de panne. Comparer ce score aux événements puis, s'il apporte une information, l'utiliser comme feature supervisée.

### Protocole de comparaison indispensable

1. Construire les features uniquement avec les données connues à l'instant de prédiction `t`.
2. Construire séparément `target_stop_6h`, `target_stop_12h` et `target_stop_24h`.
3. Séparer entraînement, validation et test dans l'ordre chronologique, avec une zone tampon adaptée aux fenêtres et horizons.
4. Empêcher qu'un même événement d'arrêt alimente à la fois l'entraînement et le test.
5. Ajuster imputation, standardisation, encodage et rééquilibrage uniquement sur l'entraînement.
6. Comparer les modèles sur les mêmes partitions et avec le même jeu de features.
7. Mesurer au minimum la précision, le rappel, le score F-bêta choisi avec le métier et l'aire sous la courbe précision-rappel ; ne pas retenir l'accuracy seule.
8. Choisir le seuil d'alerte selon le coût d'une panne manquée et celui d'une fausse alerte.
9. Vérifier la calibration si la sortie doit être présentée comme une probabilité.

### Décision recommandée

Le premier benchmark Indusense devrait comparer :

```text
DummyClassifier
→ LogisticRegression avec class_weight
→ DecisionTreeClassifier peu profond
→ RandomForestClassifier avec class_weight
→ HistGradientBoostingClassifier ou un boosting équivalent
```

Isolation Forest constitue une expérience complémentaire, pas un substitut direct à cette classification supervisée. Aucun algorithme ne peut être déclaré gagnant avant la construction des labels, le découpage temporel et la comparaison sur des métriques métier.

## Erreurs fréquentes

- Choisir un algorithme parce qu'il est populaire sans partir de la cible et des données.
- Confondre régression logistique et régression : la première est un classifieur.
- Confondre clustering, détection d'anomalies et prédiction de panne.
- Interpréter toute anomalie comme une panne certaine.
- Utiliser l'accuracy sur une cible très déséquilibrée : prédire toujours « pas de panne » peut alors sembler excellent.
- Rééquilibrer ou normaliser avant la séparation des jeux, ce qui crée une fuite de données.
- Mélanger aléatoirement une série temporelle ou des fenêtres rattachées au même événement.
- Étendre silencieusement le benchmark au Deep Learning alors que son coût, ses données requises et son protocole d'évaluation demandent un périmètre séparé.
- Lire l'importance d'une feature comme une preuve de causalité.

## Points à retenir pour le QCM

- Régression : valeur numérique continue.
- Classification : catégorie ou probabilité de classe.
- Clustering : groupes inconnus recherchés sans label.
- Régression linéaire et logistique, arbres, forêts, boosting, k-NN et SVM sont supervisés lorsqu'ils apprennent une cible connue.
- K-means, clustering hiérarchique, DBSCAN, PCA, Isolation Forest et LOF sont non supervisés.
- Random Forest utilise surtout le bagging ; Gradient Boosting construit des arbres séquentiellement.
- La régression logistique est un algorithme de classification.
- PCA réduit la dimension mais n'est pas, seule, un modèle de prédiction de panne.

## Points à savoir expliquer lors de la soutenance

- Pourquoi le label Indusense transforme le besoin en classification binaire temporelle.
- Pourquoi la régression logistique constitue une baseline utile.
- La différence entre Random Forest et Gradient Boosting.
- Pourquoi Isolation Forest peut compléter le modèle sans remplacer le label métier.
- Pourquoi 19 événements distincts limitent la complexité raisonnable du premier modèle.
- Pourquoi une séparation chronologique et des métriques adaptées aux classes rares sont nécessaires.
- Pourquoi le choix final dépend d'un compromis entre rappel des pannes, fausses alertes, interprétabilité et coût opérationnel.

## Sources

### Supports et données du projet

- `01_acculturation_IA.pdf`, support Aelion.
- `02_machine_learning.pdf`, support Aelion.
- `todos/03-GOLD-DATASET.md`, contrat cible des prédictions à 6 h, 12 h et 24 h.
- `indusense/datas/telemetry.csv` et `indusense/datas/releves_incidents.csv`, état local contrôlé le 14 septembre 2026.
- `indusense/notebooks/01-sprint-1/02-pipeline-donnees/04-build-data-gold.ipynb`, définition `emergency-stop-v1` et état de construction du Gold.

### Références techniques

- [scikit-learn - User Guide](https://scikit-learn.org/stable/user_guide.html), taxonomie et documentation des modèles supervisés et non supervisés.
- [scikit-learn - Ensembles](https://scikit-learn.org/stable/modules/ensemble.html), arbres boostés, Random Forest et Isolation Forest.
- [scikit-learn - TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html), validation respectant l'ordre temporel.
- [scikit-learn - Metrics and scoring](https://scikit-learn.org/stable/modules/model_evaluation.html), précision, rappel, F-mesure et average precision.
- [Chen et Guestrin - XGBoost: A Scalable Tree Boosting System](https://arxiv.org/abs/1603.02754).
- [Prokhorenkova et al. - CatBoost: unbiased boosting with categorical features](https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html).
- [Liu, Ting et Zhou - Isolation Forest](https://doi.org/10.1109/ICDM.2008.17).
- [NASA - Prognostics and Remaining Useful Life](https://data.nasa.gov/dataset/a-bayesian-framework-for-remaining-useful-life-estimation), exemple de formulation du temps de vie restant.
