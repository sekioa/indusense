# Roadmap du gold dataset — prédire un arrêt machine à 6 h, 12 h et 24 h

## Objectif

Le gold dataset doit fournir les données nécessaires à un modèle de machine learning capable d’estimer, pour une machine et un instant donné, la probabilité qu’un arrêt survienne dans les **6, 12 ou 24 heures** suivantes.

Cette roadmap explique **pourquoi** et **comment** construire les variables utiles (*features*) à partir des tables silver : télémétrie, incidents, maintenances et référentiel machine. Elle ne contient aucun résultat calculé : les stagiaires devront produire leurs propres jeux de données, rapports et modèles de façon reproductible.

## 1. Vocabulaire essentiel, en langage simple

| Terme | Définition | Analogie du quotidien |
|---|---|---|
| **Instant de prédiction** ou **ancre** (`t`) | L’instant précis auquel le modèle doit prendre sa décision. | L’heure à laquelle on regarde son application météo avant de sortir. |
| **Feature** | Une information disponible à l’instant `t` et donnée au modèle : température récente, variation de pression, temps depuis la dernière maintenance, etc. | Ce que l’on voit dans le rétroviseur et sur le tableau de bord avant de décider de freiner. |
| **Cible** ou **label** | La réponse que le modèle doit apprendre à prédire. Ici : « un arrêt arrive-t-il dans les prochaines heures ? » | La pluie qui arrivera ou non après avoir consulté la météo. |
| **Fenêtre passée** (*lookback window*) | La période avant `t` utilisée pour fabriquer les features. | Observer les 30 dernières minutes de circulation avant de choisir un itinéraire. |
| **Fenêtre glissante** (*rolling window*) | Une fenêtre passée qui avance avec le temps et recalcule ses statistiques à chaque instant. | Chaque fois que le train avance d’un arrêt, on regarde les derniers kilomètres parcourus, pas toujours le même tronçon. |
| **Horizon** | La période future à prédire après `t`. Ici : 6 h, 12 h et 24 h. | Se demander s’il pleuvra dans une heure, cet après-midi ou demain. |
| **Tendance** (*trend*) | La direction et la vitesse d’évolution d’une mesure au cours du temps. | Une température qui monte régulièrement est plus informative qu’une température simplement élevée à un instant. |
| **Lag** | La valeur d’une variable à un instant précédent. | Comparer le prix affiché aujourd’hui à celui d’hier. |
| **Fuite de données** (*data leakage*) | Utiliser, directement ou indirectement, une information qui n’était pas connue à l’instant `t`. | Connaître le résultat d’un match avant de parier sur son issue. |
| **Snapshot de features** | Une ligne décrivant une machine à l’instant `t`, avec toutes les features calculées à cet instant. | Une photo instantanée du tableau de bord de la machine. |

## 2. Principe temporel à respecter

Le modèle ne doit recevoir que des informations connues au moment de la prédiction. Les événements futurs servent uniquement à créer les labels pendant l’entraînement.

```text
                informations connues                 informations futures
───────────────┬──────────────────────────┬──────────────────────────────────────
               │ fenêtre passée            │ horizon à prédire
               │ [t - fenêtre ; t]         │ (t ; t + h]
───────────────┼──────────────────────────┼──────────────────────────────────────
               │       features            │          label
               │ moyenne, pente, incidents │ arrêt dans 6 h, 12 h ou 24 h ?
               │ précédents, maintenance   │
───────────────┴──────────────────────────┴──────────────────────────────────────
                                      t = instant de prédiction
```

### Règles à appliquer

1. Une feature ne peut utiliser qu’une donnée horodatée à `t` ou avant `t`.
2. Le label à l’horizon `h` est calculé uniquement avec les événements dans l’intervalle `(t ; t + h]`.
3. Une ligne d’entraînement ne peut être créée que si l’intégralité de son horizon futur est observable.
4. La dernière partie de l’historique ne doit donc pas être utilisée pour entraîner un horizon qui dépasse la fin des données disponibles.
5. Toute colonne calculée doit documenter son `feature_available_at` ou, au minimum, la dernière date source qu’elle a utilisée.

### Exemple conceptuel

Pour un snapshot à 10:00 :

- les features peuvent utiliser les mesures, incidents et maintenances connus jusqu’à 10:00 ;
- le label 6 h vaut `1` si un arrêt est observé entre 10:00 exclu et 16:00 inclus ;
- le label 12 h couvre la période jusqu’à 22:00 ;
- le label 24 h couvre la période jusqu’à 10:00 le lendemain.

Un même arrêt futur peut donc rendre positifs plusieurs horizons. C’est normal : les trois horizons sont trois questions différentes, pas trois classes exclusives.

## 3. Définir précisément ce qu’est un arrêt

Avant de développer le dataset gold, l’équipe métier doit valider une définition unique et versionnée de l’événement `machine_stop`.

### Première définition recommandée

Commencer avec un événement structuré et non ambigu, par exemple un incident portant l’indicateur d’arrêt d’urgence. Cette définition est plus fiable qu’une recherche de mots dans les commentaires libres.

### Définitions complémentaires à étudier avec le métier

- une maintenance réactive liée à un incident peut-elle être assimilée à un arrêt ?
- un incident de gravité élevée représente-t-il systématiquement un arrêt ou seulement un risque ?
- une production nulle sur plusieurs intervalles indique-t-elle un arrêt, une absence de production planifiée ou un problème de collecte ?
- les maintenances programmées doivent-elles être exclues des arrêts à prédire ou constituer une catégorie distincte ?

### Opérations à réaliser

1. Créer une table d’événements `gold_stop_event` avec au minimum : `machine_id`, `stop_at`, `stop_definition_version`, `source_event_id` et `source_table`.
2. Conserver le détail des événements sources ayant contribué à la définition d’arrêt.
3. Construire trois labels binaires : `target_stop_6h`, `target_stop_12h` et `target_stop_24h`.
4. Documenter la convention d’inclusion des bornes temporelles et l’appliquer dans tous les scripts.
5. Faire valider les faux positifs et faux négatifs apparents par un expert métier avant l’entraînement d’un modèle.

### Livrable attendu

Un contrat de label versionné, une table d’événements d’arrêt traçable et des tests couvrant les cas limites temporels.

## 4. Préparer une grille d’instants de prédiction

Le dataset gold doit avoir un grain clair : une ligne par **machine**, par **instant de prédiction** et, selon le format retenu, par **horizon**.

### Opérations à réaliser

1. Choisir la cadence de prédiction, par exemple une fois par heure si la télémétrie est horaire.
2. Créer une grille régulière de timestamps pour chaque machine active dans la période étudiée.
3. Aligner la grille sur les mesures de télémétrie validées de la couche silver.
4. Définir une règle pour les intervalles sans mesure : conserver le snapshot avec indicateurs de manque, l’exclure ou limiter la prédiction à certaines conditions de complétude.
5. Garantir l’unicité de la clé `(machine_id, prediction_at)`.
6. Ajouter les trois labels sur cette grille uniquement pour les snapshots ayant un horizon complet observable.

### Formats possibles

| Format | Description | Recommandation |
|---|---|---|
| **Large** | une ligne par machine et instant, avec trois colonnes de label `target_stop_6h`, `target_stop_12h`, `target_stop_24h` | recommandé pour construire les features une seule fois |
| **Long** | une ligne par machine, instant et horizon, avec une seule colonne `target_stop` et une colonne `horizon_hours` | utile pour comparer les horizons dans un même pipeline, mais les features sont répétées |

### Livrable attendu

Une table `gold_prediction_grid` avec une clé unique, des timestamps cohérents, les labels observables et les métadonnées de l’exécution.

## 5. Construire les features de télémétrie

La télémétrie est la source principale pour comprendre l’état récent de la machine. Une valeur isolée est rarement suffisante : le modèle doit aussi savoir si la mesure est stable, fluctuante, en hausse ou en baisse.

### 5.1 Fenêtres glissantes (*rolling windows*)

Pour chaque mesure continue, calculer plusieurs statistiques sur plusieurs fenêtres passées, par exemple 1 h, 3 h, 6 h, 12 h, 24 h et une fenêtre plus longue à valider avec le métier.

Pour chaque fenêtre, calculer lorsque pertinent :

- dernière valeur connue ;
- moyenne, médiane, minimum et maximum ;
- écart-type et étendue (`max - min`) ;
- quantiles bas et hauts ;
- nombre de mesures disponibles ;
- nombre et taux de valeurs manquantes ;
- nombre de points signalés atypiques par la couche silver.

**Analogie :** une température de 60 peut être normale pour une machine donnée. En revanche, passer de 40 à 60 en une heure peut être un signal important. Les fenêtres glissantes permettent de voir à la fois la photographie actuelle et le film des dernières heures.

### 5.2 Lags et différences

Créer des comparaisons entre la mesure actuelle et des instants antérieurs :

- `value_lag_1h`, `value_lag_6h`, `value_lag_24h` ;
- différence absolue : `current_value - value_lag` ;
- variation relative, seulement si le dénominateur est valide ;
- temps écoulé depuis la dernière mesure non nulle.

Ces variables mettent en évidence les changements rapides. Elles doivent être calculées par machine, après tri chronologique, sans emprunter une valeur appartenant à une autre machine.

### 5.3 Tendances (*trends*)

Une tendance résume le sens et la vitesse d’évolution d’un capteur dans une fenêtre passée.

Opérations à réaliser :

1. Pour chaque machine et chaque fenêtre, associer chaque mesure à un temps écoulé en heures.
2. Estimer une pente avec une régression linéaire simple, par exemple avec `numpy.polyfit` ou `sklearn.linear_model.LinearRegression`.
3. Conserver la pente, le nombre de points utilisés et éventuellement une mesure de qualité de l’ajustement.
4. Interpréter le signe : pente positive = hausse ; pente négative = baisse ; pente proche de zéro = stabilité relative.
5. Créer aussi des tendances simples et robustes, telles que `dernière_valeur - première_valeur` ou `moyenne_courte - moyenne_longue`.

**Analogie :** la position d’une voiture sur une pente ne suffit pas ; sa vitesse et son sens de déplacement disent si elle monte, descend ou reste stationnée. La pente d’un capteur joue ce rôle.

### 5.4 Features de production et de fonctionnement

Étudier et documenter les features suivantes :

- production cumulée, moyenne et variabilité dans les fenêtres passées ;
- nombre d’intervalles à production nulle ;
- écart entre production récente et production habituelle de la machine ;
- ratio de production par rapport à une capacité de référence, uniquement après validation de la cohérence des unités ;
- indicateurs de fonctionnement dégradé fondés sur plusieurs mesures cohérentes, pas sur une seule valeur isolée.

### 5.5 Ordre de calcul à implémenter

Commencer par une version volontairement simple sur une seule machine et quelques timestamps. Elle sert de référence pour vérifier ensuite l’implémentation vectorisée avec pandas.

```text
pour chaque machine :
    trier toutes les mesures par timestamp

    pour chaque instant de prédiction t :
        passé = mesures dont timestamp est dans (t - fenêtre ; t]

        moyenne_6h = moyenne(passé sur 6 h)
        écart_type_6h = écart-type(passé sur 6 h)
        pente_6h = pente des valeurs du passé sur 6 h
        lag_1h = dernière valeur disponible au plus tard une heure avant t

        futur_6h = arrêts dont stop_at est dans (t ; t + 6 h]
        target_stop_6h = 1 si futur_6h contient au moins un arrêt, sinon 0
```

Ensuite, remplacer les boucles coûteuses par des opérations vectorisées :

- `sort_values` par machine et timestamp ;
- `groupby("machine_id")` pour isoler l’historique de chaque machine ;
- `rolling("6h")`, `rolling("24h")` et `agg` pour les statistiques de fenêtre ;
- `shift` ou `merge_asof` pour les lags et les dernières informations événementielles connues ;
- jointures temporelles explicites pour construire les labels futurs.

Le choix des bornes est essentiel. Si le snapshot est créé juste après la mesure de `t`, la fenêtre de features peut inclure `t`. Si la prédiction est faite juste avant cette mesure, elle doit l’exclure. Ce choix doit être identique dans les tests, l’entraînement et l’inférence.

### Livrable attendu

Une spécification de features de télémétrie indiquant, pour chaque feature, la formule, la fenêtre, l’unité, les colonnes sources, les règles de valeurs manquantes et la date maximale de donnée autorisée.

## 6. Construire les features d’incidents et de maintenance

Les incidents et maintenances sont des événements. Ils doivent être transformés en informations disponibles avant `t`.

### Features d’incidents à étudier

- temps depuis le dernier incident de la machine ;
- nombre d’incidents dans les fenêtres précédentes ;
- nombre d’incidents par type et par niveau de gravité dans les fenêtres précédentes ;
- gravité maximale et moyenne des incidents récents ;
- temps depuis le dernier incident de chaque famille ;
- présence d’un incident dans une fenêtre courte ;
- nombre de types d’incident distincts récemment observés.

### Features de maintenance à étudier

- temps depuis la dernière maintenance ;
- temps depuis la dernière maintenance proactive et réactive ;
- durée et type de la dernière maintenance connue ;
- composant de la dernière maintenance, sous forme catégorielle canonique ;
- nombre de maintenances dans les fenêtres précédentes ;
- nombre de maintenances réactives récentes ;
- maintenance programmée à venir, seulement si son planning était réellement connu au moment de la prédiction et possède une date de disponibilité fiable.

### Règles indispensables

1. Joindre les événements à la machine par clé canonique.
2. Utiliser exclusivement les événements ayant eu lieu à `t` ou avant `t`.
3. Ne pas utiliser une maintenance liée à un incident futur comme feature du snapshot actuel.
4. Conserver la date source utilisée pour chaque agrégat si une investigation ultérieure est nécessaire.
5. Exclure les noms d’opérateurs et les commentaires libres du premier modèle ; ils peuvent contenir des informations personnelles ou des indices connus seulement après l’événement.

### Livrable attendu

Une table de features d’événements par machine et instant de prédiction, avec les règles temporelles de jointure documentées.

## 7. Ajouter les features statiques et calendaires

### Features statiques possibles

- modèle de machine ;
- ligne de production et atelier ;
- niveau de criticité ;
- capacité quotidienne et horaire ;
- âge de la machine à l’instant `t` ;
- statut actif, s’il est fiable et connu au moment de la prédiction.

### Features calendaires possibles

- heure de la journée ;
- jour de la semaine ;
- mois ou saison ;
- poste de travail si celui-ci peut être connu à l’avance ;
- encodage cyclique de l’heure et du jour (`sin` / `cos`) pour respecter leur caractère circulaire.

**Analogie :** 23 h et 0 h sont voisins dans la vraie vie, même s’ils sont éloignés dans une colonne numérique. L’encodage cyclique évite de faire croire au modèle qu’ils sont aux extrémités opposées d’une règle.

### Règles de prudence

- ne pas utiliser une catégorie si elle est créée ou corrigée après l’instant de prédiction ;
- ne pas utiliser de données personnelles comme prédicteur sans justification, minimisation et validation conformité ;
- documenter les attributs statiques qui peuvent évoluer dans le temps et rattacher leur version valide à `t`.

### Livrable attendu

Une liste de features statiques et calendaires avec leur source, leur disponibilité temporelle et leur stratégie d’encodage.

## 8. Encodage et préparation des features pour le modèle

### Principe

Le gold dataset conserve les catégories sous une forme compréhensible. L’encodage est une étape de préparation pour le modèle, réalisée dans un pipeline reproductible. Il ne doit pas écraser les colonnes gold canoniques.

### Opérations à réaliser

1. Séparer les colonnes numériques, booléennes, catégorielles et textuelles.
2. Exclure du premier modèle les identifiants uniques, les commentaires libres et toute information non disponible à `t`.
3. Imputer les valeurs manquantes uniquement dans le pipeline de machine learning, après la séparation entraînement / validation / test.
4. Ajouter des indicateurs de valeurs manquantes pour les mesures dont l’absence peut être informative.
5. Utiliser `OneHotEncoder` pour les catégories à cardinalité faible ou modérée.
6. Configurer `handle_unknown="ignore"` pour ne pas bloquer une prédiction si une nouvelle modalité apparaît.
7. Utiliser `ColumnTransformer` et `Pipeline` pour appliquer les mêmes transformations à l’entraînement et en production.
8. Standardiser les variables continues lorsque le modèle choisi le nécessite, avec `StandardScaler` appris uniquement sur l’entraînement.
9. Enregistrer les noms des features générées, la configuration et les versions de bibliothèques.
10. Sauvegarder le pipeline avec `joblib` ou `skops` et tester son rechargement sur un lot nouveau.

### Livrable attendu

Un pipeline de préparation de features sérialisé, versionné et testé, ainsi qu’un catalogue reliant chaque feature encodée à sa colonne source.

## 9. Prévenir la fuite de données

La fuite de données est l’un des principaux risques dans un projet de prédiction d’arrêt : elle peut produire d’excellents scores pendant les tests, puis un modèle inutilisable en production.

### Contrôles à mettre en place

1. Vérifier que `max_source_timestamp` de chaque feature est inférieur ou égal à `prediction_at`.
2. Vérifier que les événements utilisés pour les labels sont strictement postérieurs à `prediction_at`.
3. Construire les labels avant tout mélange aléatoire des lignes.
4. Réaliser une séparation chronologique des données : entraînement dans le passé, validation plus récente, test final encore plus récent.
5. Prévoir une zone tampon entre jeux si les fenêtres passées ou horizons futurs se chevauchent.
6. Ajuster les imputeurs, scalers et encodeurs uniquement sur l’ensemble d’entraînement.
7. Vérifier qu’aucune colonne ne révèle directement l’événement futur : statut final, compte-rendu post-incident, identifiant d’incident futur ou durée de maintenance future.
8. Écrire des tests unitaires sur une petite série temporelle artificielle où l’on connaît exactement les valeurs autorisées avant et après `t`.

### Livrable attendu

Une suite de tests de fuite de données et un manifeste des colonnes autorisées ou interdites pour chaque instant de prédiction.

## 10. Assembler les tables gold

### Tables recommandées

| Table | Grain | Rôle |
|---|---|---|
| `gold_feature_snapshot` | machine × instant de prédiction | features canoniques disponibles à `t` |
| `gold_stop_label` | machine × instant de prédiction | labels d’arrêt pour 6 h, 12 h et 24 h, avec l’événement source |
| `gold_training_dataset` | machine × instant de prédiction | jointure des snapshots et labels, réservée à l’entraînement et l’évaluation |
| `gold_feature_catalog` | une ligne par feature | formule, source, fenêtre, unité, disponibilité et version |
| `gold_data_quality` | contrôle × lot | résultats de contrôles temporels, de complétude et de lignée |

### Colonnes minimales du snapshot

- `machine_id` ;
- `prediction_at` ;
- `feature_version` ;
- `source_batch_id` ou références de lots ;
- `max_source_timestamp` ;
- features de télémétrie, incidents, maintenance, référentiel et calendrier ;
- indicateurs de qualité et de valeurs manquantes.

### Opérations à réaliser

1. Construire les features par familles puis les joindre sur `(machine_id, prediction_at)`.
2. Contrôler qu’une jointure ne multiplie pas les lignes.
3. Vérifier l’unicité de la clé du snapshot.
4. Joindre les labels uniquement pour fabriquer le jeu d’entraînement ; les snapshots de production n’ont pas encore de label.
5. Écrire les tables en Parquet, partitionnées par date de prédiction ou date de génération selon le volume.
6. Ajouter un manifeste précisant les versions de sources, de règles et de features utilisées.

### Livrable attendu

Un ensemble de tables gold Parquet, versionnées, traçables et séparant clairement features, labels et dataset d’entraînement.

## 11. Évaluer les modèles selon les horizons

Les horizons 6 h, 12 h et 24 h doivent être évalués séparément. Un bon modèle à 24 h n’est pas automatiquement bon à 6 h.

### Opérations à réaliser

1. Mettre en place un baseline simple pour chaque horizon, par exemple une régression logistique ou une règle métier explicite.
2. Entraîner ensuite des modèles plus riches seulement si le baseline est correctement évalué.
3. Mesurer au minimum : rappel (*recall*), précision (*precision*), F1, PR-AUC et matrice de confusion.
4. Examiner la calibration des probabilités : une prédiction de risque à 0,80 doit correspondre approximativement à une fréquence réelle comparable.
5. Choisir un seuil d’alerte avec les équipes opérationnelles, en tenant compte du coût d’une fausse alerte et du coût d’un arrêt non anticipé.
6. Mesurer les alertes par machine et par jour pour éviter un système inutilisable parce qu’il alerte en permanence.
7. Analyser les performances par machine, modèle, ligne et période, sans masquer les sous-groupes en difficulté.
8. Conserver les prédictions, versions de modèle, seuils et explications dans une table d’audit.

### Livrable attendu

Un rapport de performance par horizon, une décision documentée sur les seuils d’alerte et un modèle de référence réexécutable.

## 12. Idées complémentaires à explorer

- Construire des features « rapide contre lent » : moyenne sur une courte fenêtre moins moyenne sur une longue fenêtre. Elles révèlent souvent les dérives récentes.
- Ajouter des comptes d’anomalies ou de valeurs manquantes sur les dernières fenêtres, sans transformer automatiquement une anomalie en arrêt.
- Comparer une machine à son propre historique avant de la comparer à l’ensemble du parc.
- Utiliser des quantiles ou scores robustes par machine pour réduire l’effet des différences naturelles entre modèles de machine.
- Ajouter des périodes d’observation après maintenance afin de vérifier si certains schémas précèdent un incident ou s’ils sont normaux après intervention.
- Prévoir une version « explicable » du modèle avec importances de variables et, si nécessaire, SHAP, afin que les équipes comprennent la raison d’une alerte.
- Mettre en place un suivi de dérive des données et des performances une fois le modèle déployé : nouvelles catégories, taux de valeurs manquantes, décalage de distributions et fréquence des alertes.
- Définir une boucle de retour métier : chaque alerte doit pouvoir être qualifiée comme utile, non pertinente ou non observable, afin d’améliorer les labels et les seuils.

## 13. Critères de fin de roadmap

Le gold dataset est prêt lorsque :

- la définition d’arrêt est validée et versionnée ;
- chaque feature possède une formule, une source, une fenêtre et une règle de disponibilité temporelle documentées ;
- les labels 6 h, 12 h et 24 h sont construits sans chevauchement avec les features ;
- les tests empêchent les fuites de données ;
- les features, labels et jeux d’entraînement sont séparés, versionnés et traçables ;
- les pipelines d’encodage et de préparation sont réexécutables ;
- l’évaluation est chronologique, réalisée séparément par horizon et compréhensible par les équipes métier.
