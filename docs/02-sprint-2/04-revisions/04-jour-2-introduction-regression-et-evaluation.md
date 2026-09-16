# Sprint 2 — Jour 2 : régression, généralisation et évaluation

## Objectif et point de départ

Cette fiche synthétise l'introduction du jour 2 : distinguer les objectifs de **régression** et de **classification**, comprendre comment un modèle généralise à partir d'un historique, puis choisir une métrique d'évaluation adaptée au besoin métier.

Point de départ du TP : un Gold dataset a été nettoyé et séparé en jeux d'entraînement et de test ; un premier modèle a produit des prédictions. La question suivante est : **comment démontrer que cette prédiction est utile ?**

## Notions essentielles

- Une **feature** (caractéristique) est une colonne donnée en entrée au modèle, par exemple la surface, le nombre de pièces ou une mesure de capteur.
- La **cible** (*target* ou *label*) est ce que le modèle doit prédire : un prix pour une régression, ou `panne / pas de panne` pour une classification.
- La **régression** prédit une valeur numérique continue. Une régression linéaire cherche par exemple une combinaison pondérée des features pour estimer un prix.
- La **classification** prédit une catégorie. La régression logistique, malgré son nom, est un modèle de classification : elle transforme son score en une probabilité entre 0 et 1, puis un seuil permet de décider la classe.
- La **classe positive** est l'événement recherché. Pour Indusense, c'est l'occurrence d'une panne dans l'horizon choisi ; la classe négative est l'absence de panne dans cet horizon.
- La **généralisation** est la capacité à produire une prédiction correcte sur de nouvelles observations, non vues pendant l'entraînement. Le modèle ne doit pas seulement reproduire l'historique.

## Régression linéaire, polynomiale et création de features

Une régression linéaire combine les entrées avec des coefficients, par exemple :

`prix = a × surface + b × nombre_de_pièces + c × terrain + …`

Elle ne représente directement que des relations linéaires. Si le phénomène est plus complexe, on peut créer des features dérivées : par exemple `surface / nombre_de_pièces`, un carré ou un produit entre deux variables. Cette démarche est appelée **feature engineering** : elle encode une hypothèse métier dans les données d'entrée.

Une **régression polynomiale** ajoute ce type de transformations pour capturer des relations non linéaires tout en utilisant un modèle linéaire sur les nouvelles colonnes. Deux approches existent :

1. Créer peu de variables motivées par la connaissance métier : plus interprétable et souvent préférable.
2. Générer beaucoup de combinaisons, puis sélectionner les variables utiles : plus coûteux, plus difficile à expliquer et susceptible de créer du bruit ou des variables très corrélées.

Créer des features est un travail de conception et de validation ; ce n'est pas seulement du temps de calcul. Une variable redondante ou sans lien utile peut compliquer le modèle sans améliorer sa généralisation.

## La donnée avant l'algorithme

Un modèle apprend des régularités (*patterns*) observées dans son historique. Cet historique doit être :

- assez volumineux pour couvrir les cas utiles ;
- représentatif de ce que le modèle rencontrera après déploiement ;
- correctement étiqueté et préparé.

Avec trop peu d'exemples ou des exemples non représentatifs, le modèle ne peut pas généraliser de façon fiable : il produit alors une estimation fragile, voire proche du hasard. Le choix de l'algorithme compte, mais il ne compense pas une donnée insuffisante.

## Démarche commune à un modèle supervisé

1. Construire le Gold dataset et nettoyer les données.
2. Séparer les données en entraînement, validation et test. L'**entraînement** ajuste les paramètres ; la **validation** aide à choisir modèle et réglages ; le **test** mesure une seule fois la performance finale sur des données gardées à l'écart.
3. Préparer les features, par exemple par normalisation. Les statistiques de transformation sont calculées sur l'entraînement uniquement pour éviter une fuite de données.
4. Choisir un algorithme cohérent avec l'objectif : régression pour une valeur, classification pour une classe.
5. Entraîner : l'algorithme ajuste ses paramètres (ou poids) à partir de l'historique pour produire un modèle.
6. Évaluer le modèle avec des métriques adaptées, puis comparer les candidats avec les mêmes données de validation ou de test.

## Évaluer : une métrique dépend du risque métier

Une **métrique** est une mesure chiffrée de la qualité d'un modèle. Il n'existe pas de métrique universellement meilleure : le bon choix dépend de l'erreur la plus coûteuse.

Pour une classification binaire :

- La **précision** répond : parmi les alertes de panne, quelle part correspond réellement à une panne ? Une précision faible crée beaucoup de fausses alertes.
- Le **rappel** (*recall*) répond : parmi les pannes réelles, quelle part a été détectée ? Un rappel faible laisse passer des pannes.
- La **PR-AUC** (*Precision-Recall Area Under the Curve*) résume le compromis précision–rappel pour plusieurs seuils. Elle est particulièrement pertinente lorsque la classe positive est rare, comme les pannes Indusense.

Exemple médical : augmenter le rappel peut accepter davantage de faux positifs afin de manquer le moins possible de malades. À l'inverse, chercher une précision très élevée réduit les fausses alertes mais peut laisser passer des cas réels. Le même arbitrage doit être explicité pour la maintenance prédictive : coût d'un arrêt non détecté, coût d'une inspection inutile et capacité opérationnelle des équipes.

Pour une régression, les métriques ne sont pas les mêmes : elles mesurent l'écart entre une valeur prédite et une valeur réelle, par exemple l'erreur absolue moyenne (MAE) ou l'erreur quadratique moyenne (MSE/RMSE).

## Exemple Indusense

Si la cible est `panne dans les 24 h`, le modèle doit être évalué comme un classifieur. La PR-AUC aide à comparer les modèles lorsque les pannes sont peu nombreuses. Ensuite, le seuil de décision doit être choisi sur validation en fonction du compromis métier : une maintenance préventive inutile est un faux positif ; une panne imminente non signalée est un faux négatif.

## Erreurs fréquentes et bonnes pratiques

- Ne pas assimiler régression logistique et prédiction d'une valeur continue : elle sert ici à classer une observation via une probabilité.
- Ne pas conclure qu'un modèle est bon uniquement parce qu'il s'ajuste bien à l'historique : contrôler la généralisation sur des données non vues.
- Ne pas générer des features en grand nombre sans justification, sélection ni contrôle des corrélations.
- Ne pas choisir la métrique uniquement parce qu'elle est disponible dans une bibliothèque : relier sa signification au coût des faux positifs et faux négatifs.
- Ne pas utiliser le jeu de test pour régler le seuil ou choisir le modèle ; ces décisions appartiennent à la validation.

## Points à retenir pour le QCM

- Régression : valeur numérique continue ; classification : catégorie.
- La sortie d'une régression logistique est interprétable comme une probabilité de classe positive avant application d'un seuil.
- Une feature dérivée peut représenter une relation métier non capturée par les colonnes brutes.
- PR-AUC, précision et rappel concernent la classification ; MAE, MSE et RMSE concernent la régression.
- Un modèle utile généralise sur des données non vues et exige un historique représentatif.

## À savoir expliquer lors de la soutenance

Présenter l'objectif métier, la classe positive, les données historiques nécessaires, les features retenues et leur justification. Expliquer ensuite la séparation entraînement/validation/test, la métrique choisie et le compromis métier entre faux positifs et faux négatifs. Pour Indusense, justifier pourquoi une métrique orientée précision–rappel est plus informative qu'une simple accuracy lorsque les pannes sont rares.

## Validation

- Fiche fondée sur la transcription locale de l'introduction du Sprint 2, jour 2, horodatée de `00:00:00` à `00:18:49`.
- Le contenu est une synthèse pédagogique ; la transcription horodatée reste la source pour retrouver le passage oral correspondant.
