# Architecture cible de persistance SQLAlchemy

## Statut

Décision d’architecture validée le 31 août 2026.

Le socle technique est désormais implémenté : dépendances verrouillées, configuration par variables d’environnement, base déclarative, Engine, fabrique de sessions, commande de contrôle PostgreSQL et environnement Alembic. Les modèles Bronze et Ops, la première migration et l’ingestion restent à réaliser dans les prochaines étapes validées.

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
│   │       ├── bronze.py
│   │       └── ops.py
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

- ajouter et verrouiller les dépendances SQLAlchemy, psycopg et Alembic ;
- vérifier leur compatibilité avec la version Python du projet ;
- créer puis relire la migration initiale ;
- tester une ingestion complète, un rollback et la réexécution du même lot ;
- vérifier que les trois fichiers sources restent inchangés.
