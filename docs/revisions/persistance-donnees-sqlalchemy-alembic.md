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

L'implémentation Bronze du 31 août comportait `machine_maintenance_raw`, `incident_raw` et `telemetry_raw`. Elle conservait le grain mixte de l'ancien `machine.csv`. Depuis l'arrivée de la source de référence `machine.sql`, cette structure a été remplacée dans le code, la migration initiale et PostgreSQL par `machine_raw`, `maintenance_raw`, `incident_raw` et `telemetry_raw`, sans modifier les valeurs reçues.

La convention reste un fichier Python par modèle et un module `ingestion_batch.py` dans `db/models/ops/`. Les colonnes sources sont explicites, en `Text` et non nulles ; les cellules CSV vides restent donc des chaînes vides pendant la lecture. La paire `(batch_id, source_row_number)` est unique dans chaque table, tandis que `record_hash` ne l'est pas afin de conserver les doublons réellement présents dans les sources.

Les modèles sont enregistrés dans `Base.metadata` et testés indépendamment de PostgreSQL. Cette validation confirme leur structure Python ; elle ne prouve pas encore que les schémas et tables existent dans la base. La création réelle reste réservée à une migration Alembic relue puis appliquée explicitement.

### Validation PostgreSQL historique et remplacement Bronze

L'ancienne version de la migration initiale `20260831_01` avait été appliquée sur PostgreSQL local : elle avait créé les schémas `bronze` et `ops`, les tables `machine_maintenance_raw`, `incident_raw`, `telemetry_raw` et `ingestion_batch`.

La commande `indusense ingest-bronze` lit les trois CSV avec `csv.DictReader`, conserve les cellules vides sous forme de chaînes vides, calcule l’empreinte SHA-256 du fichier et celle de chaque ligne, puis écrit les lignes en transaction. Un lot est créé dans `ops.ingestion_batch` avant l’écriture ; il passe à `completed` avec son volume ou à `failed` avec un message d’erreur et une date de fin.

L’**idempotence** signifie qu’une seconde exécution avec le même fichier ne duplique pas les données. Ici, la commande retrouve un lot terminé ayant le même nom de fichier et la même empreinte SHA-256, puis ignore la source. La validation observée a conservé 115 lignes machine-maintenance, 1 245 incidents et 135 626 mesures de télémétrie après cette seconde exécution.

Une idempotence validée ne remplace pas un test de rollback : il reste à provoquer une erreur pendant une insertion et à vérifier qu’aucune ligne Bronze partielle ne subsiste.

Le remplacement du 1er septembre introduit quatre modèles ORM et un lecteur contrôlé de `machine.sql`. Le fichier SQL n'est pas exécuté : ses blocs `INSERT INTO machine` et `INSERT INTO maintenance` sont extraits, puis leurs 15 et 1 562 lignes sont chargées sous un même `batch_id` et dans une même transaction. Les 17 tests unitaires, la compilation et la génération SQL Alembic hors ligne sont validés.

La migration initiale remplacée conserve l'identifiant `20260831_01`. Comme une base ayant déjà enregistré cette révision ne rejoue pas son contenu avec un simple `alembic upgrade head`, le volume PostgreSQL `pg-db-data` a été supprimé et recréé après autorisation ; le volume pgAdmin a été préservé. La migration est désormais à `head`.

La première ingestion du nouveau Bronze contient 15 machines, 1 562 maintenances, 1 245 incidents et 135 626 mesures de télémétrie. Les trois lots sont `completed`, aucun n'est `failed`, les 90 maintenances proactives conservent un identifiant d'incident vide et l'ancienne table mixte est absente. Un second lancement ignore les trois sources sans modifier les volumes, ce qui valide l'idempotence sur ces fichiers.

### Notebook de construction et d'ingestion Bronze

Le notebook `indusense/build-data-bronze.ipynb` documente l'ancienne mise en place Bronze. Il n'a pas été modifié pendant le remplacement des modèles et ne doit plus être utilisé comme validation du contrat courant tant qu'une adaptation distincte n'a pas été discutée.

Le contrôle PostgreSQL y est volontairement optionnel (`VALIDER_POSTGRESQL = False`). Cette précaution évite qu'une exécution globale du notebook crée ou modifie des données. Après avoir configuré les variables `DB_*` et appliqué la migration, l'utilisateur peut passer cette variable à `True` pour lire les trois volumes attendus. L'écriture reste une action explicite dans le terminal : `uv run indusense ingest-bronze --source all`.

### Passer d'un grain Bronze mixte à un modèle relationnel Silver

La conception Silver commence par fixer le **grain** de chaque table, c'est-à-dire ce que représente exactement une ligne. Une source Bronze peut volontairement mélanger plusieurs grains pour rester fidèle au fichier reçu ; Silver sépare alors le référentiel machine des événements de maintenance, des incidents et des mesures de télémétrie.

Une clé étrangère garantit que la valeur référencée existe dans la table cible. Elle ne garantit pas automatiquement une règle portant sur plusieurs colonnes. Par exemple, une maintenance peut référencer un identifiant d'incident existant tout en appartenant à une autre machine. Une telle situation doit être qualifiée avec la source d'autorité et le métier avant de devenir une règle du modèle cible.

L'analyse de `machine.csv` montrait que `related_incident_id` était systématiquement renseigné pour les maintenances réactives et jamais pour les maintenances proactives. Le formateur a ensuite confirmé un bug de création de ce fichier et désigné `machine.sql` comme source faisant foi. Le profil de cette source contient 1 562 maintenances : 90 proactives sans lien et 1 472 réactives avec un lien. Tous les identifiants référencés existent, mais 503 liens, soit 34,17 %, associent deux machines différentes. Par ailleurs, 1 057 incidents distincts sont référencés et un même incident peut être lié à trois maintenances au maximum.

Le schéma SQL déclare `related_incident_id` comme un simple `VARCHAR(16)` nullable, sans clé étrangère vers les incidents ni contrainte de même machine. La règle de réalignement envisagée utilise la table `machine` comme référentiel canonique : `incident.machine_id` doit référencer un `machine.machine_code` existant, puis ce code est reporté sur la maintenance liée par `related_incident_id`. Les maintenances proactives, dépourvues d'incident lié, conservent leur `machine_code` source après validation dans le même référentiel.

La décision retenue est de conserver `machine.sql` et le Bronze tels qu'ils ont été reçus, puis de réaligner la clé machine pendant la transformation vers Silver. La maintenance conserve son code reçu dans `source_machine_code` et utilise comme `machine_code` Silver celui de l'incident lié. Le contrôle final attendu est zéro maintenance liée dont la machine diffère de celle de son incident.

Le sens inverse serait ambigu : 363 incidents sont reliés à des maintenances portant plusieurs codes machine. Reporter les codes des maintenances vers l'incident imposerait donc un choix arbitraire.

Le croisement des commentaires Bronze et des composants de maintenance montrait une cohérence textuelle dans le CSV défectueux, mais ne peut pas valider sa structure relationnelle. Les commentaires eux-mêmes restent absents de Silver conformément à la minimisation déjà décidée.

Le profil du CSV Bronze Indusense observé le 31 août 2026 montrait :

- 15 machines communes au référentiel, aux incidents et à la télémétrie ;
- des attributs de machine stables dans les 115 lignes machine-maintenance ;
- 115 identifiants de maintenance et 1 245 identifiants d'incident uniques ;
- 25 références maintenance-incident existantes, dont une associe la même machine des deux côtés et 24 relient deux machines différentes ;
- 1 340 couples télémétriques `(machine_id, timestamp)` répétés avec des mesures différentes.

Ces effectifs décrivent l'état du CSV analysé, pas la référence SQL. Le contrôle de `machine.sql` doit être conservé séparément afin de ne pas mélanger les deux populations : 115 maintenances dans le CSV contre 1 562 dans le SQL. La provenance doit être explicite dans les transformations et les résultats.

Ces répétitions de télémétrie ne sont pas identiques sur toutes les mesures, mais le métier confirme qu'elles sont des doublons techniques dus à l'occupation du bus de données. Les 1 340 groupes contiennent 2 686 lignes, soit 1 346 lignes excédentaires lorsqu'une seule représentante est conservée. Les écarts maximaux sont faibles : `0,063 °C`, `0,088 bar`, `0,064 V`, `0,088 rpm` et zéro pièce produite ; le maximum relatif à la moyenne du groupe reste inférieur à `0,15 %`. Silver impose donc l'unicité de `(machine_id, measured_at)` et trace les lignes écartées. La règle déterministe validée conserve la ligne la plus complète, puis la plus petite `source_row_number` en cas d'égalité, sans calculer de moyenne.

Le profil révèle également 2 828 lignes Bronze avec au moins un capteur absent : 894 températures, 995 pressions et 958 rotations, réparties sur les 15 machines. Silver conserve ces lignes avec `NULL` sur la mesure absente et un avertissement d'audit ; il ne remplace pas une absence par zéro et ne rejette pas les autres mesures valides de la ligne.

Une relation ORM avec `relationship()` facilite la navigation entre objets Python, mais la clé étrangère et les contraintes PostgreSQL restent les garanties d'intégrité. Les deux notions sont complémentaires et ne doivent pas être confondues.

### Ordre de mise en œuvre du passage Bronze vers Silver

Le contrat d'entrée Bronze est réaligné dans le code et PostgreSQL sur `machine.sql`, `releves_incidents.csv` et `telemetry.csv`. Les quatre tables brutes sont `machine_raw`, `maintenance_raw`, `incident_raw` et `telemetry_raw`. Pour Silver, le chargement complet et atomique est validé dans le contrat cible.

L'ordre recommandé est :

1. figer les sources Bronze, leur représentation et le mode de chargement complet ou incrémental ;
2. profiler les données et définir le contrat Silver : grain, colonnes, types, nullabilité, clés, cardinalités et règles de qualité ;
3. figer les transformations : alignement des codes machine depuis l'incident vers la maintenance liée, dédoublonnage stable, suppression des données opérateur et traitement des valeurs invalides ;
4. définir la traçabilité, l'idempotence, les audits de dédoublonnage, la quarantaine et les critères bloquants ;
5. créer les modèles ORM Silver et les tests de structure ;
6. créer et relire la migration Alembic du schéma Silver et des tables Ops nécessaires ;
7. implémenter le pipeline transactionnel Bronze vers Silver avec publication atomique ;
8. exécuter les tests unitaires, de migration, d'intégration et de qualité, puis seulement lancer le pipeline sur PostgreSQL et contrôler les volumes.

Les tests ne constituent pas uniquement une dernière étape : leurs cas et résultats attendus sont définis avec le contrat, puis implémentés au fur et à mesure du modèle, de la migration et du pipeline.

Le modèle cible a été validé le 1er septembre 2026. Tous les horodatages métier sont en UTC : les timestamps sans offset des CSV incidents et télémétrie sont interprétés directement en UTC, et non convertis depuis `Europe/Paris`. La machine n'est pas historisée dans cette première version, les indicateurs d'incident utilisent les noms anglais du contrat, la description de maintenance est conservée, toute anomalie bloquante annule la publication et le chargement Silver initial est complet et atomique.

L'implémentation Silver ajoute quatre modèles ORM métier, `ops.pipeline_run`, `ops.pipeline_run_source`, `ops.transformation_issue`, la migration `20260901_01` et la commande `indusense build-silver`. Les 29 tests, la compilation et la génération SQL Alembic hors ligne réussissent.

L'exécution PostgreSQL du 1er septembre 2026 est validée : le run `235a0dd3-9c39-48b0-9287-31d3aa5449c2` est `completed` sans erreur et référence les trois lots Bronze. Il a lu 138 448 lignes et publié 137 102 lignes métier : 15 machines, 1 245 incidents, 1 562 maintenances et 134 280 télémétries. L'audit contient 1 346 doublons techniques écartés et 2 792 télémétries conservées avec au moins un `NULL`, soit 4 138 avertissements. Les contrôles en base trouvent zéro référence machine orpheline, zéro divergence entre une maintenance liée et son incident, zéro doublon `(machine_code, measured_at)` et zéro colonne personnelle supprimée encore présente dans `silver.incident`.

Le notebook `build-data-silver.ipynb` retrace cette démarche en 17 cellules alternant Markdown et Python. Son exécution est volontairement en lecture seule : elle inspecte les modèles et la migration, relit le dernier run, vérifie les volumes et exécute les contrôles d'intégrité sans relancer la publication atomique.

La correspondance exacte avec les compétences C1 à C9 reste à confirmer avec le Kit candidat.

## Consulter les données Indusense dans pgAdmin

**pgAdmin** est une interface graphique d’administration de PostgreSQL. Dans l’environnement Docker d’Indusense, pgAdmin doit joindre PostgreSQL par le nom du service Docker `db`, et non par `localhost` : `localhost` désignerait le conteneur pgAdmin lui-même.

### Diagnostiquer des tables qui semblent vides

L'arbre d'objets et les onglets **View/Edit Data** de pgAdmin ne se mettent pas toujours à jour après un chargement exécuté depuis une autre application. Il faut distinguer une vue non rafraîchie d'une autre connexion PostgreSQL. Le contrôle fiable consiste à ouvrir **Query Tool** depuis la base `indusense` et à exécuter une requête qui affiche simultanément l'identité de la connexion et les volumes. Pour l'exécution Silver du 1er septembre 2026, la connexion applicative a confirmé la base `indusense`, le rôle `indusense-user`, le port `5432` et respectivement 15, 1 245, 1 562 et 134 280 lignes dans `silver.machine`, `silver.incident`, `silver.maintenance` et `silver.telemetry`.

Si la barre d'état indique par exemple **Total rows: 15 of 15** et **Successfully run**, mais qu'aucune grille n'est visible, les données sont bien présentes : le panneau **Data Output** est simplement replié sous l'éditeur SQL. Il faut saisir la fine barre de séparation horizontale située juste au-dessus de la barre d'état et la faire glisser vers le haut pour réafficher la grille des résultats.

Pour enregistrer la connexion depuis l’écran d’accueil de pgAdmin :

1. choisir **Ajouter un nouveau serveur** ;
2. dans **Général**, donner un nom libre, par exemple `Indusense` ;
3. dans **Connexion**, saisir `db` comme nom d’hôte et `5432` comme port ;
4. reprendre le nom de base, l’utilisateur et le mot de passe définis par `DB_NAME`, `DB_USER` et `DB_PASSWORD` dans la configuration `.docker` ;
5. enregistrer, puis développer **Servers > Indusense > Databases > [base] > Schemas**.

Les données ingérées se trouvent dans les tables du schéma `bronze` :

- `machine_raw` ;
- `maintenance_raw` ;
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
