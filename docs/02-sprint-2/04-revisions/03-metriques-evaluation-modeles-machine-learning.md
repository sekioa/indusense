# Rapport de référence — métriques d'évaluation des modèles de Machine Learning

## Objectif et point de départ

Ce rapport permet de choisir et de défendre une métrique d'évaluation. Pour chaque métrique, il indique **son calcul et sa signification concrète**, le **type de problème** concerné et les situations où il faut la privilégier ou s'en méfier.

**Prérequis.** Un modèle a produit des prédictions sur un jeu de validation ou de test qui n'a pas servi à l'entraîner. Une métrique ne rend pas un modèle fiable par elle-même : elle mesure sa qualité sur ce jeu précis et doit être reliée au risque métier.

## Avant de choisir : les règles communes

- La **vérité terrain** est la valeur réellement observée, notée `y` ; la **prédiction** du modèle est notée `ŷ`.
- Le jeu de **validation** sert à choisir les réglages, le modèle et, en classification, le seuil d'alerte. Le jeu de **test** est réservé à l'évaluation finale, une fois ces choix figés.
- Une **métrique** est une mesure chiffrée ; une **fonction de perte** (*loss*) est la quantité que l'algorithme cherche souvent à minimiser pendant l'entraînement. Elles peuvent être identiques, mais ce n'est pas obligatoire.
- Comparer les modèles sur les mêmes observations, le même horizon temporel et la même définition de la cible. Une meilleure valeur ne prouve rien si le protocole a changé.
- Accompagner un score d'un effectif, d'une période et, si possible, d'un intervalle d'incertitude : 100 % de rappel sur deux pannes ne garantit pas une performance stable.

## Classification : partir de la matrice de confusion

Une **classification binaire** décide entre une classe positive (événement recherché) et une classe négative. Après application d'un seuil, chaque prédiction entre dans une cellule de la matrice suivante.

| Réalité / prédiction | Positive | Négative |
|---|---:|---:|
| Positive | vrai positif (**VP**) : événement détecté | faux négatif (**FN**) : événement manqué |
| Négative | faux positif (**FP**) : fausse alerte | vrai négatif (**VN**) : absence correctement reconnue |

Exemple Indusense : « panne dans les 24 h » est la classe positive. Un FN est donc une panne imminente non signalée ; un FP déclenche une inspection ou une maintenance inutile.

### Accuracy (exactitude globale)

- **Calcul et mesure :** `(VP + VN) / (VP + VN + FP + FN)`. C'est la proportion de décisions correctes, toutes classes confondues.
- **Type :** classification binaire ou multiclasse.
- **À privilégier :** classes relativement équilibrées et coûts des erreurs comparables.
- **S'en méfier :** avec une classe rare. Si 99 % des équipements ne tombent pas en panne, prédire systématiquement « pas de panne » obtient 99 % d'accuracy mais ne détecte aucune panne. Elle ne dit pas non plus quel type d'erreur est commis.

### Précision (*precision*, valeur prédictive positive)

- **Calcul et mesure :** `VP / (VP + FP)`. Parmi les alertes émises, c'est la part qui est réellement positive.
- **Type :** classification binaire ; en multiclasse, elle se calcule par classe puis s'agrège.
- **À privilégier :** lorsqu'une action déclenchée par une alerte est coûteuse, limitée en capacité ou intrusive : inspection terrain, contrôle manuel, blocage de transaction.
- **S'en méfier :** un modèle peut avoir une précision de 100 % en ne levant qu'une seule alerte et en manquant presque tous les vrais cas. Toujours la lire avec le rappel et le nombre d'alertes.

### Rappel (*recall*, sensibilité, taux de vrais positifs)

- **Calcul et mesure :** `VP / (VP + FN)`. Parmi tous les positifs réels, c'est la part détectée par le modèle.
- **Type :** classification binaire ; calcul par classe en multiclasse.
- **À privilégier :** lorsqu'il est grave de manquer un événement : dépistage, fraude majeure, risque sécurité, panne coûteuse. Pour Indusense, il mesure la part des pannes imminentes repérées.
- **S'en méfier :** prédire « positif » pour tout le monde donne un rappel de 100 %, tout en créant potentiellement trop de fausses alertes. L'interpréter avec la précision ou un coût métier.

### Spécificité et taux de faux positifs

- **Calcul et mesure :** la **spécificité** est `VN / (VN + FP)` : parmi les négatifs réels, la part correctement écartée. Le **taux de faux positifs** (*FPR*) est `FP / (FP + VN) = 1 - spécificité`.
- **Type :** classification binaire.
- **À privilégier :** pour vérifier que le système n'alerte pas abusivement ou lorsqu'écarter correctement les non-cas est essentiel.
- **S'en méfier :** avec une majorité écrasante de négatifs, une spécificité élevée peut coexister avec une précision faible et un rappel médiocre. Ce n'est pas une mesure de détection des cas positifs.

### F1 et F-bêta

- **Calcul et mesure :** `F1 = 2 × précision × rappel / (précision + rappel)` ; c'est leur moyenne harmonique, qui devient faible si l'une des deux valeurs est faible. `Fβ` pondère le compromis : `β > 1` favorise le rappel ; `β < 1` favorise la précision.
- **Type :** classification binaire ou multiclasse.
- **À privilégier :** F1 si précision et rappel sont aussi importants ; F2 si manquer un positif coûte davantage ; F0,5 si une fausse alerte coûte davantage. Pour Indusense, F2 peut être étudié si une panne manquée est nettement plus coûteuse qu'une inspection inutile.
- **S'en méfier :** F1 ne tient pas compte des vrais négatifs, cache le détail précision/rappel et impose une pondération implicite. Le choix de `β` doit être justifié par le métier, pas choisi pour maximiser un score a posteriori.

### Balanced accuracy

- **Calcul et mesure :** moyenne du rappel de chaque classe. En binaire : `(rappel + spécificité) / 2`.
- **Type :** classification binaire ou multiclasse déséquilibrée.
- **À privilégier :** première vue globale lorsque les classes ne sont pas équilibrées et que chaque classe doit compter de façon comparable.
- **S'en méfier :** elle suppose que les classes ont la même importance. Elle ne remplace pas le suivi de la précision si les faux positifs ont un coût opérationnel.

### MCC (*Matthews Correlation Coefficient*)

- **Calcul et mesure :** `(VP×VN − FP×FN) / √((VP+FP)(VP+FN)(VN+FP)(VN+FN))`. Il résume la corrélation entre prédictions et réalité, de `−1` (inverse parfait) à `1` (parfait), `0` correspondant environ au hasard.
- **Type :** classification binaire ; extension multiclasse disponible.
- **À privilégier :** comparaison synthétique de classifieurs avec classes déséquilibrées, car les quatre cellules de la matrice sont prises en compte.
- **S'en méfier :** moins intuitif pour un public métier qu'une précision ou un rappel ; il ne dit pas explicitement si l'erreur dominante est un FP ou un FN.

### ROC-AUC

- **Calcul et mesure :** la courbe **ROC** trace le rappel contre le FPR pour tous les seuils. Son aire, l'**AUC**, est aussi la probabilité qu'un positif reçoive un score supérieur à un négatif choisi au hasard. `1` est idéal, `0,5` correspond approximativement au hasard.
- **Type :** classification binaire produisant un score ou une probabilité ; extensions multiclasse possibles.
- **À privilégier :** comparer la capacité de classement de modèles avant le choix du seuil, surtout si les classes ne sont pas extrêmement rares.
- **S'en méfier :** elle ne choisit aucun seuil, ne garantit pas la calibration des probabilités et peut paraître excellente quand les négatifs sont très nombreux : un faible FPR peut encore représenter beaucoup de fausses alertes. Dans ce cas, compléter par PR-AUC et des résultats au seuil métier.

### PR-AUC et Average Precision

- **Calcul et mesure :** la courbe **précision-rappel** trace précision contre rappel pour les seuils. La **PR-AUC** en résume l'aire ; l'**Average Precision** (AP) est l'agrégation usuelle en paliers de précision selon le rappel. Une référence utile est la prévalence, c'est-à-dire la proportion de positifs : une AP proche de cette proportion n'apporte guère plus qu'un classement aléatoire.
- **Type :** classification binaire avec score ; évaluation par classe possible en multiclasse.
- **À privilégier :** événement positif rare et réellement important : pannes, fraude, maladie. C'est la métrique de comparaison prioritaire pour la détection de panne Indusense.
- **S'en méfier :** la valeur dépend fortement de la proportion de positifs, donc elle se compare seulement sur des jeux comparables. Elle ne dispense pas de fixer et de tester le seuil réellement utilisable par les équipes.

### Log loss (*cross-entropy*) et Brier score

- **Calcul et mesure :** la **log loss** pénalise `−log(p)` pour la probabilité `p` attribuée à la vraie classe ; une probabilité très confiante et erronée est lourdement sanctionnée. Le **Brier score** est la moyenne de `(p − y)²`, avec `y` égal à 0 ou 1 : il mesure l'écart quadratique entre probabilité annoncée et résultat.
- **Type :** classification probabiliste ; log loss aussi en multiclasse.
- **À privilégier :** lorsqu'une sortie est utilisée comme probabilité, pour prioriser un risque ou calculer un coût attendu. Le Brier score est plus facilement interprétable que la log loss pour une cible binaire.
- **S'en méfier :** ces scores mélangent calibration et capacité à séparer les classes ; les utiliser avec une courbe de calibration. Ils exigent des probabilités, pas seulement des labels. Une probabilité « 80 % » n'est crédible que si des cas notés 80 % se réalisent environ 80 % du temps.

### Classification multiclasse : macro, pondéré et micro

- **Calcul et mesure :** précision, rappel et F1 sont calculés pour chaque classe. Une moyenne **macro** donne le même poids à chaque classe ; une moyenne **pondérée** (*weighted*) pèse chaque classe par son effectif ; une moyenne **micro** cumule les VP/FP/FN avant de calculer le score.
- **Type :** classification multiclasse ou multilabel.
- **À privilégier :** macro si chaque classe rare doit être protégée ; pondérée pour décrire la performance moyenne observée ; micro lorsque chaque décision individuelle a le même poids dans un problème multilabel.
- **S'en méfier :** la moyenne pondérée et la micro peuvent être dominées par la classe majoritaire. Toujours afficher aussi les résultats par classe et la matrice de confusion.

## Régression : mesurer l'écart de valeur

La **régression** prédit une quantité numérique continue : prix, consommation, durée restante. L'**erreur résiduelle** est `e = y − ŷ`.

### MAE (*Mean Absolute Error*)

- **Calcul et mesure :** `MAE = moyenne(|y − ŷ|)`. Elle donne l'erreur absolue moyenne, dans la même unité que la cible : par exemple « 2,4 heures » d'erreur moyenne sur une durée restante.
- **Type :** régression.
- **À privilégier :** lorsqu'une erreur de +10 et de −10 a le même coût et qu'une mesure robuste aux valeurs extrêmes est souhaitée.
- **S'en méfier :** elle ne pénalise pas plus sévèrement les grosses erreurs. Si une erreur très élevée est dangereuse, compléter par RMSE, quantiles d'erreur ou une métrique métier.

### MSE et RMSE

- **Calcul et mesure :** `MSE = moyenne((y − ŷ)²)` ; `RMSE = √MSE`. Le carré amplifie les grosses erreurs. RMSE revient dans l'unité de la cible, tandis que MSE est dans une unité au carré.
- **Type :** régression.
- **À privilégier :** quand les erreurs importantes doivent peser davantage, par exemple une très mauvaise estimation de consommation ou de durée de vie restante. RMSE est plus lisible que MSE dans un rapport.
- **S'en méfier :** une seule valeur aberrante peut dominer le score. Vérifier les erreurs individuelles et la qualité des données plutôt que conclure trop vite qu'un modèle est mauvais.

### R² (*coefficient de détermination*)

- **Calcul et mesure :** `R² = 1 − somme((y − ŷ)²) / somme((y − moyenne(y))²)`. Il compare le modèle à une prédiction constante égale à la moyenne. `1` est idéal ; `0` n'est pas meilleur que cette baseline ; il peut être négatif sur de nouvelles données.
- **Type :** régression.
- **À privilégier :** expliquer quelle part de la variabilité est capturée et comparer des modèles sur la même cible et le même jeu.
- **S'en méfier :** il ne donne pas une erreur dans l'unité métier, augmente souvent si l'on ajoute des variables et ne prouve ni causalité ni qualité sur d'autres populations. Ne pas comparer des R² entre cibles de variabilité différente.

### MAPE, sMAPE et erreurs relatives

- **Calcul et mesure :** `MAPE = moyenne(|(y − ŷ) / y|) × 100`. Elle exprime l'erreur relative en pourcentage. La **sMAPE** remplace le dénominateur par une expression dépendant de `|y|` et `|ŷ|` afin d'atténuer certains effets d'échelle.
- **Type :** régression, surtout prévision de séries temporelles.
- **À privilégier :** quand la comparaison relative est réellement utile, par exemple une erreur de 10 % de demande, et que les valeurs réelles sont strictement positives et éloignées de zéro.
- **S'en méfier :** MAPE est indéfinie si `y = 0` et explose près de zéro ; elle pénalise asymétriquement les sous-prédictions. Ne pas l'utiliser mécaniquement pour des compteurs contenant des zéros.

### MedAE et quantiles d'erreur

- **Calcul et mesure :** **MedAE** est la médiane de `|y − ŷ|` : la moitié des erreurs est inférieure ou égale à cette valeur. Un quantile, par exemple P90, indique la valeur sous laquelle se situent 90 % des erreurs absolues.
- **Type :** régression.
- **À privilégier :** données bruitées ou comportant des valeurs extrêmes ; objectifs de service tels que « 90 % des estimations à moins de 4 h d'erreur ».
- **S'en méfier :** la médiane peut cacher la gravité des 10 % pires erreurs. La présenter avec MAE/RMSE et la distribution des résidus.

### Pinball loss et couverture d'intervalle

- **Calcul et mesure :** la **pinball loss** pénalise différemment une sous-estimation et une surestimation selon un quantile `q` à prédire. La **couverture** d'un intervalle `[borne basse, borne haute]` est la proportion de vraies valeurs incluses dans cet intervalle.
- **Type :** régression quantile et prévision avec incertitude.
- **À privilégier :** lorsqu'il faut exprimer une incertitude actionnable : stock de sécurité, délai prudent, prévision P90. Une couverture cible de 90 % signifie que l'intervalle devrait contenir environ 90 % des valeurs futures.
- **S'en méfier :** une couverture seule récompense un intervalle infiniment large. La compléter par sa largeur moyenne et vérifier la couverture sur données non vues.

## Clustering : évaluer une structure sans toujours disposer de vérité terrain

Le **clustering** regroupe des observations sans cible connue. Une métrique **interne** utilise seulement les données et les clusters ; une métrique **externe** les compare à des groupes de référence connus. Une bonne métrique ne prouve pas que les clusters ont un sens métier.

### Inertie / WCSS

- **Calcul et mesure :** somme des distances au carré entre chaque point et le centroïde de son cluster. Elle mesure la compacité interne ; K-means cherche à la minimiser.
- **Type :** clustering par centroïdes, notamment K-means.
- **À privilégier :** tracer la méthode du coude pour examiner plusieurs valeurs de `k` sur des données mises à l'échelle.
- **S'en méfier :** elle diminue toujours lorsque `k` augmente : elle ne désigne jamais seule le bon nombre de clusters et dépend de l'échelle des variables.

### Silhouette score

- **Calcul et mesure :** pour chaque point, compare la distance moyenne à son propre cluster (`a`) à la distance au cluster voisin le plus proche (`b`) : `(b − a) / max(a, b)`. La moyenne varie de `−1` à `1` ; plus elle est élevée, plus les clusters sont compacts et séparés.
- **Type :** clustering, sans labels.
- **À privilégier :** comparer quelques nombres de clusters avec une même distance et des données normalisées.
- **S'en méfier :** favorise les groupes compacts et séparés, souvent quasi sphériques ; peut mal noter une structure dense, irrégulière ou de densité différente pourtant utile. Inspecter aussi la taille et le contenu des groupes.

### Davies-Bouldin et Calinski-Harabasz

- **Calcul et mesure :** **Davies-Bouldin** compare dispersion interne et distance entre clusters : plus bas est préférable. **Calinski-Harabasz** compare la séparation inter-clusters à la dispersion intra-cluster : plus haut est préférable.
- **Type :** clustering sans labels.
- **À privilégier :** compléter silhouette pour comparer plusieurs partitions avec la même représentation des données.
- **S'en méfier :** leurs valeurs absolues n'ont pas de seuil universel et dépendent de la distance, de l'échelle et de la forme des groupes. Elles ne remplacent pas une interprétation métier.

### ARI et NMI : comparaison avec une référence connue

- **Calcul et mesure :** l'**ARI** (*Adjusted Rand Index*) compare les paires d'observations placées ensemble ou séparées, en corrigeant l'accord dû au hasard ; `1` est parfait, `0` correspond approximativement au hasard. La **NMI** (*Normalized Mutual Information*) mesure l'information partagée entre clusters et labels de référence, de `0` à `1`.
- **Type :** clustering avec labels externes ou partition de référence.
- **À privilégier :** vérifier si des clusters retrouvant une segmentation connue — type de machine, famille de panne — ont une cohérence avec cette référence, sans imposer les mêmes noms de clusters.
- **S'en méfier :** si les labels de référence sont utilisés pour entraîner ou choisir les clusters, ce n'est plus une validation indépendante. Un bon ARI/NMI décrit l'accord avec la référence, pas nécessairement l'utilité future.

## Autres problèmes utiles à connaître

### Détection d'anomalies

- **Calcul et mesure :** si des anomalies validées existent, utiliser précision, rappel, PR-AUC et taux de faux alertes comme pour une classification, en définissant explicitement ce qu'est une anomalie. Sans labels, suivre la proportion d'alertes, leur stabilité et une revue métier d'un échantillon.
- **Type :** détection d'anomalies ou de nouveauté.
- **À privilégier :** score d'anomalie confronté à des événements ultérieurs ou à une expertise humaine ; recherche d'une liste priorisée à examiner.
- **S'en méfier :** une observation rare n'est pas forcément un défaut. Sans vérité terrain, aucun score interne ne mesure directement un « taux de détection de panne ».

### Ranking : NDCG et précision à k

- **Calcul et mesure :** la **précision à k** est la part d'éléments pertinents dans les `k` premiers résultats. **NDCG@k** mesure la pertinence, pondérée par la position : un résultat utile au premier rang vaut plus qu'au dixième, puis normalisée par le classement idéal.
- **Type :** recherche, recommandation, priorisation de dossiers ou d'alertes.
- **À privilégier :** lorsqu'une équipe ne peut traiter que les `k` alertes les plus prioritaires.
- **S'en méfier :** définir ce que signifie « pertinent » et la capacité réelle `k`. Une bonne qualité dans le top 10 ne dit rien des alertes hors top 10 ni de la calibration du score.

### Analyse de survie : concordance (C-index)

- **Calcul et mesure :** le **C-index** est la proportion de paires comparables correctement ordonnées : une observation dont l'événement survient plus tôt doit recevoir un risque plus élevé. Il gère les observations **censurées**, dont l'événement n'a pas encore été observé à la fin du suivi.
- **Type :** temps avant événement, par exemple durée avant panne.
- **À privilégier :** lorsqu'on prédit ou classe un risque au cours du temps en présence de censure.
- **S'en méfier :** il évalue surtout l'ordre des risques, pas la précision des probabilités dans le temps. Compléter par une vérification de calibration et des courbes de survie adaptées.

## Guide de décision rapide

| Situation observée | Métriques à afficher en priorité | Pourquoi |
|---|---|---|
| Régression, erreur lisible dans l'unité métier | MAE, RMSE, P90 d'erreur | Erreur moyenne, gravité des grosses erreurs et niveau de service. |
| Régression avec cible parfois nulle | MAE/RMSE, pas MAPE seule | MAPE devient instable ou indéfinie près de zéro. |
| Classification équilibrée, erreurs comparables | Accuracy, matrice de confusion, F1 | Vue globale plus détail des erreurs. |
| Classe positive rare | PR-AUC/AP, précision, rappel, F-bêta, matrice de confusion | La classe minoritaire et les fausses alertes restent visibles. |
| Panne ou danger à ne pas manquer | Rappel, F2, précision au seuil choisi | Le FN est le risque dominant, sans oublier la capacité à traiter les alertes. |
| Action coûteuse déclenchée par une alerte | Précision, spécificité, rappel minimal | Limiter les FP tout en conservant une détection acceptable. |
| Probabilité utilisée pour décider | Brier/log loss, courbe de calibration, PR-AUC ou ROC-AUC | Distinguer justesse des probabilités et pouvoir de classement. |
| Clustering sans labels | Silhouette, Davies-Bouldin, tailles et analyse métier | Mesurer compacité/séparation sans confondre score et sens métier. |
| Clustering avec groupes de référence | ARI/NMI, puis analyse métier | Vérifier l'accord avec une partition externe. |

## Démarche reproductible pour un rapport d'évaluation

1. Écrire le besoin métier et l'erreur la plus coûteuse. Exemple : « rater une panne est plus coûteux qu'une inspection ».
2. Définir la cible et l'unité d'évaluation : une ligne, une machine, une panne, un client, une fenêtre temporelle.
3. Séparer entraînement, validation et test avant toute transformation. Pour des données chronologiques, respecter le temps et prévoir une zone tampon si les horizons se chevauchent.
4. Sur validation, comparer les modèles avec des métriques cohérentes et choisir le seuil selon le coût et la capacité opérationnelle.
5. Figer modèle et seuil, puis produire sur test : métriques principales, matrice de confusion ou distribution des erreurs, effectifs et période observée.
6. Interpréter les résultats avec le métier : un score élevé peut être inutilisable si le volume d'alertes dépasse la capacité des équipes.

## Exemple appliqué à Indusense

Le besoin « un arrêt d'urgence se produira-t-il dans les 24 heures ? » est une **classification binaire déséquilibrée**. La classe positive est l'arrêt dans cet horizon. Le rapport final doit donc contenir au minimum :

- la prévalence des arrêts dans chaque partition ;
- PR-AUC/AP pour comparer les scores de modèles ;
- précision, rappel et F2 au seuil retenu sur validation ;
- la matrice de confusion sur le test temporel, pour chiffrer pannes manquées et inspections inutiles ;
- éventuellement le Brier score et une courbe de calibration si la probabilité de panne est affichée aux utilisateurs.

L'accuracy seule serait trompeuse si les arrêts sont rares. Le seuil `0,5` n'est pas une règle métier : il doit être choisi sur validation, puis seulement évalué une fois sur le test.

### Traduire un résultat pour un Product Owner

Un score technique doit se reformuler en langage métier avant restitution, par exemple (chiffres d'illustration du support Aelion, pas des résultats Indusense mesurés) :

| Métrique technique | Formulation métier |
|---|---|
| Recall = 85 % | Sur 100 pannes, 85 sont détectées ; 15 passent inaperçues. |
| FN = 30 (sur 200 positifs) | 30 pannes manquées = 30 arrêts non planifiés potentiels. |
| FP = 48 | 48 fausses alarmes = 48 interventions inutiles. |
| F1 = 0,78 | Score global de fiabilité — acceptable pour un POC. |
| ROC-AUC = 0,92 | Le modèle distingue bien les machines saines des machines à risque. |

Voir aussi la [fiche POC ML](12-poc-ml-baseline-cout-metier-plan-experience.md) pour le chiffrage du coût métier d'un FN et d'un FP (ordres de grandeur en euros).

## Erreurs fréquentes et bonnes pratiques

- Optimiser plusieurs fois sur le jeu de test : cela transforme implicitement le test en validation et surestime la généralisation.
- Annoncer une AUC ou un F1 sans indiquer le seuil, la classe positive, l'effectif et la prévalence.
- Comparer des PR-AUC calculées sur des populations ayant des proportions de positifs très différentes.
- Confondre une bonne capacité de classement (AUC) avec des probabilités fiables (calibration).
- Choisir une métrique uniquement parce qu'elle est élevée ; déclarer avant l'entraînement quelle erreur est la plus coûteuse.
- Utiliser un unique score de clustering comme une preuve que les groupes sont utiles ou causaux.

## Points à retenir pour le QCM

- Accuracy = décisions correctes toutes classes confondues ; elle peut masquer une classe rare.
- Précision = fiabilité des alertes ; rappel = part des positifs réels détectés.
- F1 équilibre précision et rappel ; F2 donne plus de poids au rappel.
- ROC-AUC mesure la capacité de classement sur tous les seuils ; PR-AUC est souvent plus informative pour une classe positive rare.
- MAE reste dans l'unité de la cible ; RMSE pénalise davantage les grosses erreurs ; MAPE ne convient pas aux valeurs nulles.
- Une métrique interne de clustering ne remplace pas la validation métier ; l'inertie diminue toujours quand le nombre de clusters augmente.

## À savoir expliquer lors de la soutenance

Savoir justifier : la cible et la classe positive ; les conséquences d'un FP et d'un FN ; le découpage qui protège le test ; le choix de la métrique principale ; le seuil opérationnel ; et les limites du résultat. Pour Indusense, expliquer pourquoi PR-AUC, rappel et précision au seuil retenu sont plus utiles qu'une accuracy isolée.

## Sources du cours

- `06_Evaluation_AELION.pdf`, support Aelion.
- `07_poc_ml.pdf`, support Aelion « POC ML & métriques métier » (Séance 11) : matrice de confusion, coût métier FN/FP, traduction technique → métier.
- `10_metriques_ROC_PR_AUC.pdf`, support Aelion « Rappel des métriques — ROC AUC & PR AUC ».

## Références techniques

- [scikit-learn — Model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html)
- [scikit-learn — Clustering performance evaluation](https://scikit-learn.org/stable/modules/clustering.html#clustering-performance-evaluation)
- [scikit-learn — Probability calibration](https://scikit-learn.org/stable/modules/calibration.html)
