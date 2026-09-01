# Architecture cible de persistance SQLAlchemy

## Statut

Décision d’architecture initiale validée le 31 août 2026 et contrat Bronze remplacé le 1er septembre 2026.

Le code, les modèles ORM et la migration initiale décrivent quatre grains Bronze alignés sur `machine.sql`, `releves_incidents.csv` et `telemetry.csv`. Les tests unitaires, la compilation et la génération SQL Alembic hors ligne sont validés. La base de développement a été recréée, la migration remplacée a été appliquée et les trois sources ont été ingérées le 1er septembre 2026.

Le modèle Silver, sa migration `20260901_01`, ses tables de traçabilité Ops et la commande `indusense build-silver` sont implémentés. La migration et la publication transactionnelle ont été exécutées sur PostgreSQL le 1er septembre 2026, puis contrôlées par des requêtes en lecture seule.

## Objectif

Mettre en place progressivement la persistance du dataset Bronze Indusense dans PostgreSQL, sans modifier les fichiers sources ni anticiper la transformation Silver ou Gold.

## Décisions retenues

1. La première implémentation couvre uniquement le Bronze et le suivi opérationnel des ingestions.
2. PostgreSQL sépare les données dans les schémas `bronze` et `ops`.
3. Les valeurs métier Bronze sont conservées sous forme de texte afin de préserver la fidélité à la source.
4. Une table brute correspond à chaque grain logique reçu. `machine.sql` alimente donc deux tables Bronze dans un même lot et une même transaction.
5. Le fichier SQL source n'est pas exécuté : seuls les blocs contrôlés `INSERT INTO machine` et `INSERT INTO maintenance` sont extraits.
6. Alembic est le seul mécanisme de création et d’évolution du schéma ; l’application n’utilise pas `Base.metadata.create_all()` pour gérer la base.
7. Une commande CLI orchestre l’ingestion des trois fichiers Bronze et les quatre tables cibles.
8. Le notebook Bronze historique n'est pas modifié dans cette étape et ne constitue plus une validation du nouveau contrat.
9. Chaque table ORM est déclarée dans un module Python dédié afin de garder la correspondance avec sa source explicite.

## Organisation cible du code

```text
indusense/
├── alembic.ini
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── src/indusense/
│   ├── cli.py
│   ├── db/
│   │   ├── base.py
│   │   ├── config.py
│   │   ├── engine.py
│   │   ├── session.py
│   │   └── models/
│   │       ├── bronze/
│   │       │   ├── incident_raw.py
│   │       │   ├── machine_raw.py
│   │       │   ├── maintenance_raw.py
│   │       │   └── telemetry_raw.py
│   │       └── ops/
│   │           └── ingestion_batch.py
│   └── ingestion/
│       └── bronze.py
└── tests/
    ├── unit/
    └── integration/
```

## Modèle PostgreSQL cible initial

```text
PostgreSQL
├── bronze
│   ├── machine_raw
│   ├── maintenance_raw
│   ├── incident_raw
│   └── telemetry_raw
└── ops
    └── ingestion_batch
```

Chaque ligne Bronze conserve les colonnes sources ainsi que `batch_id`, `source_row_number`, `record_hash` et `ingested_at`.

Les colonnes issues des fichiers sources sont déclarées en `Text` et non nulles. Une valeur CSV vide devra être lue comme une chaîne vide afin de préserver la différence entre une cellule présente mais vide et une colonne absente. Les colonnes techniques utilisent des types adaptés : clé interne `BigInteger`, lot `UUID`, numéro de ligne `Integer`, empreinte `String(64)` et date d’ingestion avec fuseau horaire.

La paire `(batch_id, source_row_number)` est unique dans chaque table Bronze. `record_hash` n’est volontairement pas unique : deux lignes identiques présentes dans la source doivent rester deux enregistrements Bronze distincts.

`ops.ingestion_batch` conserve au minimum l’identifiant du lot, le fichier source, son empreinte SHA-256, les dates de début et de fin, le statut, le nombre de lignes et une éventuelle erreur technique.

## Flux d’ingestion cible

1. Lire le fichier sans le modifier.
2. Calculer son empreinte SHA-256.
3. Créer le lot dans `ops.ingestion_batch`.
4. Lire et empreinter chaque ligne.
5. Insérer les lignes en lot dans la ou les tables Bronze correspondantes.
6. Vérifier les volumes écrits.
7. Valider la transaction et marquer le lot comme terminé.
8. En cas d’erreur, annuler la transaction et tracer l’échec.

L’ingestion est idempotente : rejouer le même fichier avec la même version du pipeline ne doit pas créer de doublons. Les doublons présents dans les sources, notamment en télémétrie, restent néanmoins conservés comme données Bronze.

## Frontières de responsabilité

- les lecteurs Python contrôlés extraient les lignes CSV et les deux blocs `INSERT` attendus ;
- SQLAlchemy décrit les tables et réalise les écritures transactionnelles ;
- psycopg transporte les échanges entre Python et PostgreSQL ;
- Alembic versionne le schéma ;
- PostgreSQL persiste les données et applique les contraintes ;
- Silver réalisera ultérieurement le typage, la normalisation et la séparation des entités ;
- Gold sera ajouté seulement pour un cas d’usage analytique validé.

## Validations restant à effectuer

- tester un rollback provoqué pendant une insertion ;
- ajouter des tests d’intégration PostgreSQL isolés du conteneur de développement ;
- définir la stratégie de gestion des lots échoués et de reprise.

## Validations du remplacement Bronze observées le 1er septembre 2026

- Les métadonnées SQLAlchemy enregistrent `machine_raw`, `maintenance_raw`, `incident_raw`, `telemetry_raw` et `ingestion_batch`.
- Le lecteur contrôlé de `machine.sql` extrait 15 machines et 1 562 maintenances sans exécuter le SQL source.
- La CLI résout les trois nouveaux chemins et associe `machine.sql` à deux tables dans un même lot.
- Les 17 tests unitaires réussissent.
- La compilation Python et la génération SQL Alembic hors ligne réussissent.
- Le SQL généré crée exactement les quatre tables Bronze attendues.
- Le volume PostgreSQL local a été supprimé et recréé sans supprimer le volume pgAdmin.
- La migration `20260831_01` est appliquée et constitue la révision Alembic courante `head`.
- L'ingestion persistée contient 15 machines, 1 562 maintenances, 1 245 incidents et 135 626 mesures de télémétrie.
- Trois lots sont au statut `completed`, aucun lot n'est au statut `failed` et les 90 maintenances proactives ont un `related_incident_id` Bronze vide.
- Un second lancement ignore les trois sources grâce à leur nom et leur empreinte SHA-256 ; les volumes restent inchangés.
- L'ancienne table `bronze.machine_maintenance_raw` n'existe plus.

## Validation PostgreSQL historique du 31 août 2026

- L'ancienne version de la migration Alembic `20260831_01` avait créé les schémas `bronze` et `ops`, trois tables brutes et `ops.ingestion_batch`.
- La première ingestion a chargé 115 lignes dans `machine_maintenance_raw`, 1 245 dans `incident_raw` et 135 626 dans `telemetry_raw`.
- Les trois lots sont au statut `completed`.
- Une seconde exécution a ignoré les trois fichiers car leur empreinte SHA-256 avait déjà été ingérée ; les volumes sont restés identiques.

Ces résultats décrivent l'ancien schéma présent dans la base avant son remplacement ; ils ne constituent pas la validation du schéma actuellement déployé.

## Validation Silver observée le 1er septembre 2026

- La révision Alembic active est `20260901_01 (head)`.
- Le run `235a0dd3-9c39-48b0-9287-31d3aa5449c2` est au statut `completed`, sans message d'erreur, et référence les trois lots Bronze sources.
- Les tables Silver contiennent 15 machines, 1 245 incidents, 1 562 maintenances et 134 280 télémétries.
- Les 503 codes machine de maintenance concernés ont été réalignés sur la machine de l'incident lié.
- Les 1 346 doublons techniques de télémétrie ont été écartés et audités ; aucune clé `(machine_code, measured_at)` n'est dupliquée en Silver.
- Les 2 792 télémétries représentantes possédant au moins une mesure absente sont conservées avec `NULL` et un avertissement d'audit.
- Aucun incident, aucune maintenance et aucune télémétrie ne référence une machine absente.
- Aucune maintenance liée ne conserve un code machine différent de celui de son incident.
- `operator_name`, `operator_badge`, `shift` et `comment` sont absentes de `silver.incident`.

Comme la révision initiale conservait l'identifiant `20260831_01`, la base existante ne pouvait pas rejouer son nouveau contenu. Le passage « annule et remplace » a donc recréé explicitement la base de développement avant `alembic upgrade head`. Cette destruction a concerné uniquement le volume PostgreSQL `pg-db-data` ; le volume pgAdmin `pg-gui-data` a été préservé.
