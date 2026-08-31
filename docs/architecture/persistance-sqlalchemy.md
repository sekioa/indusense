# Architecture cible de persistance SQLAlchemy

## Statut

Décision d’architecture validée le 31 août 2026.

Le socle technique, les modèles ORM initiaux, la première migration et l’ingestion Bronze sont implémentés et validés sur PostgreSQL local : dépendances verrouillées, configuration par variables d’environnement, base déclarative, Engine, fabrique de sessions, commande de contrôle PostgreSQL, environnement Alembic, trois modèles Bronze et un modèle de suivi Ops.

## Objectif

Mettre en place progressivement la persistance du dataset Bronze Indusense dans PostgreSQL, sans modifier les fichiers sources ni anticiper la transformation Silver ou Gold.

## Décisions retenues

1. La première implémentation couvre uniquement le Bronze et le suivi opérationnel des ingestions.
2. PostgreSQL sépare les données dans les schémas `bronze` et `ops`.
3. Les valeurs métier Bronze sont conservées sous forme de texte afin de préserver la fidélité à la source.
4. Une table brute correspond à chaque fichier source.
5. Le grain mixte de `machine.csv` est conservé dans `bronze.machine_maintenance_raw` ; sa normalisation en machines et maintenances appartient au Silver.
6. Alembic est le seul mécanisme de création et d’évolution du schéma ; l’application n’utilise pas `Base.metadata.create_all()` pour gérer la base.
7. Une commande CLI orchestre l’ingestion des trois fichiers Bronze.
8. Les notebooks existants ne sont pas modifiés par cette mise en place.
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
│   │       │   ├── machine_maintenance_raw.py
│   │       │   └── telemetry_raw.py
│   │       └── ops/
│   │           └── ingestion_batch.py
│   └── ingestion/
│       ├── bronze.py
│       ├── hashing.py
│       └── readers.py
└── tests/
    ├── unit/
    └── integration/
```

## Modèle PostgreSQL cible initial

```text
PostgreSQL
├── bronze
│   ├── machine_maintenance_raw
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
5. Insérer les lignes en lot dans la table Bronze correspondante.
6. Vérifier les volumes écrits.
7. Valider la transaction et marquer le lot comme terminé.
8. En cas d’erreur, annuler la transaction et tracer l’échec.

L’ingestion est idempotente : rejouer le même fichier avec la même version du pipeline ne doit pas créer de doublons. Les doublons présents dans les sources, notamment en télémétrie, restent néanmoins conservés comme données Bronze.

## Frontières de responsabilité

- pandas lit les fichiers et effectue les contrôles préparatoires en mémoire ;
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

## Validations observées le 31 août 2026

- La migration Alembic `20260831_01` a créé les schémas `bronze` et `ops`, les trois tables brutes et `ops.ingestion_batch`.
- La première ingestion a chargé 115 lignes dans `machine_maintenance_raw`, 1 245 dans `incident_raw` et 135 626 dans `telemetry_raw`.
- Les trois lots sont au statut `completed`.
- Une seconde exécution a ignoré les trois fichiers car leur empreinte SHA-256 avait déjà été ingérée ; les volumes sont restés identiques.
