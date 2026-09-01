# Persistance des données avec SQLAlchemy et Alembic

## Définition et objectif

**pandas** travaille principalement en mémoire : un `DataFrame` disparaît à la fin du programme s’il n’est pas enregistré. La **persistance** consiste à conserver durablement les données, par exemple dans une base de données, afin de pouvoir les relire lors d’une exécution ultérieure.

Un **SGBD** (*système de gestion de base de données*) est le logiciel qui stocke les données et permet de les interroger. PostgreSQL, MariaDB, MySQL, SQL Server et Oracle sont des SGBD relationnels. MongoDB est une base orientée documents et Cassandra une base NoSQL orientée colonnes larges.

Pour le TP, l’objectif sera de stocker durablement le dataset Bronze dans une base sans confondre trois responsabilités :

- pandas charge et manipule les données en mémoire ;
- SQLAlchemy relie le code Python à une base relationnelle ;
- **psycopg** est le pilote qui transporte les échanges entre Python et PostgreSQL ;
- le SGBD assure le stockage durable et l’exécution des requêtes.

L’URL SQLAlchemy utilisant ce pilote commence par `postgresql+psycopg://`. Une URL réelle peut contenir des secrets : elle doit venir de la configuration de l’environnement et ne doit pas être enregistrée dans Git.

## SQL, ORM et ODM

**SQL** (*Structured Query Language*) est le langage utilisé pour définir et interroger une base relationnelle.

Un **ORM** (*Object-Relational Mapper*) fait correspondre des objets du programme à des tables relationnelles. Avec SQLAlchemy, une classe Python peut représenter une table, un objet une ligne et un attribut une colonne. L’ORM produit ensuite les requêtes SQL nécessaires, mais il ne remplace ni le SGBD ni la nécessité de comprendre le modèle relationnel.

Un **ODM** (*Object-Document Mapper*) remplit un rôle voisin pour une base orientée documents. Il ne faut donc pas employer `ODM` comme synonyme général d’outil NoSQL : toutes les bases NoSQL ne stockent pas des documents.

Exemples d’ORM selon les langages ou écosystèmes :

- Python : SQLAlchemy ;
- PHP : Doctrine ou Propel ;
- Java : Hibernate, qui implémente notamment la spécification JPA ;
- JavaScript ou TypeScript : TypeORM.

## SQLAlchemy : les deux manières principales de travailler

SQLAlchemy propose notamment :

- **SQLAlchemy Core**, qui construit explicitement des tables et des requêtes SQL en Python ;
- **SQLAlchemy ORM**, qui ajoute une représentation des tables sous forme de classes et de relations entre objets.

Le flux général est le suivant :

1. le code Python crée ou manipule des objets ;
2. SQLAlchemy traduit les opérations en requêtes SQL adaptées au dialecte du SGBD ;
3. le SGBD exécute ces requêtes et conserve les données ;
4. SQLAlchemy reconstruit des objets Python à partir des résultats lus.

Une **session** SQLAlchemy représente une unité de travail avec la base. Elle suit les objets chargés ou modifiés. Un `commit` valide durablement la transaction ; un `rollback` annule les changements non validés si une erreur survient.

L’**Engine** SQLAlchemy gère la configuration des connexions et leur réutilisation dans un **pool de connexions**. Il est normalement créé une fois par processus. Les sessions restent courtes et ne doivent pas englober la lecture d’un gros fichier ou un long calcul.

## DDL, DML et migrations

Le **DDL** (*Data Definition Language*, ou LDD en français) regroupe les instructions qui définissent la structure : `CREATE TABLE`, `ALTER TABLE` ou `DROP TABLE`.

Le **DML** (*Data Manipulation Language*, ou LMD en français) agit sur les données : `INSERT`, `UPDATE` et `DELETE`. La lecture avec `SELECT` est parfois classée séparément dans le **DQL** (*Data Query Language*).

Une **migration** est une modification versionnée du schéma de la base. **Alembic** est l’outil de migration couramment associé à SQLAlchemy. Il permet de faire évoluer le schéma de manière explicite et reproductible, par exemple en ajoutant une table ou une colonne, sans recréer manuellement toute la base.

Une migration générée automatiquement doit toujours être relue : Alembic détecte des différences de schéma, mais ne peut pas deviner toutes les intentions métier ni garantir qu’une transformation de données est sans risque.

## Modéliser les relations et les cardinalités

Une **relation** décrit le lien entre deux entités. La **cardinalité** indique combien d’occurrences de chaque entité peuvent participer à ce lien.

Dans l’exemple du cours :

- une machine peut avoir de zéro à plusieurs incidents : relation `OneToMany` du point de vue de `machine` ;
- chaque incident appartient à une seule machine : relation `ManyToOne` du point de vue de `incident`.

En base relationnelle, la table `incident` porte généralement une **clé étrangère** `machine_id` qui référence la **clé primaire** de la table `machine`.

Les principales cardinalités sont :

- `OneToOne` : une occurrence correspond à au plus une occurrence de l’autre entité ;
- `OneToMany` / `ManyToOne` : un parent peut être lié à plusieurs enfants, chaque enfant ayant un parent ;
- `ManyToMany` : plusieurs occurrences de chaque côté peuvent être liées, généralement par une table d’association.

Le chargement d’une relation peut être **lazy** : les données liées ne sont demandées que lorsqu’on y accède. Il peut être **eager** : elles sont chargées avec la requête initiale. Le choix influence le nombre de requêtes, la mémoire utilisée et les performances.

Le chargement lazy non maîtrisé peut provoquer le problème **N+1** : une première requête charge une liste de machines, puis une requête supplémentaire est envoyée pour chacune afin de récupérer ses incidents. `selectinload` ou `joinedload` peuvent réduire les allers-retours, mais leur pertinence doit être vérifiée selon le volume réellement chargé.

## Organisation recommandée dans PostgreSQL

Un **schéma PostgreSQL** est un espace de noms qui regroupe des tables dans une même base. La ressource du cours recommande de séparer :

- `bronze` pour les données brutes, les lots et la quarantaine ;
- `silver` pour les entités normalisées et contrôlées ;
- `gold` pour les features, labels et résultats de qualité ;
- `ops` pour les exécutions, audits et informations opérationnelles.

Cette séparation clarifie les responsabilités et permet d’accorder des droits différents selon les usages. Elle ne signifie pas que toutes les données doivent obligatoirement être en tables : des volumes analytiques importants peuvent rester en Parquet, avec leur emplacement et leur lignée référencés dans PostgreSQL.

## Démarche pour ingérer un dataset Bronze

1. Définir le rôle exact de la base et ce qui doit rester fidèle à la source Bronze.
2. Concevoir le schéma : tables, colonnes, types, clés primaires, clés étrangères et contraintes.
3. Déclarer les modèles SQLAlchemy correspondant à ce schéma.
4. Créer et relire une migration Alembic, puis l’appliquer à la base ciblée.
5. Charger le dataset source sans le modifier silencieusement.
6. Insérer les lignes dans une transaction et valider avec `commit` seulement si l’ensemble est cohérent.
7. Contrôler le résultat par des requêtes de comptage, des vérifications de contraintes et un échantillon relu depuis la base.

Le choix des types SQL doit respecter la fidélité du Bronze définie pour le projet. Si la consigne impose de conserver les valeurs brutes sous forme de texte, le typage métier sera réalisé plus tard dans Silver.

Une ingestion doit être **idempotente** : rejouer le même lot avec la même version du pipeline ne doit ni créer de doublons ni produire un résultat différent. Elle conserve notamment l’empreinte de la source, l’identifiant du lot, la date d’ingestion, le numéro de ligne source et le statut des contrôles.

## Erreurs fréquentes et bonnes pratiques

- Confondre pandas et une base : un `DataFrame` n’assure pas à lui seul la persistance.
- Confondre SQLAlchemy et le SGBD : SQLAlchemy communique avec le SGBD, mais ne stocke pas lui-même les données.
- Appeler `create_all()` à chaque évolution et croire que cela remplace les migrations : cette méthode ne décrit pas un historique versionné des changements.
- Valider trop tôt avec `commit` : regrouper les opérations cohérentes dans une transaction et prévoir un `rollback` en cas d’échec.
- Définir une relation Python sans clé étrangère cohérente dans la base.
- Créer un `Engine` ou ouvrir une transaction pour chaque ligne importée.
- Insérer une télémétrie volumineuse ligne par ligne avec l’ORM au lieu de mesurer une stratégie d’écriture en lot.
- Utiliser systématiquement le chargement eager et récupérer inutilement un grand volume de données liées.
- Laisser un chargement lazy produire un problème N+1 sans contrôler le nombre de requêtes.
- Faire confiance sans relecture à une migration générée automatiquement.
- Transformer silencieusement les données Bronze pendant l’ingestion et perdre la fidélité à la source.

## Points à retenir pour le QCM

- La persistance conserve les données au-delà de l’exécution du programme.
- Un SGBD relationnel stocke des tables reliées par des clés.
- Un ORM fait correspondre objets et tables ; un ODM concerne les documents.
- SQLAlchemy est une boîte à outils SQL et un ORM Python.
- psycopg est le pilote Python utilisé pour communiquer avec PostgreSQL.
- L’Engine gère les connexions ; la Session porte une unité de travail transactionnelle courte.
- Alembic versionne les évolutions du schéma SQLAlchemy.
- DDL/LDD décrit la structure ; DML/LMD modifie les données.
- `OneToMany` et `ManyToOne` sont deux points de vue sur la même relation.
- `lazy` et `eager` décrivent le moment où les données liées sont chargées.
- Une ingestion idempotente peut être rejouée sans dupliquer ni altérer son résultat.

## Points à savoir expliquer lors de la soutenance

- Pourquoi une base est nécessaire alors que pandas travaille déjà avec les données.
- Comment le modèle Python correspond aux tables, colonnes et relations SQL.
- Pourquoi les migrations doivent être versionnées et relues.
- Comment une transaction protège la cohérence d’une ingestion.
- Comment vérifier que toutes les lignes Bronze attendues ont été stockées sans transformation non prévue.

## Mise en pratique Indusense : socle SQLAlchemy

Le socle validé le 31 août 2026 sépare les responsabilités avant de définir les tables métier :

- `DatabaseSettings` lit et valide `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST` et `DB_PORT` ;
- `URL.create` construit l’URL PostgreSQL sans concaténer manuellement le mot de passe ;
- `create_database_engine` crée l’Engine avec `pool_pre_ping=True` ;
- `create_session_factory` prépare des sessions courtes ;
- `Base` porte une convention de nommage stable pour les futures contraintes ;
- `indusense db-check` exécute une lecture minimale pour vérifier la base et l’utilisateur connectés ;
- Alembic connaît `Base.metadata`, mais aucune révision n’est créée avant la validation des modèles Bronze et Ops.

Cette étape confirme la connectivité et l’organisation technique. Elle ne crée encore aucun schéma, aucune table et n’ingère aucune donnée.

## Concevoir un modèle ORM Bronze avant la première migration

Deux correspondances différentes ne doivent pas être confondues :

- **un fichier source = une table Bronze** est une décision de modélisation des données : elle préserve le grain et la structure de chaque source sans normalisation prématurée ;
- **un fichier Python = une classe ORM = une table** est une convention d’organisation du code : elle peut faciliter la lecture, mais ne change pas le schéma PostgreSQL produit.

Pour une couche Bronze fidèle à la source, le modèle ORM reste volontairement pauvre en logique métier :

- chaque colonne source est conservée sous son nom d’origine ;
- les valeurs métier peuvent être stockées en `Text` lorsqu’aucune conversion Bronze n’est autorisée ;
- des colonnes techniques typées assurent la traçabilité, par exemple une clé primaire interne, `batch_id`, `source_row_number`, `record_hash` et `ingested_at` ;
- les relations métier, comme machine vers incidents, ne sont pas imposées à ce stade si la source ne garantit pas leur intégrité ;
- une contrainte d’unicité ne doit pas supprimer les doublons réellement présents dans le fichier source.

Les trois tables Bronze envisagées pour Indusense restent `machine_maintenance_raw`, `incident_raw` et `telemetry_raw`. La table `machine_maintenance_raw` conserve volontairement le grain mixte du fichier `machine.csv` ; séparer machine et maintenance serait déjà une normalisation Silver.

Pour Indusense, la convention validée est un fichier Python par modèle : trois modules dans `db/models/bronze/` et un module `ingestion_batch.py` dans `db/models/ops/`. Les colonnes sources sont explicites, en `Text` et non nulles ; les cellules CSV vides devront donc rester des chaînes vides pendant la lecture. La paire `(batch_id, source_row_number)` est unique, tandis que `record_hash` ne l’est pas afin de conserver les doublons réellement présents dans les sources.

Les modèles sont enregistrés dans `Base.metadata` et testés indépendamment de PostgreSQL. Cette validation confirme leur structure Python ; elle ne prouve pas encore que les schémas et tables existent dans la base. La création réelle reste réservée à une migration Alembic relue puis appliquée explicitement.

### Validation PostgreSQL et ingestion Bronze Indusense

La migration initiale `20260831_01` a été appliquée sur PostgreSQL local : elle a créé les schémas `bronze` et `ops`, les tables `machine_maintenance_raw`, `incident_raw`, `telemetry_raw` et `ingestion_batch`.

La commande `indusense ingest-bronze` lit les trois CSV avec `csv.DictReader`, conserve les cellules vides sous forme de chaînes vides, calcule l’empreinte SHA-256 du fichier et celle de chaque ligne, puis écrit les lignes en transaction. Un lot est créé dans `ops.ingestion_batch` avant l’écriture ; il passe à `completed` avec son volume ou à `failed` avec un message d’erreur et une date de fin.

L’**idempotence** signifie qu’une seconde exécution avec le même fichier ne duplique pas les données. Ici, la commande retrouve un lot terminé ayant le même nom de fichier et la même empreinte SHA-256, puis ignore la source. La validation observée a conservé 115 lignes machine-maintenance, 1 245 incidents et 135 626 mesures de télémétrie après cette seconde exécution.

Une idempotence validée ne remplace pas un test de rollback : il reste à provoquer une erreur pendant une insertion et à vérifier qu’aucune ligne Bronze partielle ne subsiste.

### Notebook de construction et d'ingestion Bronze

Le notebook `indusense/build-data-bronze.ipynb` est une démonstration reproductible de la mise en place Bronze. Il alterne une explication métier et une cellule de vérification : inventaire des CSV, inspection des classes ORM, présence de la migration, puis calcul des empreintes SHA-256 sans modification de la source.

Le contrôle PostgreSQL y est volontairement optionnel (`VALIDER_POSTGRESQL = False`). Cette précaution évite qu'une exécution globale du notebook crée ou modifie des données. Après avoir configuré les variables `DB_*` et appliqué la migration, l'utilisateur peut passer cette variable à `True` pour lire les trois volumes attendus. L'écriture reste une action explicite dans le terminal : `uv run indusense ingest-bronze --source all`.

### Passer d'un grain Bronze mixte à un modèle relationnel Silver

La conception Silver commence par fixer le **grain** de chaque table, c'est-à-dire ce que représente exactement une ligne. Une source Bronze peut volontairement mélanger plusieurs grains pour rester fidèle au fichier reçu ; Silver sépare alors le référentiel machine des événements de maintenance, des incidents et des mesures de télémétrie.

Une clé étrangère garantit que la valeur référencée existe dans la table cible. Elle ne garantit pas automatiquement une règle portant sur plusieurs colonnes. Par exemple, une maintenance peut référencer un identifiant d'incident existant tout en appartenant à une autre machine. Cela ne constitue pas automatiquement une anomalie : une relation inter-machine peut avoir un sens fonctionnel. Tant que le métier ne l'interdit pas, la base doit imposer seulement l'existence de l'incident par une clé étrangère simple et conserver la machine propre à chaque événement.

L'analyse détaillée confirme que `related_incident_id` est systématiquement renseigné pour les maintenances réactives et jamais pour les maintenances proactives. La clé étrangère simple et nullable vers `silver.incident.incident_id` est donc conservée. Elle formalise une relation déclarée par la source, sans prétendre que l'incident est la cause directe de la maintenance ni qu'il doit concerner la même machine. Cette sémantique reste à valider avec le métier.

Le croisement des commentaires Bronze et des composants de maintenance renforce cette décision : les descriptions des 25 maintenances réactives mentionnent explicitement leur incident lié et les couples composant–symptôme sont plus cohérents que des appariements aléatoires. La relation doit donc être persistée. Les commentaires eux-mêmes restent absents de Silver conformément à la minimisation déjà décidée ; ils ne sont pas nécessaires pour matérialiser la clé étrangère.

Le profil Bronze Indusense observé le 31 août 2026 montre :

- 15 machines communes au référentiel, aux incidents et à la télémétrie ;
- des attributs de machine stables dans les 115 lignes machine-maintenance ;
- 115 identifiants de maintenance et 1 245 identifiants d'incident uniques ;
- 25 références maintenance-incident existantes, dont une associe la même machine des deux côtés et 24 relient deux machines différentes ;
- 1 340 couples télémétriques `(machine_id, timestamp)` répétés avec des mesures différentes.

Ces répétitions de télémétrie ne sont pas des doublons exacts. La décision retenue est de conserver chaque mesure dans Silver avec une clé technique `telemetry_id` auto-incrémentée. `(machine_id, measured_at)` reste un index de recherche non unique. Une référence unique vers la ligne Bronze source devra empêcher qu'un rejeu du pipeline ne recrée la même mesure Silver. Le métier décidera ultérieurement si les mesures partageant un instant doivent être agrégées, distinguées par une information supplémentaire ou considérées comme des anomalies.

Une relation ORM avec `relationship()` facilite la navigation entre objets Python, mais la clé étrangère et les contraintes PostgreSQL restent les garanties d'intégrité. Les deux notions sont complémentaires et ne doivent pas être confondues.

La correspondance exacte avec les compétences C1 à C9 reste à confirmer avec le Kit candidat.

## Consulter les données Indusense dans pgAdmin

**pgAdmin** est une interface graphique d’administration de PostgreSQL. Dans l’environnement Docker d’Indusense, pgAdmin doit joindre PostgreSQL par le nom du service Docker `db`, et non par `localhost` : `localhost` désignerait le conteneur pgAdmin lui-même.

Pour enregistrer la connexion depuis l’écran d’accueil de pgAdmin :

1. choisir **Ajouter un nouveau serveur** ;
2. dans **Général**, donner un nom libre, par exemple `Indusense` ;
3. dans **Connexion**, saisir `db` comme nom d’hôte et `5432` comme port ;
4. reprendre le nom de base, l’utilisateur et le mot de passe définis par `DB_NAME`, `DB_USER` et `DB_PASSWORD` dans la configuration `.docker` ;
5. enregistrer, puis développer **Servers > Indusense > Databases > [base] > Schemas**.

Les données ingérées se trouvent dans les tables du schéma `bronze` :

- `machine_maintenance_raw` ;
- `incident_raw` ;
- `telemetry_raw`.

Le suivi des ingestions se trouve dans `ops.ingestion_batch`. Pour afficher quelques lignes sans modifier les données, utiliser **Query Tool** et exécuter une requête `SELECT` limitée, par exemple :

```sql
SELECT *
FROM bronze.incident_raw
LIMIT 100;
```

`SELECT` lit les données et `LIMIT 100` limite le résultat aux cent premières lignes. Pour un premier contrôle, éviter `UPDATE`, `DELETE`, `INSERT`, `TRUNCATE` et `DROP`, qui changent ou suppriment des données ou leur structure.

## Pour aller plus loin

- [SQLAlchemy — ORM Quick Start](https://docs.sqlalchemy.org/en/20/orm/quickstart.html) : correspondance entre classes Python, tables et sessions.
- [Alembic — Tutoriel](https://alembic.sqlalchemy.org/en/latest/tutorial.html) : migrations versionnées et reproductibles.
- [PostgreSQL — Transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html) : `commit`, `rollback` et cohérence des écritures.
