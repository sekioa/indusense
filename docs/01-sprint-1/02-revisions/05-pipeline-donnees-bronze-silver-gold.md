# Pipeline de données Bronze, Silver et Gold

## Définition et objectif

L’architecture **Bronze–Silver–Gold**, aussi appelée architecture en médaillon, organise progressivement les données selon leur niveau de préparation. Un **pipeline de données** est l’enchaînement des opérations qui collecte, transforme et rend les données utilisables.

L’objectif est de conserver une source fidèle, de rendre les données fiables, puis de produire un dataset adapté au besoin de machine learning.

## Les trois niveaux

| Niveau | Rôle | Opérations principales |
| --- | --- | --- |
| Bronze | Conserver les données collectées au plus près de leur état d’origine | Ingestion, ajout de métadonnées techniques et traçabilité de la source |
| Silver | Obtenir des données propres, cohérentes et protégées selon le besoin du pipeline | Dédoublonnage, typage, normalisation, contrôles de qualité, gestion des rejets et transformations de protection nécessaires |
| Gold | Fournir les données utiles à un usage précis | Sélection, minimisation, anonymisation, *feature engineering* et préparation des jeux pour le modèle |

Un **dataset** est un ensemble structuré de données. Le **typage** associe à chaque valeur un type exploitable, comme une date, un nombre ou un booléen. La **normalisation** harmonise les formats ou les échelles. Les **rejets** sont les enregistrements qui ne satisfont pas les règles de qualité et qui doivent rester traçables pour être analysés ou corrigés.

## Démarche

### 1. Recenser et qualifier les sources

Les données peuvent venir de bases SQL, de fichiers XML, JSON, CSV, TXT ou TSV, ainsi que d’API externes. Une **API** est une interface permettant à un programme d’échanger avec un autre service.

Avant l’ingestion, vérifier notamment :

- les droits d’accès et les conditions d’utilisation ;
- les coûts, quotas et limites des API ;
- le format et la fréquence de mise à jour ;
- la présence éventuelle de données personnelles.

### 2. Construire le niveau Bronze

Le Bronze conserve une copie fidèle des données reçues afin de pouvoir rejouer le pipeline et auditer les transformations. Les notes du formateur recommandent de ne pas modifier les types à ce stade et de conserver les valeurs sous forme de texte.

Le principe général à retenir est la fidélité à la source. Le stockage systématique en texte est un choix d’implémentation dépendant du contexte : certains systèmes conservent plutôt le fichier brut et ses métadonnées sans le convertir.

### 3. Nettoyer le niveau Silver

Le passage au Silver comprend notamment :

1. la suppression ou le rapprochement des doublons ;
2. la conversion vers les types attendus ;
3. l’harmonisation des unités, libellés et formats ;
4. l’application de règles de qualité ;
5. l’isolement des lignes rejetées avec la raison du rejet.

Le résultat attendu est un dataset cohérent, contrôlé et encore réutilisable pour plusieurs usages.

Dans le TP `releves_incidents`, la consigne impose également de rendre les données qualifiées de sensibles non identifiables dès la production du Silver. Cela précise le pipeline propre à l’exercice : une transformation de protection n’est pas réservée par principe au Gold. Elle doit être appliquée au niveau approprié, avant qu’une donnée identifiable soit exposée ou utilisée sans nécessité. La méthode exacte reste à choisir après l’analyse des colonnes et du risque de réidentification.

Pour l'analyse incidents-maintenance, la décision retenue est une **minimisation par suppression** de `operator_name`, `operator_badge` et `shift`. Le commentaire libre `comment` est conservé dans Silver : il peut contenir une information métier sur un arrêt de machine absente des indicateurs structurés. Le fichier Bronze reste inchangé et le Silver est relu pour vérifier à la fois l'absence des trois colonnes opérateur et la présence du commentaire métier.

Cette minimisation réduit les identifiants directs, mais elle ne suffit pas à démontrer une anonymisation irréversible face à tout recoupement possible. Le commentaire libre doit également être contrôlé avant toute diffusion, car il peut contenir des éléments identifiants. Un horodatage précis associé à une machine peut encore constituer un quasi-identifiant si un tiers possède, par exemple, le planning détaillé des opérateurs.

### 4. Préparer le niveau Gold

Le Gold répond à un cas d’usage déterminé. Pour un modèle de machine learning, il peut inclure :

- la sélection des seules variables utiles ;
- la **minimisation**, c’est-à-dire la limitation des données personnelles au strict nécessaire ;
- l’**anonymisation**, qui vise à empêcher l’identification des personnes ;
- le **feature engineering**, c’est-à-dire la création ou la transformation de variables utiles au modèle ;
- le traitement d’un éventuel déséquilibre entre les classes ;
- la séparation en jeux d’entraînement, de validation et de test.

Le jeu d’entraînement sert à ajuster le modèle. Le jeu de validation sert à choisir les réglages. Le jeu de test sert à mesurer une dernière fois les performances sur des données restées à l’écart.

## Exemple concret

Pour prévoir une panne industrielle :

- Bronze conserve les relevés bruts des capteurs et leur date de collecte ;
- Silver convertit les dates et mesures, harmonise les unités, retire les doublons et isole les valeurs invalides ;
- Gold sélectionne les capteurs pertinents, calcule par exemple une moyenne glissante, puis produit les jeux d’entraînement, de validation et de test.

Dans Indusense, le métier confirme que plusieurs télémétries portant la même machine et le même timestamp sont des répétitions techniques dues à l'occupation du bus. Les 1 340 groupes observés présentent des écarts très faibles, inférieurs à `0,15 %` de la moyenne du groupe au maximum, et aucune différence sur le nombre de pièces produites. Bronze conserve toutes les lignes ; Silver conserve la ligne la plus complète, puis la première ligne source en cas d'égalité, et audite les 1 346 lignes écartées.

Une valeur de capteur manquante n'est pas automatiquement une ligne invalide. Dans le Bronze Indusense, 2 828 télémétries ont au moins une température, pression ou rotation absente. Comme les autres mesures de ces lignes restent valides, Silver conserve la ligne avec `NULL` et un avertissement. L'imputation éventuelle appartient à une future vue de features, avec une règle explicite, et non au nettoyage Silver.

### Observation Silver avant la définition du label Gold

Une exploration exécutée sur Silver sert à réunir des faits avant de décider le contrat métier d'un arrêt ; elle ne le remplace pas. Le périmètre observé couvre 1 245 incidents, 1 562 maintenances et 134 280 mesures de télémétrie, entre le 1er juin 2025 et le 9 juin 2026 selon la table.

- 19 incidents ont `is_emergency_stop = true`. Cette information est structurée, donc plus facilement traçable et testable qu'une interprétation du texte libre.
- Les incidents de criticité 4 portent la plus forte proportion observée d'arrêts d'urgence (`14 / 167`, soit `8,38 %`), mais la gravité 4 ne se confond pas avec un arrêt : 153 incidents de ce niveau ne sont pas des arrêts d'urgence.
- Les commentaires mentionnant `arrêt` ou `stop` sont associés à 18 des 19 arrêts d'urgence dans cet historique. Le test du chi-deux mesure une association très forte ; il ne prouve ni la causalité ni que le commentaire était disponible avant l'incident. Le texte libre reste donc du contexte d'analyse, pas une feature ou une règle de label à ce stade.
- 1 472 maintenances sont réactives et 90 proactives. Les liens vers les incidents aident à étudier le contexte, mais une intervention réactive ne doit pas être automatiquement assimilée à un arrêt machine.
- La télémétrie contient 270 mesures à production nulle (`0,20 %`). Une production nulle peut refléter un arrêt, une pause planifiée ou un défaut de collecte : elle demande une analyse temporelle avant tout usage comme label.

Les constats chiffrés sont dépendants du jeu Silver actuel. La décision versionnée sur `machine_stop` reste à valider par le métier avant la construction des labels Gold.

### Décision de périmètre : label Gold v1

Pour la première version pédagogique du Gold Indusense, un `machine_stop` est défini comme un incident `silver.incident` dont `is_emergency_stop = true`. L'événement porte la machine `machine_code`, la date `occurred_at`, l'identifiant source `incident_id` et la version de définition `emergency-stop-v1`.

Cette définition est volontairement restrictive : elle ne prétend pas couvrir tous les arrêts réels. En particulier, une machine peut être arrêtée manuellement en réponse à un problème. Les incidents de criticité élevée, les maintenances réactives et les périodes de production nulle ressemblent potentiellement à ce type de situation, mais ne seront **pas** ajoutés au label v1 sans une règle métier permettant d'éviter les faux positifs.

Une version ultérieure étudiera une définition enrichie des arrêts manuels, à partir de ces signaux et de leur chronologie. Les commentaires restent des éléments de qualification et de validation, jamais une règle automatique ou une feature du premier modèle.

Le notebook `notebooks/01-sprint-1/02-pipeline-donnees/04-build-data-gold.ipynb` construit en mémoire la table logique `gold_stop_event`, avec les cinq colonnes minimales de lignée, l'indicateur source d'arrêt d'urgence et la criticité source. Le commentaire libre n'est pas recopié : l'incident complet reste accessible dans Silver grâce à `source_table` et `source_event_id`.

L'exécution complète contre Silver valide 19 événements, 19 identifiants sources uniques, aucune valeur manquante dans les colonnes obligatoires et le respect de la définition `emergency-stop-v1` pour chaque ligne. Les labels ne sont pas encore construits.

Pour Gold V1, seuls les instants de prédiction disposant d'au moins 24 heures futures entièrement observables seront conservés. Cette règle rend les trois horizons de 6 h, 12 h et 24 h simultanément calculables et évite de transformer une fin d'historique inconnue en faux label négatif.

Le label d'une ligne porte uniquement sur l'arrêt futur de la machine identifiée par cette ligne. Une surchauffe ou un arrêt récent observé sur une autre machine peut néanmoins constituer une future feature de contexte si cette information est disponible à l'instant de prédiction. En revanche, rendre positif le label d'une machine qui ne s'arrête pas changerait la question métier en « une machine quelconque va-t-elle s'arrêter ? ».

La cadence de prédiction retenue pour Gold V1 est d'une heure, alignée sur les timestamps de `silver.telemetry`. Les 15 machines observées possèdent chacune 8 952 mesures, du 1er juin 2025 à 00:00 au 8 juin 2026 à 23:00 UTC, sans aucun intervalle différent de 60 minutes. Après retrait des 24 dernières heures non labellisables, la future grille doit contenir 8 928 instants par machine, soit 133 920 lignes.

Le notebook construit désormais `gold_prediction_grid` en mémoire, sans table PostgreSQL ni fichier. La grille générée contient bien 133 920 lignes et respecte le grain d'une ligne par machine et par heure. Les contrôles exécutés valident l'absence de clé `(machine_id, prediction_at)` dupliquée, une cadence strictement horaire et un horizon futur de 24 h observable pour chaque ligne.

Gold V1 conserve un snapshot même si aucune ligne de télémétrie ne correspond à son heure et expose alors `telemetry_row_available = false`. Une ligne Silver présente mais contenant un capteur à `NULL` est une situation différente : le snapshot reste également conservé, sans imputation à ce stade. Les indicateurs propres aux capteurs et la couverture des fenêtres seront traités avec les features. Sur la grille actuelle, les 133 920 snapshots ont tous `telemetry_row_available = true` et aucune heure Silver complète ne manque.

Les trois labels binaires sont ajoutés au format large avec la convention `(prediction_at ; prediction_at + horizon]`. L'exécution produit 102 positifs à 6 h (`0,0762 %`), 204 à 12 h (`0,1523 %`) et 408 à 24 h (`0,3047 %`). Les contrôles valident l'imbrication `target_stop_6h <= target_stop_12h <= target_stop_24h`, le maintien des 133 920 lignes et l'absence du timestamp futur temporaire dans la grille finale. Plusieurs arrêts proches peuvent couvrir les mêmes snapshots : le nombre de positifs ne se calcule donc pas en multipliant simplement le nombre d'arrêts par l'horizon.

Chaque ligne de la grille porte les métadonnées du contrat (`gold_dataset_version`, `stop_definition_version`, `prediction_cadence_hours`, `max_label_horizon_hours`) et de l'exécution (`gold_build_run_id`, `gold_built_at`, `source_observed_until`). Un UUID et un horodatage UTC communs identifient chaque exécution. Ces colonnes servent à la traçabilité et doivent être exclues des features ; `source_observed_until` contient notamment une information future par rapport à de nombreux snapshots.

### Première référence de features de télémétrie

La convention opérationnelle retenue pour les features est `(t - fenêtre ; t]` : la borne ancienne est exclue et la mesure disponible à l'instant `t` est incluse, car le snapshot est produit après sa réception. Avec une cadence horaire, une fenêtre de 6 h complète contient donc six mesures. Les labels restent calculés dans `(t ; t + horizon]`.

Avant toute vectorisation, le notebook calcule explicitement `temperature_last`, la moyenne, l'écart-type de population (`ddof=0`), le nombre de valeurs disponibles, le nombre et le taux de valeurs manquantes sur trois snapshots de `MACH-01`. `feature_available_at` vérifie que la date source maximale utilisée ne dépasse jamais `prediction_at`.

Dans l'exemple précédant le premier arrêt V1 de `MACH-01`, les trois fenêtres contiennent chacune six températures valides. La moyenne sur 6 h passe de `64,5985 °C` à `75,9993 °C`, puis `77,7433 °C`, tandis que la dernière valeur atteint `80 °C`. Ce cas illustre un signal à étudier ; il ne démontre pas à lui seul une relation causale généralisable entre la hausse de température et l'arrêt.

La même référence est recalculée avec `pandas.rolling("6h", closed="right")`. La dernière valeur, la moyenne, les comptes et taux de manque sont strictement identiques à la boucle. L'écart absolu maximal sur l'écart-type est de `4,66 × 10⁻¹⁴`, uniquement dû à l'arithmétique en virgule flottante et inférieur à la tolérance de validation `10⁻¹²`. Cette comparaison autorise la vectorisation sans changer la définition métier de la fenêtre.

La généralisation Gold V1 ajoute 100 features de télémétrie : quatre dernières valeurs (`temperature`, `pressure`, `voltage`, `rotation`) puis, pour les fenêtres de 3 h, 6 h, 12 h et 24 h, la moyenne, le minimum, le maximum, l'écart-type de population, le nombre de valeurs disponibles et le taux de manque. Les calculs sont réalisés par machine avec `rolling(..., closed="right")`, donc uniquement à partir de données disponibles dans `(t - fenêtre ; t]`. La fenêtre 1 h est écartée car elle répéterait la dernière mesure avec la cadence horaire ; l'étendue, les médianes et quantiles sont reportés pour limiter les features redondantes ; aucun compteur d'outlier n'est créé faute de signal numérique dédié dans Silver.

Sur les 133 920 snapshots, les taux de manque moyens des fenêtres restent faibles. Ils vont de `0,0112 %` à `0,1288 %` pour la tension et d'environ `0,67 %` à `0,86 %` pour les autres capteurs, selon la fenêtre. Les périodes de début d'historique restent présentes : leur couverture réduite est exposée par `available_count` et `missing_rate`, sans imputation ni exclusion.

### Lags et variations de télémétrie

Le vocabulaire retenu distingue la **variation signée** `delta = current_value - lag_value` d'une éventuelle valeur absolue dérivable ensuite. Un lag disponible à l'horizon `h` est la dernière valeur non nulle dont la date source est inférieure ou égale à `t - h`. Sa valeur doit être accompagnée de son âge réel : une feature nommée `lag_1h` peut autrement provenir d'une mesure plus ancienne si une télémétrie manque.

La variation relative est calculée par `delta / abs(lag_value)` seulement lorsque le lag est présent et non nul. Le temps écoulé depuis la dernière valeur non nulle est également conservé. La référence sur `MACH-01` vérifie les horizons 1 h, 6 h et 24 h : chaque source respecte sa date limite et, dans l'historique actuel sans trou, les âges réellement observés correspondent aux horizons demandés.

**Vectoriser** un calcul consiste à appliquer une opération sur une série ou une table entière plutôt que de parcourir une ligne de snapshot après l'autre avec une boucle Python. Pour les lags, une jointure temporelle vectorisée recherche, par machine, la dernière mesure non nulle dont la date est inférieure ou égale à `prediction_at - h`. Elle produit le même résultat que la référence explicite, mais efficacement sur toutes les lignes, tout en conservant l'horodatage source pour contrôler l'absence de fuite de données.

La vectorisation avec `merge_asof` ajoute 52 features : pour chaque capteur, le temps depuis la dernière mesure non nulle, puis aux horizons 1 h, 6 h et 24 h la valeur de lag, son âge réel, le delta signé et la variation relative. Les timestamps sources restent temporaires et ne sont pas intégrés au dataset. La jointure est partitionnée par machine et la comparaison aux neuf cas de référence de `MACH-01` est identique. Les sections 5.1 et 5.2 totalisent désormais 152 features de télémétrie : leur sélection et leur régularisation devront être étudiées avant l'entraînement, compte tenu des 19 arrêts indépendants disponibles.

### Tendances de télémétrie

Une tendance complète le niveau courant, les statistiques de fenêtre et les lags : elle mesure le sens et la vitesse d'évolution d'un capteur. Gold V1 retiendra, pour chaque capteur, une pente de régression linéaire sur 6 h et sur 24 h, exprimée dans l'unité du capteur par heure, ainsi que `mean_gap_6h_24h = moyenne_6h - moyenne_24h`. Un écart positif signifie que le niveau moyen récent dépasse son niveau moyen sur 24 h ; il peut révéler une montée récente sans établir à lui seul une causalité.

Comme les autres features de fenêtre, les pentes utilisent exclusivement les valeurs non nulles de `(t - fenêtre ; t]`. La pente nécessite au minimum deux valeurs : si cette condition n'est pas satisfaite, la feature reste manquante et ne doit pas être remplacée arbitrairement. Le contrôle `feature_available_at <= prediction_at` rend la frontière temporelle vérifiable.

La référence exécutée sur `MACH-01` avant le premier arrêt montre une hausse de température : à `2025-06-17 00:00 UTC`, la pente vaut `1,4955 °C/h` sur 6 h et `0,9437 °C/h` sur 24 h, avec un écart de moyennes de `11,6663 °C`. Elle valide la formule et le périmètre temporel ; la vectorisation pour l'ensemble des machines et des quatre capteurs reste l'étape suivante.

La vectorisation retenue calcule les pentes à partir des sommes glissantes du nombre de valeurs, du temps, de la valeur, du temps au carré et du produit temps-valeur. Elle ajoute 12 features : pour chacun des quatre capteurs, `slope_6h`, `slope_24h` et `mean_gap_6h_24h`. La jointure conserve les 133 920 snapshots Gold et la comparaison avec la référence explicite de `MACH-01` est identique à la tolérance de `10⁻¹²`. Les sections 5.1 à 5.3 totalisent donc 164 features de télémétrie.

Pour calculer une pente par heure de façon robuste, le temps est exprimé comme durée écoulée depuis la première mesure de la même machine. Cette translation ne modifie pas la pente. Éviter une conversion directe de la représentation interne d'un timestamp en entier : selon la précision (`us` ou `ns`) du type datetime, elle peut introduire une erreur d'unité, ici un facteur 1 000 détecté par la comparaison avec l'exemple de référence.

Erreur rencontrée : pour une machine sans arrêt futur, affecter directement `pd.NaT` crée par défaut une série sans fuseau horaire. Sa comparaison avec un `prediction_at` en UTC échoue avec `Cannot compare tz-naive and tz-aware datetime-like objects`. La série vide doit reprendre explicitement le type horodaté UTC de `gold_stop_event.stop_at`.

Précondition locale : si Docker Desktop n'est pas démarré, les requêtes Silver attendent ou échouent faute de PostgreSQL. Il faut démarrer Docker Desktop, puis vérifier le projet Compose explicite `indusense` avant d'exécuter le notebook. Un projet Compose implicite incorrect peut donner l'impression qu'aucun conteneur n'est présent.

Erreur de diagnostic rencontrée : lancer `docker compose` depuis le dossier `.docker` sans préciser le nom du projet a interrogé un projet Compose implicite différent et a donné l'impression que PostgreSQL était arrêté. Le contrôle correct utilise le projet `indusense` (option `-p indusense`) et confirme que le conteneur `db-1` est actif. Il faut vérifier le projet Compose ciblé avant de conclure qu'un service est indisponible.

## Erreurs fréquentes et bonnes pratiques

- Modifier ou écraser les données Bronze empêche de rejouer fidèlement les traitements.
- Supprimer silencieusement les rejets masque les problèmes de qualité ; conserver leur cause et leur provenance.
- Construire les variables ou équilibrer les classes avant la séparation peut provoquer une **fuite de données**, c’est-à-dire transmettre au modèle une information provenant indirectement de la validation ou du test.
- Équilibrer aussi les jeux de validation et de test peut fausser l’évaluation ; ils doivent généralement rester représentatifs des données réelles.
- Collecter des données « au cas où » s’oppose au principe de minimisation du RGPD.
- Utiliser une API sans vérifier ses droits, quotas et coûts peut rendre le pipeline non conforme ou non reproductible.

## Points à retenir pour le QCM

- Bronze conserve les données proches de la source.
- Silver nettoie, type, normalise et contrôle la qualité.
- Gold prépare les données pour un usage métier ou analytique précis.
- Selon le pipeline et le risque, les transformations de protection des données peuvent être nécessaires dès le niveau Silver.
- Les rejets doivent être explicables et traçables.
- Les jeux de validation et de test ne servent pas à entraîner le modèle.

## Points à savoir expliquer lors de la soutenance

- Pourquoi séparer les données en plusieurs niveaux plutôt que de modifier directement la source.
- Comment garantir la traçabilité d’une donnée depuis son origine jusqu’au modèle.
- Quelles transformations sont effectuées à chaque niveau et pourquoi.
- Comment éviter une fuite de données lors du *feature engineering* et de l’équilibrage.
- Comment la minimisation et l’anonymisation participent à la conformité RGPD.

La correspondance exacte avec les compétences C1 à C9 reste à confirmer avec le Kit candidat.

## Pour aller plus loin

- [Databricks — Architecture Medallion](https://www.databricks.com/glossary/medallion-architecture) : présentation détaillée des responsabilités Bronze, Silver et Gold.
- [scikit-learn — Données incohérentes et fuite de données](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage) : pièges à éviter lors des transformations et de l’évaluation.
- [CNIL — Principes clés du RGPD](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre2) : repère pour la minimisation et la traçabilité des traitements.
