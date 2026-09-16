# Roadmap d’analyse et de préparation du bronze dataset

## Objectif

Cette roadmap décrit les opérations que les stagiaires doivent réaliser sur les fichiers CSV du dossier `datas/` :

- `machine.csv` ;
- `releves_incidents.csv` ;
- `telemetry.csv`.

Le but n’est pas de documenter les résultats de l’analyse dans ce fichier, mais de définir une démarche reproductible. Les résultats produits par les scripts ou notebooks devront être enregistrés séparément avec leur date d’exécution.

La couche **bronze** reste fidèle aux sources : aucune ligne ne doit être supprimée, aucune valeur ne doit être corrigée silencieusement et les anomalies doivent être conservées avec leurs métadonnées de contrôle.

## Environnement Python à utiliser

Les stagiaires doivent travailler avec un environnement Python 3.15.x et vérifier la compatibilité des dépendances retenues.

| Bibliothèque | Usage attendu |
|---|---|
| `pathlib`, `csv`, `datetime`, `logging`, `json` | manipulation de fichiers, dates, journalisation et exports de rapports |
| `pandas` | chargement, profiling, filtrage, agrégation et contrôles de qualité |
| `numpy` | calculs numériques, quantiles et bornes IQR |
| `matplotlib` et `seaborn` | graphiques statiques : distributions, corrélations, boxplots et séries temporelles |
| `scikit-learn` | standardisation et détection multivariée avec `IsolationForest` |
| `pyarrow` | écriture de fichiers Parquet pour la couche bronze |
| `pandera` (recommandé) | validation déclarative des schémas et des règles de qualité |

## 1. Inventaire et profil initial

### Opérations à réaliser

Pour chaque fichier CSV :

1. Vérifier l’existence du fichier, sa taille, son encodage et son séparateur.
2. Charger le fichier avec `pandas.read_csv` sans conversion destructive.
3. Extraire le nombre de lignes et de colonnes (`DataFrame.shape`).
4. Lister les noms de colonnes dans leur ordre source.
5. Afficher quelques lignes d’exemple (`head`, `sample`) pour contrôler la lisibilité du chargement.
6. Relever les types inférés par pandas (`dtypes`, `info`).
7. Compter les valeurs manquantes par colonne et au total (`isna().sum()`).
8. Rechercher les chaînes vides et les valeurs textuelles représentant une absence, par exemple `""`, `"NA"`, `"N/A"` ou `"null"`.
9. Compter les doublons de lignes complets (`duplicated`).
10. Produire un rapport de profil au format Markdown, JSON ou CSV.

### Livrable attendu

Un rapport par fichier contenant uniquement les métadonnées de profil : nom du fichier, date d’analyse, nombre de lignes, nombre de colonnes, colonnes, types inférés, taux de valeurs manquantes et nombre de doublons.

## 2. Typage et dictionnaire de données

### Opérations à réaliser

1. Classer chaque colonne dans l’une des familles suivantes : identifiant, date, heure, timestamp, numérique, booléen, catégorie ou texte libre.
2. Définir le type cible de chaque colonne et le justifier dans un dictionnaire de données.
3. Tester le parsing des dates et timestamps avec `pd.to_datetime(..., errors="coerce")`.
4. Mesurer les échecs de parsing avant toute conversion définitive.
5. Vérifier que les identifiants restent des chaînes, même si certains ne contiennent que des chiffres.
6. Vérifier que les indicateurs binaires utilisent uniquement les valeurs attendues, par exemple `0` et `1`.
7. Pour les incidents, créer une colonne dérivée `incident_at` à partir de `date` et `time`, sans supprimer les colonnes sources.
8. Pour la télémétrie, documenter explicitement le fuseau horaire du champ `timestamp` ou l’absence de fuseau.

### Livrable attendu

Un dictionnaire de données versionné : colonne, type source, type cible, description métier, unité éventuelle, caractère nullable, clé ou relation éventuelle, et règle de validation.

## 3. Analyse des colonnes catégorielles

### Opérations à réaliser

1. Identifier toutes les colonnes catégorielles, y compris les clés métier, catégories de maintenance, postes, composants, modèles et machines.
2. Calculer la cardinalité de chaque colonne (`nunique`).
3. Produire les effectifs et pourcentages de chaque modalité (`value_counts`).
4. Identifier les modalités rares, inconnues ou inattendues.
5. Vérifier l’homogénéité des libellés : espaces superflus, casse, accents, fautes de frappe et synonymes.
6. Distinguer les identifiants à forte cardinalité des catégories métier à analyser.
7. Ne normaliser les libellés qu’en vue d’une couche silver ; conserver la valeur source dans bronze.

### Livrable attendu

Une table de cardinalité et de fréquence par colonne catégorielle, accompagnée d’une liste des modalités à faire valider par le métier.

## 4. Statistiques descriptives des mesures numériques

### Opérations à réaliser

1. Sélectionner les colonnes numériques en excluant les identifiants techniques des analyses statistiques.
2. Calculer, pour chaque mesure : nombre de valeurs disponibles, minimum, maximum, moyenne, médiane, écart-type, quartiles et percentiles utiles.
3. Utiliser `DataFrame.describe` puis compléter avec les métriques nécessaires.
4. Contrôler les unités de mesure : température, pression, tension, rotation, volumes produits, capacités et durées.
5. Rechercher les valeurs impossibles ou incohérentes avec les règles métier : valeurs négatives, valeurs hors domaine ou valeurs constantes inattendues.
6. Réaliser les statistiques globales puis, lorsque pertinent, les segmenter par machine, ligne, type de maintenance ou poste.

### Livrable attendu

Une table de statistiques descriptives par variable numérique, ainsi qu’une liste des règles de plausibilité à valider avec les responsables métier.

## 5. Contrôles de qualité des données

### Opérations à réaliser

1. Vérifier l’unicité des clés attendues : identifiant d’incident, identifiant de maintenance et toute autre clé définie dans le dictionnaire de données.
2. Vérifier les doublons métier, par exemple une même combinaison machine / timestamp dans la télémétrie.
3. Vérifier les relations entre fichiers :
   - les machines référencées par les incidents et la télémétrie doivent exister dans le référentiel machine ;
   - les incidents liés à une maintenance doivent exister dans le fichier des incidents.
4. Vérifier les domaines de valeurs : gravité, criticité, statuts booléens, types d’incident et types de maintenance.
5. Mesurer la complétude par colonne, par machine et par période.
6. Mettre en place un statut de contrôle par ligne ou par lot : `valid`, `warning`, `invalid`, sans supprimer les données source.
7. Journaliser chaque contrôle, son seuil, son résultat et les lignes concernées.

### Livrable attendu

Un rapport de qualité par lot et une table de contrôles contenant au minimum : nom du contrôle, fichier, date de calcul, seuil, valeur observée, statut et nombre de lignes concernées.

## 6. Graphiques de distribution

### Opérations à réaliser

Pour chaque mesure numérique pertinente :

1. Produire un histogramme pour visualiser la distribution.
2. Ajouter, si utile, une courbe de densité (KDE).
3. Produire un boxplot pour visualiser les quartiles et les valeurs atypiques.
4. Comparer les distributions par groupe métier : machine, ligne, atelier, type de maintenance ou poste.
5. Ajouter les titres, unités, légendes, dates de génération et sources de données aux graphiques.
6. Enregistrer les images dans un répertoire versionné, sans les mélanger aux données bronze.

### Graphiques attendus par fichier

| Fichier | Graphiques à produire |
|---|---|
| `machine.csv` | histogramme et boxplot des durées de maintenance ; barplots par type de maintenance, composant, criticité, ligne et atelier ; comparaison des durées par type ou composant |
| `releves_incidents.csv` | barplots de gravité, de poste, de machine et de type d’incident ; barplots empilés de gravité par machine ou par poste ; série temporelle du volume d’incidents |
| `telemetry.csv` | histogrammes, densités et boxplots des capteurs et de la production ; comparaison par machine ; séries temporelles par machine et par capteur ; graphique de complétude des mesures |

### Livrable attendu

Un répertoire de graphiques accompagné d’un notebook ou script reproductible expliquant le choix de chaque visualisation.

## 7. Analyse des corrélations

### Opérations à réaliser

1. Sélectionner uniquement des variables numériques comparables ; exclure les identifiants et le texte libre.
2. Gérer explicitement les valeurs manquantes avant le calcul : suppression temporaire des lignes incomplètes ou stratégie de calcul par paire.
3. Calculer une matrice de corrélation de Pearson pour les mesures continues.
4. Utiliser Spearman lorsque la variable est ordinale, comme la gravité, ou lorsque la relation semble non linéaire.
5. Produire une heatmap annotée de la matrice de corrélation.
6. Compléter les relations importantes avec des nuages de points, une droite de tendance et une coloration par machine si nécessaire.
7. Réaliser les calculs globalement et par machine lorsque les groupes ont des régimes de fonctionnement différents.
8. Documenter qu’une corrélation n’implique pas une causalité.

### Livrable attendu

Une matrice de corrélation par fichier, les graphiques associés et une courte note précisant les variables exclues et les choix de méthode.

## 8. Détection des valeurs atypiques avec l’IQR

### Opérations à réaliser

1. Appliquer la méthode IQR uniquement aux variables numériques pertinentes.
2. Calculer `Q1`, `Q3`, `IQR = Q3 - Q1`, puis les bornes `Q1 - 1,5 × IQR` et `Q3 + 1,5 × IQR`.
3. Créer un indicateur d’anomalie par variable sans supprimer les lignes signalées.
4. Produire des boxplots annotés avec les bornes IQR et le nombre de lignes signalées.
5. Réaliser le calcul par groupe lorsqu’il est pertinent :
   - par type de maintenance pour les durées ;
   - par machine et fenêtre temporelle glissante pour la télémétrie ;
   - avec prudence sur la gravité des incidents, car une valeur élevée peut être un événement métier valide.
6. Exclure les identifiants, les catégories, les commentaires et les indicateurs binaires de l’IQR.
7. Conserver les bornes, la méthode, les paramètres et la date du calcul dans le rapport d’anomalies.

### Livrable attendu

Une table de drapeaux IQR et des graphiques associés. Chaque drapeau doit être interprété comme un signal à examiner, jamais comme une preuve d’erreur à supprimer.

## 9. Détection multivariée avec Isolation Forest

### Opérations à réaliser

1. Préparer une matrice de variables numériques pertinente par fichier et par machine si nécessaire.
2. Gérer les valeurs manquantes sans modifier les données bronze : utiliser un sous-ensemble complet pour l’entraînement ou ajouter des indicateurs de valeurs manquantes dans la vue d’analyse.
3. Standardiser les variables avec `StandardScaler` lorsque les amplitudes sont différentes.
4. Entraîner `IsolationForest` avec une graine aléatoire fixe et des paramètres explicitement documentés.
5. Tester plusieurs niveaux de contamination et comparer la stabilité des résultats.
6. Produire un score d’anomalie, un drapeau et la version du modèle pour chaque observation analysée.
7. Visualiser les points signalés dans les séries temporelles, les scatter plots et, si nécessaire, une projection en deux dimensions.
8. Valider les résultats avec une revue métier avant toute utilisation décisionnelle.

### Recommandations par fichier

| Fichier | Approche recommandée |
|---|---|
| `machine.csv` | privilégier l’analyse des durées ; le volume réduit impose une interprétation prudente et les attributs répétés de machine ne doivent pas dominer le modèle |
| `releves_incidents.csv` | analyser gravité et indicateurs de type d’incident ; traiter les commentaires séparément, sans les injecter directement dans un premier modèle |
| `telemetry.csv` | entraîner par machine ou par groupe de machines comparable, puis afficher le score sur les séries temporelles des capteurs |

### Livrable attendu

Un rapport de modèle contenant les variables utilisées, le prétraitement, les paramètres, la graine aléatoire, les scores, les drapeaux et les graphiques de validation.

## 10. Préparation de la couche bronze

### Opérations à réaliser

1. Conserver un exemplaire immuable de chaque fichier CSV source.
2. Ajouter des métadonnées techniques à chaque ligne ou lot : `source_file`, `ingested_at`, `batch_id`, `source_row_number` et `record_hash`.
3. Conserver les colonnes brutes et créer, si besoin, des colonnes typées parallèles plutôt que de remplacer les valeurs d’origine.
4. Préserver les valeurs manquantes, doublons et anomalies ; les décisions de correction, d’imputation ou de dédoublonnage sont reportées en silver.
5. Écrire les données bronze en Parquet avec `pyarrow`, partitionnées au minimum par source et date d’ingestion.
6. Ajouter un registre de schéma et une politique d’évolution de schéma.
7. Tester la réexécution d’un même lot afin de garantir l’idempotence et la traçabilité.

### Livrable attendu

Des datasets bronze partitionnés, un manifeste de lot, un dictionnaire de données, un rapport de qualité et des scripts d’ingestion réexécutables.

## 11. Critères de fin de roadmap

La roadmap est considérée comme réalisée lorsque :

- chaque CSV dispose d’un rapport de profil et d’un dictionnaire de données ;
- les contrôles de qualité sont automatisés et journalisés ;
- les distributions, corrélations et anomalies IQR / Isolation Forest sont visualisées sans modifier les sources ;
- les relations entre les fichiers sont testées ;
- les données bronze sont reproductibles, historisées, traçables et prêtes à alimenter une couche silver.
