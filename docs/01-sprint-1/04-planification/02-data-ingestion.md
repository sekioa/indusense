# Roadmap d’ingestion et de préparation du silver dataset

## Objectif

Cette roadmap conduit à la création d’un **silver dataset** à partir de la couche bronze. Les données silver doivent être typées, standardisées, normalisées, dédoublonnées, contrôlées et prêtes pour l’analyse ou la préparation de jeux de features.

Le silver n’écrase pas la traçabilité du bronze : chaque enregistrement transformé doit conserver les métadonnées qui permettent de retrouver sa source, son lot d’ingestion et la règle de transformation appliquée.

Les résultats d’exécution ne doivent pas être écrits dans ce document. Les stagiaires doivent produire leurs propres rapports de qualité, journaux d’exécution et datasets versionnés.

## Environnement Python à utiliser

Les stagiaires doivent travailler avec un environnement Python 3.15.x et vérifier la compatibilité des dépendances avant de les adopter.

| Bibliothèque | Usage attendu |
|---|---|
| `pathlib`, `datetime`, `hashlib`, `logging`, `json`, `uuid` | fichiers, métadonnées de lots, empreintes, journalisation et identifiants techniques |
| `pandas` | transformations tabulaires, jointures, typage, dédoublonnage et exports |
| `numpy` | conversions numériques, valeurs manquantes et règles vectorisées |
| `pyarrow` | lecture et écriture de Parquet, schémas et partitionnement |
| `pandera` (recommandé) | contrats de données et validation de DataFrames |
| `scikit-learn` | `OneHotEncoder`, `ColumnTransformer`, `Pipeline` et persistance des transformations ML |
| `joblib` ou `skops` | sauvegarde versionnée des encodeurs et pipelines entraînés |
| `duckdb` ou `polars` (optionnel) | validation et transformations performantes sur des volumes plus importants |
| `great_expectations` (optionnel) | documentation et exécution de suites de contrôles de qualité |

## 1. Définir le contrat d’entrée et le périmètre silver

### Opérations à réaliser

1. Identifier les sources bronze à transformer et leur emplacement de lecture.
2. Définir la fréquence d’exécution, le mode de chargement (complet ou incrémental) et l’identifiant de lot.
3. Définir les entités silver attendues : référentiel machine, maintenances, incidents et télémétrie.
4. Définir le grain de chaque table silver : une ligne par machine, incident, intervention de maintenance ou mesure de télémétrie.
5. Définir les clés primaires métier, les clés techniques éventuelles et les clés étrangères entre tables.
6. Lister les règles de transformation dans une configuration versionnée plutôt que de les disperser dans le code.
7. Définir les règles de rejet, de quarantaine et d’avertissement ; ne pas mélanger les erreurs bloquantes et les anomalies métier à investiguer.

### Livrable attendu

Un contrat silver versionné comprenant le schéma cible, le grain, les clés, les sources bronze, les règles de transformation, les règles de qualité et la stratégie d’incrémentalité.

## 2. Lecture du bronze et traçabilité de la transformation

### Opérations à réaliser

1. Lire les données bronze sans dépendre de fichiers locaux non versionnés.
2. Préserver les colonnes de lignée : fichier source, identifiant de lot, date d’ingestion, numéro de ligne source et empreinte de l’enregistrement.
3. Ajouter les métadonnées silver : `silver_processed_at`, `pipeline_version`, `transformation_version` et, si besoin, un identifiant d’exécution.
4. Journaliser le nombre de lignes lues, transformées, envoyées en quarantaine et écrites dans chaque table cible.
5. Vérifier que la même exécution sur le même lot est idempotente : elle ne crée ni doublon ni résultat différent.
6. Prévoir une écriture atomique : écrire d’abord dans une zone temporaire, valider, puis publier la partition silver.

### Livrable attendu

Un module d’entrée réutilisable et un journal d’exécution permettant de relier toute ligne silver à son origine bronze.

## 3. Standardiser les noms, les types et les unités

### Opérations à réaliser

1. Appliquer une convention de nommage cohérente, par exemple `snake_case`.
2. Harmoniser les noms de clés identiques entre sources, par exemple utiliser un même nom canonique pour l’identifiant de machine.
3. Convertir les colonnes vers les types définis dans le contrat : chaînes, entiers, décimaux, booléens, dates et timestamps.
4. Normaliser les dates et timestamps dans une convention unique, idéalement UTC pour les instants ; documenter tout décalage de fuseau horaire.
5. Vérifier et standardiser les unités de mesure. Toute conversion d’unité doit être explicite, testée et documentée.
6. Harmoniser les valeurs nulles : convertir les chaînes représentant une absence vers une valeur nulle standard, sans inventer de valeur de remplacement.
7. Conserver les colonnes bronze d’origine ou leur référence de lignée lorsque la transformation modifie une valeur.
8. Contrôler les échecs de conversion et envoyer les lignes concernées en quarantaine avec le motif du rejet.

### Livrable attendu

Un schéma silver typé, un dictionnaire de correspondance source → cible et un rapport des erreurs de conversion.

## 4. Nettoyer et standardiser les valeurs textuelles

### Opérations à réaliser

1. Supprimer les espaces de début et de fin avec une règle uniforme.
2. Uniformiser la représentation Unicode et les caractères invisibles.
3. Définir une règle de casse par colonne : conserver la casse pour les noms propres, utiliser une forme canonique pour les codes et catégories contrôlées.
4. Standardiser les identifiants métier en préservant les zéros initiaux et le format attendu.
5. Créer des tables de correspondance versionnées pour les libellés synonymes, fautes connues ou anciennes valeurs.
6. Ne modifier un libellé que si une règle explicite existe ; conserver la valeur d’origine et la règle appliquée dans la lignée si le changement est significatif.
7. Isoler les valeurs inconnues dans une catégorie explicite ou une table de quarantaine, plutôt que de les rapprocher automatiquement d’une catégorie existante.

### Livrable attendu

Des tables de mapping versionnées, des règles de normalisation testées et un rapport des valeurs non reconnues.

## 5. Gérer les valeurs manquantes et les règles de plausibilité

### Opérations à réaliser

1. Définir, pour chaque colonne, si une valeur nulle est autorisée, interdite ou conditionnelle.
2. Distinguer les valeurs manquantes structurelles des valeurs manquantes accidentelles.
3. Ajouter des indicateurs de présence lorsque l’absence est informative pour l’analyse ultérieure.
4. Conserver les valeurs manquantes dans silver lorsqu’aucune règle métier fiable ne permet de les compléter.
5. N’imputer une valeur que dans une vue de features ou une couche dédiée, jamais sans règle et sans trace.
6. Mettre en quarantaine les lignes qui violent une contrainte bloquante : clé obligatoire absente, date invalide, mesure impossible ou valeur hors domaine confirmé.
7. Mettre en place des contrôles de plausibilité : bornes physiques, unités, séquences temporelles et combinaisons de statuts autorisées.

### Livrable attendu

Une matrice de gestion des valeurs manquantes, des règles de plausibilité automatisées et une table de quarantaine avec le motif de chaque ligne.

## 6. Dédupliquer les données

### Opérations à réaliser

1. Distinguer les doublons exacts, les doublons de clé et les doublons métier.
2. Définir une clé de dédoublonnage par entité : identifiant d’incident, identifiant de maintenance, clé machine ou combinaison machine / timestamp pour la télémétrie.
3. Définir une stratégie de résolution documentée : conserver le premier, le dernier, la version la plus complète, agréger ou placer en quarantaine.
4. Comparer les lignes portant la même clé afin d’identifier les conflits de valeurs.
5. Ne jamais dédupliquer silencieusement une donnée conflictuelle ; conserver les lignes écartées et le motif de la décision.
6. Créer une table d’audit de dédoublonnage avec clé métier, lignes candidates, règle appliquée, ligne retenue et lignes exclues.
7. Tester la stabilité du dédoublonnage : les mêmes données et la même règle doivent produire le même résultat.

### Cas particulier : télémétrie

Pour une même machine et un même timestamp, définir explicitement si les valeurs représentent :

- des répétitions techniques à supprimer ;
- plusieurs mesures légitimes à conserver ;
- des mesures à agréger avec une fonction métier définie ;
- des conflits nécessitant une quarantaine.

### Livrable attendu

Des tables silver dédoublonnées, une table d’audit de dédoublonnage et des tests automatisés de stabilité.

## 7. Normaliser le modèle de données

### Opérations à réaliser

1. Extraire le référentiel machine dans une table dédiée, avec une ligne par machine au grain choisi.
2. Conserver les interventions de maintenance dans une table de faits ou d’événements reliée à la machine par clé canonique.
3. Conserver les incidents dans une table de faits ou d’événements reliée à la machine et, lorsque possible, à une maintenance.
4. Conserver la télémétrie dans une table de mesures au grain machine / timestamp défini par la règle de dédoublonnage.
5. Éviter la répétition des attributs de machine dans les tables d’événements lorsque ces attributs appartiennent au référentiel.
6. Définir les clés étrangères et tester l’intégrité référentielle après transformation.
7. Décider si les attributs de machine évoluent dans le temps ; si oui, définir une stratégie d’historisation, par exemple un SCD de type 2.
8. Documenter les jointures autorisées, les cardinalités et les règles temporelles de rattachement.

### Modèle cible minimal

| Table silver | Grain | Contenu principal |
|---|---|---|
| `silver_machine` | une ligne par machine | identifiant machine et attributs de référence standardisés |
| `silver_maintenance` | une ligne par intervention | date, type, composant, durée, incident lié et clé machine |
| `silver_incident` | une ligne par incident | instant, gravité, opérateur, catégories d’incident et clé machine |
| `silver_telemetry` | une ligne par mesure validée | timestamp, mesures capteurs, production et clé machine |
| `silver_quarantine` | une ligne par rejet ou conflit | donnée source, motif, règle, lot et date de traitement |

### Livrable attendu

Un schéma relationnel documenté, des tables normalisées et des tests de clés primaires et étrangères.

## 8. Préparer les catégories et le One-Hot Encoding

### Principe

Les catégories restent sous une forme normalisée dans les tables silver. Le One-Hot Encoding doit être produit dans une **vue de features distincte**, destinée à la modélisation ou aux analyses qui le nécessitent. Il ne doit pas remplacer la colonne catégorielle canonique.

### Opérations à réaliser

1. Identifier les catégories adaptées à un encodage : cardinalité faible ou modérée, sens métier stable et disponibilité au moment de la prédiction.
2. Exclure les identifiants uniques, les textes libres et les catégories à très forte cardinalité d’un premier encodage One-Hot.
3. Définir explicitement la liste des colonnes à encoder dans une configuration versionnée.
4. Utiliser `OneHotEncoder` dans un `ColumnTransformer` et une `Pipeline` scikit-learn.
5. Configurer `handle_unknown="ignore"` afin que les nouvelles modalités ne fassent pas échouer l’inférence.
6. Déterminer si une modalité de référence doit être supprimée (`drop="first"`) selon le modèle cible ; documenter ce choix.
7. Ajuster l’encodeur uniquement sur les données d’entraînement afin d’éviter toute fuite de données.
8. Utiliser une séparation temporelle lorsque les données représentent une série d’événements ou de mesures.
9. Conserver les noms de features générés et vérifier leur stabilité entre versions.
10. Sauvegarder l’encodeur, sa configuration, la version des bibliothèques et le schéma de features avec `joblib` ou `skops`.
11. Tester les cas de modalités inconnues, de valeurs nulles et de catégories rares.

### Livrable attendu

Une table ou vue `silver_features` documentée, un pipeline d’encodage sérialisé, une liste de colonnes encodées et une suite de tests contre la fuite de données et les modalités inconnues.

## 9. Contrôles de qualité du silver dataset

### Opérations à réaliser

1. Définir des schémas `pandera` ou des expectations équivalentes pour chaque table silver.
2. Contrôler les types, nullités, unicité, domaines de valeurs, bornes numériques et formats d’identifiants.
3. Contrôler l’intégrité référentielle entre référentiel machine, incidents, maintenances et télémétrie.
4. Contrôler la cohérence temporelle : timestamps valides, ordre des événements, dates de maintenance et incidents liés.
5. Vérifier que le dédoublonnage et les mappings ont bien été appliqués selon leur version de règle.
6. Comparer les volumes entrants, sortants et mis en quarantaine.
7. Produire un rapport de qualité et échouer l’exécution uniquement pour les violations définies comme bloquantes.

### Livrable attendu

Une suite de tests automatisée, un rapport de qualité par lot et un seuil d’acceptation explicite avant publication.

## 10. Publier et maintenir le silver dataset

### Opérations à réaliser

1. Écrire les tables silver en Parquet avec un schéma explicite.
2. Partitionner les tables volumineuses selon un axe adapté, par exemple date d’événement ou date d’ingestion, sans créer un trop grand nombre de petites partitions.
3. Publier les tables uniquement après la réussite des contrôles bloquants.
4. Ajouter un manifeste de publication : lot, versions de schéma et pipeline, sources, volumes, statut qualité et emplacements des sorties.
5. Gérer l’évolution de schéma : ajout de colonne, renommage, changement de type et dépréciation.
6. Mettre en place des métriques de suivi : volumes, taux de nulls, taux de doublons, nouvelles catégories et lignes en quarantaine.
7. Prévoir un mécanisme de reprise, de réexécution et de retour à une version antérieure.
8. Appliquer les règles de sécurité et de confidentialité aux données d’opérateurs : accès minimal, pseudonymisation si nécessaire et durée de conservation documentée.

### Livrable attendu

Des tables silver partitionnées et versionnées, un manifeste de publication, un journal de lignée et un tableau de suivi de qualité.

## 11. Critères de fin de roadmap

La préparation silver est considérée comme terminée lorsque :

- chaque source bronze est lue de façon reproductible et traçable ;
- les valeurs sont standardisées selon un contrat documenté ;
- les doublons sont traités avec une règle et un audit explicites ;
- les données sont normalisées en tables cohérentes et reliées par des clés testées ;
- les catégories restent disponibles sous forme canonique et les features One-Hot sont versionnées séparément ;
- les contrôles de qualité, la quarantaine et la publication Parquet sont automatisés ;
- les données silver sont réexécutables, historisées et prêtes pour les usages analytiques ou une couche gold.
