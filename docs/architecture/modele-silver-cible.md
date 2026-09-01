# Modèle relationnel Silver cible

## Statut

Modèle validé, implémenté et publié sur PostgreSQL le 1er septembre 2026. Les modèles ORM, la migration Alembic, le pipeline, la CLI et les contrôles de données persistées sont validés.

## Objectif

Transformer les sources Bronze Indusense en tables métier typées, normalisées, reliées et traçables, sans modifier les fichiers reçus. L'implémentation Bronze existante sera remplacée plutôt que maintenue en parallèle. La première version utilise un chargement Silver complet et atomique afin de garder une mise en œuvre pédagogique simple.

## Faits observés

- `machine.sql` contient 15 machines et 1 562 maintenances dans deux structures distinctes.
- Les 1 245 incidents ont un `incident_id` unique, concernent 15 machines, n'ont aucune cellule vide et utilisent uniquement `0` et `1` pour les neuf indicateurs de type.
- La gravité observée va de 2 à 5 ; le domaine cible proposé reste 1 à 5.
- La télémétrie contient 135 626 mesures sur 15 machines.
- Elle contient 1 340 couples `(machine_id, timestamp)` répétés, soit 2 686 lignes et 1 346 lignes excédentaires si une seule mesure est conservée. Le métier confirme qu'il s'agit de répétitions techniques liées à l'occupation du bus de données.
- Les écarts à l'intérieur de ces groupes sont faibles : au maximum `0,063 °C`, `0,088 bar`, `0,064 V`, `0,088 rpm` et aucune différence sur `pieces_produced`. Le plus grand écart relatif à la moyenne d'un groupe reste inférieur à `0,15 %`.
- Les capteurs contiennent des plages de valeurs absentes : 894 températures, 995 pressions et 958 rotations sont vides dans Bronze ; 2 828 lignes ont au moins une mesure absente. Les 15 machines sont concernées.
- Parmi les 1 472 maintenances réactives liées à un incident, 503 portent un code machine différent de celui de l'incident.

## Décisions déjà confirmées

1. Le Bronze actuel sera remplacé par un Bronze aligné sur `machine.sql`, `releves_incidents.csv` et `telemetry.csv` ; aucune compatibilité avec les anciens fichiers n'est recherchée.
2. Les fichiers reçus et le Bronze restent fidèles à la source. L'alignement des codes machine est réalisé pendant le passage en Silver.
3. Pour une maintenance liée, la machine canonique est celle de l'incident désigné par `related_incident_id`.
4. Une maintenance proactive, sans incident lié, conserve son code machine source après contrôle dans le référentiel machine.
5. Les colonnes `operator_name`, `operator_badge`, `shift` et `comment` ne sont pas copiées en Silver.
6. Les mesures partageant une machine et un timestamp sont des doublons techniques : Silver conserve une seule ligne par `(machine_code, measured_at)`. La ligne la plus complète est retenue ; en cas d'égalité, la plus petite `source_row_number` gagne. La ligne représentante garde une clé `telemetry_id` auto-incrémentée et les lignes écartées restent traçables depuis Bronze.
7. Tous les horodatages métier sont en UTC, y compris les timestamps incidents et télémétrie qui ne portent pas d'offset dans les CSV.
8. `silver.machine` représente l'état courant, sans historisation dans cette première version.
9. Les neuf indicateurs d'incident utilisent les noms anglais définis dans ce contrat.
10. La description de maintenance est conservée en Silver.
11. Une anomalie bloquante annule la publication Silver complète.
12. Le chargement Silver initial est complet et atomique, non incrémental.

## Prérequis Bronze annule et remplace

Le nouveau Bronze comportera quatre grains :

| Table Bronze | Grain | Source |
|---|---|---|
| `bronze.machine_raw` | une ligne d'insertion machine | `machine.sql` |
| `bronze.maintenance_raw` | une ligne d'insertion maintenance | `machine.sql` |
| `bronze.incident_raw` | une ligne du fichier incidents | `releves_incidents.csv` |
| `bronze.telemetry_raw` | une ligne du fichier télémétrie | `telemetry.csv` |

Les valeurs métier restent en texte dans Bronze. Chaque ligne conserve `batch_id`, `source_row_number`, `record_hash` et `ingested_at`. L'ingestion de `machine.sql` écrit les machines et les maintenances dans une même transaction et dans un même lot, afin qu'une erreur ne laisse pas une moitié du fichier chargée.

Le remplacement Bronze et la recréation de la base de développement ont été exécutés avant l'implémentation Silver. Les quatre tables Bronze sont alimentées et constituent les seules entrées du pipeline.

## Colonnes de traçabilité communes à Silver

Chaque table métier Silver porte les colonnes suivantes :

| Colonne | Type PostgreSQL | Rôle |
|---|---|---|
| `source_batch_id` | `UUID` | lot Bronze d'origine, clé étrangère vers `ops.ingestion_batch` |
| `source_row_number` | `INTEGER` | ligne physique ou logique dans la source |
| `source_record_hash` | `VARCHAR(64)` | empreinte de la ligne Bronze |
| `pipeline_run_id` | `UUID` | exécution Bronze vers Silver ayant produit la ligne |
| `transformation_version` | `VARCHAR(32)` | version des règles appliquées |
| `silver_processed_at` | `TIMESTAMPTZ` | instant UTC de transformation |

La paire `(source_batch_id, source_row_number)` est unique dans chaque table Silver. Elle empêche le rejeu d'une même ligne Bronze dans une même cible, indépendamment de la clé métier.

## Table `silver.machine`

**Grain :** une ligne par machine dans l'état courant. Aucune historisation SCD n'est prévue dans cette première version.

| Colonne | Type | Null | Règle |
|---|---|---:|---|
| `machine_code` | `VARCHAR(16)` | non | clé primaire |
| `commissioning_date` | `DATE` | non | date de mise en service |
| `max_daily_capacity` | `INTEGER` | non | strictement positive |
| `max_hourly_capacity_pieces` | `INTEGER` | non | strictement positive |
| `model` | `VARCHAR(32)` | non | modèle canonique |
| `production_line` | `VARCHAR(16)` | non | ligne de production |
| `location` | `VARCHAR(16)` | non | atelier ou emplacement |
| `criticality` | `VARCHAR(8)` | non | `LOW`, `MEDIUM` ou `HIGH` |
| `is_active` | `BOOLEAN` | non | valeur issue de la source ou de son défaut déclaré |

Index proposés : `production_line` et `location`.

## Table `silver.incident`

**Grain :** une ligne par incident.

| Colonne | Type | Null | Règle |
|---|---|---:|---|
| `incident_id` | `VARCHAR(16)` | non | clé primaire |
| `machine_code` | `VARCHAR(16)` | non | clé étrangère vers `silver.machine` |
| `occurred_at` | `TIMESTAMPTZ` | non | fusion de `date` et `time`, interprétées directement en UTC |
| `severity` | `SMALLINT` | non | valeur comprise entre 1 et 5 |
| `is_overheating` | `BOOLEAN` | non | source `type_surchauffe` |
| `is_pressure_drop` | `BOOLEAN` | non | source `type_baisse_pression` |
| `is_vibration` | `BOOLEAN` | non | source `type_vibration` |
| `is_mechanical_noise` | `BOOLEAN` | non | source `type_bruit_mecanique` |
| `is_overconsumption` | `BOOLEAN` | non | source `type_surconsommation` |
| `is_mechanical_blockage` | `BOOLEAN` | non | source `type_blocage_mecanique` |
| `is_sensor_alarm` | `BOOLEAN` | non | source `type_alarme_capteur` |
| `is_emergency_stop` | `BOOLEAN` | non | source `type_arret_urgence` |
| `is_quality_defect` | `BOOLEAN` | non | source `type_defaut_qualite` |

Une contrainte unique supplémentaire sur `(incident_id, machine_code)` permet à la maintenance de référencer simultanément l'incident et sa machine. Index proposé : `(machine_code, occurred_at)`.

## Table `silver.maintenance`

**Grain :** une ligne par intervention de maintenance.

| Colonne | Type | Null | Règle |
|---|---|---:|---|
| `maintenance_id` | `INTEGER` | non | clé primaire métier fournie par la source |
| `machine_code` | `VARCHAR(16)` | non | machine canonique Silver |
| `source_machine_code` | `VARCHAR(16)` | non | code reçu dans `machine.sql` avant alignement |
| `machine_code_was_aligned` | `BOOLEAN` | non | vrai si la valeur a été corrigée en Silver |
| `maintenance_at` | `TIMESTAMPTZ` | non | instant déjà fourni avec fuseau dans le SQL |
| `maintenance_type` | `VARCHAR(16)` | non | `proactive` ou `reactive` |
| `action_type` | `VARCHAR(32)` | non | action normalisée |
| `component` | `VARCHAR(64)` | non | composant concerné |
| `description` | `TEXT` | non | description de l'intervention |
| `related_incident_id` | `VARCHAR(16)` | oui | incident lié, absent pour une maintenance proactive |
| `duration_hours` | `NUMERIC(6,2)` | non | strictement positive |

Contraintes proposées :

- clé étrangère `machine_code` vers `silver.machine` ;
- clé étrangère composée `(related_incident_id, machine_code)` vers `silver.incident(incident_id, machine_code)` ;
- `proactive` implique `related_incident_id IS NULL` ;
- `reactive` implique `related_incident_id IS NOT NULL`.

La clé étrangère composée garantit en base qu'une maintenance liée et son incident portent la même machine. Un incident peut néanmoins rester lié à plusieurs maintenances. Index proposés : `(machine_code, maintenance_at)`, `maintenance_type` et `related_incident_id`.

## Table `silver.telemetry`

**Grain :** une mesure validée par machine et par instant UTC, après suppression des répétitions techniques du bus.

| Colonne | Type | Null | Règle |
|---|---|---:|---|
| `telemetry_id` | `BIGINT GENERATED BY DEFAULT AS IDENTITY` | non | clé primaire technique auto-incrémentée |
| `machine_code` | `VARCHAR(16)` | non | clé étrangère vers `silver.machine` |
| `measured_at` | `TIMESTAMPTZ` | non | timestamp source interprété directement en UTC |
| `temperature_c` | `DOUBLE PRECISION` | oui | mesure en degrés Celsius ; absence conservée en `NULL` |
| `pressure_bar` | `DOUBLE PRECISION` | oui | mesure en bars ; absence conservée en `NULL` |
| `voltage_mean_v` | `DOUBLE PRECISION` | oui | tension moyenne en volts ; absence conservée en `NULL` |
| `rotation_mean_rpm` | `DOUBLE PRECISION` | oui | rotation moyenne en tours par minute ; absence conservée en `NULL` |
| `pieces_produced` | `INTEGER` | non | compteur non négatif |

`(machine_code, measured_at)` porte une contrainte d'unicité. Les 1 340 groupes temporels répétés actuellement observés produisent une ligne Silver chacun ; les 1 346 lignes Bronze écartées sont enregistrées dans l'audit de transformation. Les mesures de capteur absentes ne sont ni remplacées par zéro ni imputées : la ligne reste exploitable avec `NULL` et un avertissement d'audit.

## Tables opérationnelles

### `ops.pipeline_run`

Une ligne par exécution : `run_id`, versions du pipeline et des transformations, début, fin, statut et métriques de volumes. Une table d'association `ops.pipeline_run_source` relie l'exécution aux lots Bronze consommés.

### `ops.transformation_issue`

Une ligne par rejet, avertissement ou doublon écarté : exécution, référence Bronze, table cible, code de règle, niveau, action, motif et payload JSONB utile au diagnostic. La donnée brute reste dans Bronze ; cette table évite de recopier une ligne invalide dans Silver.

## Relations et cardinalités

```text
silver.machine 1 ─── 0..n silver.incident
silver.machine 1 ─── 0..n silver.maintenance
silver.machine 1 ─── 0..n silver.telemetry
silver.incident 1 ─── 0..n silver.maintenance
ops.pipeline_run 1 ─── 1..n ops.pipeline_run_source n ─── 1 ops.ingestion_batch
ops.pipeline_run 1 ─── 0..n ops.transformation_issue
```

La relation incident-maintenance ne signifie pas qu'une intervention est la preuve causale de l'incident ; elle matérialise le lien fourni par `related_incident_id` après correction de cohérence.

## Règles de transformation principales

1. Valider que chaque code machine des trois domaines existe dans le référentiel `machine`.
2. Convertir les types et envoyer en erreur toute valeur obligatoire non convertible.
3. Construire les timestamps incidents et télémétrie en leur attachant directement le fuseau UTC, sans conversion depuis un fuseau local.
4. Pour une maintenance réactive, retrouver l'incident et remplacer `machine_code` par la machine de cet incident ; conserver la valeur reçue dans `source_machine_code`.
5. Pour une maintenance proactive, conserver le code reçu après contrôle référentiel.
6. Supprimer du résultat Silver `operator_name`, `operator_badge`, `shift` et `comment`.
7. Dédupliquer les machines, incidents et maintenances par leur clé métier ; un conflit de contenu pour une même clé est bloquant et tracé.
8. Dédupliquer la télémétrie par `(machine_id, timestamp)` et tracer chaque ligne Bronze écartée. Conserver d'abord la ligne possédant le plus de mesures capteurs, puis la plus petite `source_row_number` en cas d'égalité, sans moyenner les mesures.
9. Publier toutes les tables Silver dans une transaction complète uniquement si les contrôles bloquants réussissent.

## Contrôles bloquants proposés

- clé métier absente, dupliquée avec des valeurs conflictuelles ou non convertible ;
- machine inconnue ;
- incident lié inexistant ;
- incohérence machine-incident restante après alignement ;
- timestamp, booléen ou valeur numérique non convertible ;
- valeur hors d'un domaine explicitement contraint ;
- volume publié différent du bilan attendu `lu = écrit + écarté`.

## Validation de l'exécution

Le remplacement Bronze préalable et le passage à Silver sont exécutés sur PostgreSQL. L'implémentation comprend les quatre modèles métier, les trois modèles Ops, la migration `20260901_01`, la commande `indusense build-silver`, la publication transactionnelle et l'audit des anomalies. Les 29 tests réussissent, la compilation et le SQL Alembic hors ligne sont validés.

Le run `235a0dd3-9c39-48b0-9287-31d3aa5449c2` a lu 138 448 lignes Bronze et publié 137 102 lignes métier Silver : 15 machines, 1 245 incidents, 1 562 maintenances et 134 280 télémétries. Il a réaligné 503 maintenances, audité 1 346 doublons télémétriques écartés et conservé avec `NULL` 2 792 télémétries représentantes incomplètes. Les contrôles persistés trouvent zéro référence machine orpheline, zéro incohérence maintenance-incident, zéro clé télémétrique dupliquée et zéro colonne minimisée encore présente dans `silver.incident`.
