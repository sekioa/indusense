# Cours structuré — Évaluation des modèles

## Objectif et point de départ

Ce cours permet d'évaluer un modèle au regard du besoin métier, plutôt que de retenir mécaniquement le score le plus élevé. L'utilisateur doit pouvoir choisir une métrique, lire les erreurs et défendre son protocole d'évaluation.

**Prérequis.** Un modèle a déjà produit des prédictions `y_pred` pour lesquelles on connaît la valeur réelle `y`. La transcription complète, horodatée et complétée par le support AELION est disponible dans [03-jour-2-evaluation-des-modeles.txt](../02-transcriptions/03-jour-2-evaluation-des-modeles.txt).

## 1. Pourquoi évaluer un modèle ?

Un modèle apprend sur des exemples connus. Son score sur ces exemples ne démontre pas sa capacité à réussir sur de nouvelles données : il peut avoir mémorisé une partie de l'entraînement. L'évaluation mesure la **généralisation**, c'est-à-dire la performance sur des observations non vues.

Une **métrique** est une mesure chiffrée de cette performance. Elle ne se choisit pas après avoir vu les résultats : elle traduit une décision métier sur ce que coûte une erreur.

Exemple : en maintenance prédictive, manquer une panne peut provoquer un arrêt de production ; déclencher une inspection inutile a aussi un coût, mais souvent inférieur. Il faut donc regarder les deux types d'erreurs, pas seulement le pourcentage global de décisions correctes.

## 2. Séparer entraînement, validation et test

| Jeu | Rôle | Usage autorisé |
| --- | --- | --- |
| **Train** | Le modèle apprend ses paramètres. | `model.fit(X_train, y_train)` |
| **Validation** | Comparer les modèles, régler les hyperparamètres et le seuil. | Essayer des variantes et prendre une décision. |
| **Test** | Mesurer la performance finale. | Évaluer une fois le modèle et le seuil figés. |

Le **jeu de test** représente souvent 20 % à 30 % des données et doit être représentatif de la production. Le flux minimal est :

```python
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
```

On compare ensuite `y_pred` à `y_test`, la **vérité terrain**, c'est-à-dire la réponse réellement observée.

### Le découpage dépend des données

Un découpage aléatoire convient à des observations indépendantes et identiquement distribuées. Pour une série temporelle, il faut conserver l'ordre : entraînement sur le passé, validation plus tard, test encore plus tard. Sinon, le modèle apprend indirectement des informations venant du futur : c'est une **fuite de données**.

Dans Indusense, les données étant temporelles, on ne doit pas utiliser un découpage aléatoire.

## 3. Partir du besoin métier

Avant de choisir une métrique, répondre à ces questions :

1. La cible est-elle une valeur continue ou une classe ?
2. Quelles erreurs sont coûteuses ou dangereuses ?
3. Quelle action une prédiction déclenche-t-elle ?
4. Quel volume d'alertes les équipes peuvent-elles traiter ?

Une métrique principale sert à comparer les modèles. Des métriques secondaires et les erreurs détaillées servent à comprendre ce résultat.

## 4. Régression : prédire une valeur continue

Une **régression** prédit un nombre : prix, consommation, durée restante ou température. L'**erreur résiduelle** est la différence entre la valeur réelle `y` et la prédiction `ŷ` :

`erreur = y - ŷ`

Pour moyenner les erreurs, il faut empêcher qu'une erreur positive annule une erreur négative.

### MAE — Mean Absolute Error

`MAE = moyenne(|y - ŷ|)`

La **MAE** est la moyenne des erreurs absolues. Les erreurs `-2`, `-3` et `+10` deviennent `2`, `3` et `10`. La MAE est dans l'unité de la cible : une MAE de 2,4 heures signifie une erreur moyenne de 2,4 heures.

- À privilégier si sur-prédiction et sous-prédiction ont un coût comparable.
- Limite : elle ne pénalise pas spécialement les très grandes erreurs.

### MSE et RMSE — pénaliser les grosses erreurs

`MSE = moyenne((y - ŷ)²)`

La **MSE** met les erreurs au carré. `-2`, `-3` et `+10` deviennent donc `4`, `9` et `100` : une grosse erreur pèse fortement dans le score.

`RMSE = √MSE`

La **RMSE** revient dans l'unité métier de la cible, tout en gardant cette forte pénalisation. MSE et RMSE sont utiles si une erreur extrême est particulièrement grave.

- Limite : une valeur aberrante peut dominer le score ; il faut aussi inspecter les erreurs individuelles et la qualité des données.

### R² — comparaison avec une référence naïve

Le coefficient de détermination **R²** compare le modèle à une référence qui prédit toujours la moyenne de `y_train` :

`R² = 1 - MSE_modele / MSE_modele_constant`

- `R² = 1` : prédictions parfaites.
- `R² = 0` : pas mieux que la référence constante.
- `R² < 0` : moins bon que cette référence.

R² ne donne pas une erreur dans l'unité métier. Il doit être lu avec MAE ou RMSE.

## 5. Classification binaire : prédire une classe

Une **classification binaire** prédit l'une de deux classes : panne / pas de panne, fraude / pas de fraude. La **classe positive** est l'événement que l'on cherche à détecter.

La **matrice de confusion** compte les quatre résultats possibles :

| Réalité / prédiction | Prédite négative | Prédite positive |
| --- | --- | --- |
| Réellement négative | **VN** : vrai négatif | **FP** : faux positif |
| Réellement positive | **FN** : faux négatif | **VP** : vrai positif |

Dans Indusense : VP = panne correctement signalée ; FN = panne manquée ; FP = alerte inutile ; VN = absence de panne correctement reconnue. Les cellules FP et FN doivent être évaluées au regard de leur coût métier.

### Accuracy — exactitude globale

`accuracy = (VP + VN) / (VP + VN + FP + FN)`

L'**accuracy** est la proportion de décisions correctes. Elle est trompeuse pour une classe rare : si 99 % des machines ne tombent pas en panne, prédire systématiquement « pas de panne » donne 99 % d'accuracy mais détecte 0 % des pannes.

Elle convient surtout lorsque les classes sont relativement équilibrées et que les coûts des erreurs sont comparables.

### Recall — trouver les positifs réels

`recall = VP / (VP + FN)`

Le **recall** (rappel ou sensibilité) répond à : « parmi tous les positifs réels, quelle part est détectée ? » Il réduit les faux négatifs.

On le privilégie lorsqu'il est grave de manquer un événement : panne critique, fraude majeure, risque sécurité ou dépistage. Un modèle qui prédit toujours positif atteint pourtant un recall de 1 : il faut donc le lire avec la precision.

### Precision — fiabilité des alertes

`precision = VP / (VP + FP)`

La **precision** répond à : « parmi les alertes émises, quelle part est réellement justifiée ? » Elle réduit les faux positifs.

On la privilégie lorsqu'une alerte consomme une ressource rare ou coûteuse. Une precision élevée peut toutefois provenir d'un modèle qui n'émet presque aucune alerte ; il faut la lire avec le recall.

### F1 et F-bêta — un compromis explicite

`F1 = 2 × precision × recall / (precision + recall)`

Le **F1-score** est la moyenne harmonique de precision et recall : il baisse fortement si l'une est faible.

- `F2` donne plus de poids au recall.
- `F0,5` donne plus de poids à la precision.

Pour Indusense, F2 est pertinent si une panne manquée coûte davantage qu'une inspection inutile. Cette pondération doit être justifiée avant de regarder le test.

## 6. Scores, probabilités et seuil de décision

Un classifieur peut fournir un score `p(x)` pour une observation `x`, souvent interprété comme une probabilité d'appartenir à la classe positive. Il faut un **seuil de décision** pour produire une classe :

- au-dessus du seuil, prédiction positive ;
- au-dessous, prédiction négative.

Abaisser le seuil génère souvent plus d'alertes : le recall augmente, mais les FP et la charge opérationnelle peuvent augmenter. Relever le seuil fait l'inverse. Le seuil `0,5` est une valeur technique par défaut, pas une règle métier.

Le seuil est choisi sur validation et figé avant l'évaluation sur test.

## 7. ROC-AUC et PR-AUC

La courbe **ROC** trace, pour tous les seuils, le taux de vrais positifs (**TPR**, identique au recall) contre le taux de faux positifs (**FPR**) :

`FPR = FP / (FP + VN)`

La **ROC-AUC** est l'aire sous cette courbe. Elle mesure la capacité à classer globalement un positif au-dessus d'un négatif :

- proche de `1` : bonne séparation des classes ;
- proche de `0,5` : comportement proche du hasard.

ROC-AUC ne choisit aucun seuil et ne garantit pas que les probabilités soient fiables. Quand les positifs sont rares, un FPR faible peut encore représenter beaucoup de fausses alertes.

La courbe **precision-recall** affiche precision et recall selon les seuils. La **PR-AUC** ou l'**Average Precision** est souvent plus informative pour une classe positive rare, comme les pannes Indusense. Sa référence utile est la **prévalence**, la proportion de positifs dans les données.

## 8. Démarche reproductible

1. Définir la cible, la classe positive et l'horizon de prédiction.
2. Identifier le coût d'un FP et d'un FN avec le métier.
3. Créer train, validation et test sans fuite de données.
4. Entraîner les candidats sur le train.
5. Comparer les candidats sur validation avec la métrique décidée et la matrice de confusion.
6. Choisir le seuil sur validation selon le compromis métier et la capacité à traiter les alertes.
7. Figer modèle et seuil.
8. Évaluer une seule fois sur le test : métriques, matrice de confusion, effectifs, période et limites.

## 9. Application à Indusense

La question est : « une panne se produira-t-elle dans les 24 prochaines heures ? » C'est une classification binaire déséquilibrée. Les données étant temporelles, le découpage doit être chronologique.

Le rapport final doit montrer :

- la prévalence des pannes ;
- PR-AUC pour comparer les modèles ;
- precision, recall et F2 au seuil retenu sur validation ;
- la matrice de confusion sur le test temporel ;
- le nombre concret de pannes manquées et d'inspections inutiles ;
- les limites : période observée, évolution des machines et capacité opérationnelle.

## 10. Erreurs fréquentes

- Évaluer sur le train et appeler ce score une performance de production.
- Choisir le seuil sur le test : le test devient alors implicitement un jeu de validation.
- Utiliser seulement l'accuracy pour une classe rare.
- Confondre precision (« les alertes sont-elles fiables ? ») et recall (« combien de vrais cas sont trouvés ? »).
- Dire que R² est toujours compris entre 0 et 1 : il peut être négatif sur des données nouvelles.
- Confondre capacité de classement (AUC) et fiabilité des probabilités (calibration).

## À retenir pour le QCM et la soutenance

- MAE est dans l'unité de la cible ; MSE/RMSE pénalisent les grosses erreurs ; R² compare à une prédiction constante.
- VP, FP, VN et FN sont les quatre résultats d'une classification binaire.
- `recall = VP / (VP + FN)` ; `precision = VP / (VP + FP)`.
- F1 équilibre precision et recall ; F2 favorise le recall.
- ROC-AUC évalue le classement sur tous les seuils ; PR-AUC est préférable si le positif est rare.
- Une métrique est défendable seulement si elle est reliée au coût métier et à un protocole train/validation/test correct.

Pour la soutenance, savoir justifier la classe positive, le coût de FP/FN, le découpage, la métrique, le seuil et la principale limite du résultat.

Correspondance exacte avec le référentiel C1 à C9 : à confirmer avec le Kit candidat local.
