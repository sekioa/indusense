# Persister les données avec SQLAlchemy, Alembic, psycopg et PostgreSQL

## Objectif

Ce guide explique, étape par étape, comment persister les données des couches bronze, silver et gold dans PostgreSQL avec :

- **SQLAlchemy** pour décrire les tables, écrire des requêtes et manipuler les données en Python ;
- **psycopg** comme pilote PostgreSQL ;
- **Alembic** pour versionner et appliquer les changements de structure de la base.

Le conteneur PostgreSQL est fourni. Ce document ne lance pas le conteneur, ne crée pas de tables et ne contient pas de résultat d’exécution : il fournit la démarche, les choix à faire et les livrables attendus pour les stagiaires.

## 1. Les idées clés, expliquées simplement

| Terme | Définition | Analogie |
|---|---|---|
| **PostgreSQL** | Le système qui stocke durablement les données dans des tables, applique des contraintes et exécute du SQL. | Un entrepôt avec des rayonnages, des règles d’accès et un inventaire. |
| **psycopg** | Le pilote Python qui sait communiquer avec PostgreSQL. | Le chauffeur-livreur qui parle à la fois Python et PostgreSQL. |
| **Dialecte SQLAlchemy** | L’adaptateur qui indique à SQLAlchemy comment parler au pilote et au moteur de base précis. | Un traducteur spécialisé dans le vocabulaire PostgreSQL. |
| **ORM** (*Object-Relational Mapper*) | Une couche qui associe une classe Python à une table et un objet Python à une ligne. | Une fiche de catalogue Python correspondant à un article rangé dans l’entrepôt. |
| **Modèle ORM** | La classe Python qui décrit les colonnes, contraintes et relations d’une table. | Le plan du rayonnage : quelles cases existent, ce qu’elles contiennent et quelles règles elles respectent. |
| **Engine** | L’objet SQLAlchemy qui gère la manière de se connecter à la base et son pool de connexions. | Le standard téléphonique qui organise les appels vers l’entrepôt. |
| **Session** | L’espace de travail où l’application lit, crée, modifie ou supprime des objets avant de valider une transaction. | Un panier de préparation : rien n’est définitivement rangé tant que l’opération n’est pas validée. |
| **Transaction** | Un groupe d’opérations qui réussissent toutes ou sont toutes annulées. | Un virement bancaire : on ne veut jamais débiter sans créditer. |
| **Migration** | Un script versionné qui fait évoluer le schéma de la base, par exemple en ajoutant une table ou un index. | Une notice de travaux numérotée pour réaménager l’entrepôt sans perdre son contenu. |
| **Révision Alembic** | Une migration identifiée, reliée à la migration précédente. | Une page numérotée dans l’historique des travaux. |

## 2. Pourquoi utiliser un ORM ?

Sans ORM, le développeur écrit du SQL sous forme de chaînes de caractères dans chaque partie de l’application. C’est parfois approprié, mais devient difficile à maintenir lorsque le nombre de tables, de relations et de règles augmente.

### Caractéristiques principales d’un ORM

1. **Mapping classe ↔ table** : une classe Python décrit une table ; ses attributs décrivent les colonnes.
2. **Mapping objet ↔ ligne** : une instance Python représente une ligne chargée ou à insérer.
3. **Typage explicite** : les types Python et SQL sont rapprochés, par exemple `datetime` / `TIMESTAMP`, `Decimal` / `NUMERIC`.
4. **Relations explicites** : les clés étrangères et relations entre objets rendent visibles les liens machine → incidents, maintenances et télémétrie.
5. **Requêtes composables** : SQLAlchemy construit des requêtes paramétrées sans concaténer des valeurs utilisateur dans du SQL.
6. **Unité de travail** : la session suit les objets modifiés et les regroupe dans une transaction.
7. **Portabilité raisonnée** : le code reste largement indépendant de la base, tout en permettant d’utiliser les fonctions propres à PostgreSQL lorsque nécessaire.

### Avantages pour le projet

- Un modèle de données lisible, centralisé et revu avec le code Python.
- Des contraintes métier visibles : clés primaires, clés étrangères, unicité, nullité, index et contrôles de domaine.
- Moins de duplication entre les scripts d’ingestion, l’API éventuelle et les tâches de préparation de données.
- Des transactions explicites qui évitent les écritures partielles.
- Des requêtes paramétrées qui réduisent le risque d’injection SQL.
- Une métadonnée SQLAlchemy utilisable directement par Alembic pour comparer le modèle attendu au schéma de la base.

### Ce que l’ORM ne remplace pas

L’ORM ne remplace ni la compréhension du SQL ni la modélisation des données. Les stagiaires doivent savoir lire le SQL généré, comprendre les index et vérifier le plan d’exécution des requêtes importantes.

Pour la télémétrie volumineuse, éviter une insertion ORM ligne par ligne : elle est simple à lire mais coûteuse à grande échelle. Préférer des écritures en lot, le SQLAlchemy Core ou un mécanisme PostgreSQL adapté, tout en gardant les modèles ORM, les contraintes et les migrations comme contrat de persistance.

## 3. Architecture de persistance recommandée

### 3.1 Séparer les schémas PostgreSQL

Utiliser des schémas PostgreSQL pour rendre les couches explicites :

| Schéma | Rôle |
|---|---|
| `bronze` | données brutes, métadonnées de lot et tables de quarantaine |
| `silver` | données normalisées, standardisées et dédoublonnées |
| `gold` | snapshots de features, labels d’arrêt, catalogue de features et résultats de qualité |
| `ops` | exécutions, journaux, audits, migrations applicatives et informations opérationnelles |

Les droits PostgreSQL doivent suivre cette séparation : une tâche de lecture analytique ne doit pas posséder les mêmes droits qu’un processus d’écriture de migration.

### 3.2 Structure de projet suggérée

```text
indusense/
├── pyproject.toml
├── alembic.ini
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── src/indusense/
│   ├── db/
│   │   ├── config.py
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models/
│   │       ├── machine.py
│   │       ├── incident.py
│   │       ├── maintenance.py
│   │       ├── telemetry.py
│   │       └── pipeline.py
│   ├── repositories/
│   ├── services/
│   └── ingestion/
└── tests/
    ├── db/
    └── migrations/
```

Le nom exact des dossiers peut évoluer, mais les modèles, la configuration de connexion, les migrations et les tests doivent rester clairement séparés.

### 3.3 Entités à modéliser

Commencer avec les entités correspondant aux roadmaps précédentes :

- machine ;
- incident ;
- maintenance ;
- télémétrie ;
- lot d’ingestion et enregistrement de quarantaine ;
- snapshot gold de features et label d’arrêt ;
- exécution de pipeline et audit de qualité.

Ne pas imposer le même stockage à toutes les données. PostgreSQL convient bien aux données référentielles, événementielles, aux métadonnées et aux données de volume raisonnable. Les datasets analytiques très volumineux peuvent rester en Parquet, avec leur catalogue et leur lignée référencés dans PostgreSQL.

## 4. Installer et configurer les dépendances

### Opérations à réaliser

1. Ajouter SQLAlchemy, Alembic et psycopg aux dépendances du projet avec le gestionnaire de paquets retenu.
2. Vérifier leur compatibilité avec la version Python retenue par le projet.
3. Ne pas stocker de mot de passe, de chaîne de connexion complète ou de secret dans Git.
4. Lire la configuration depuis des variables d’environnement ou un mécanisme de secrets fourni par l’environnement de déploiement.
5. Prévoir une configuration distincte pour le développement, les tests et la production.
6. Utiliser une base ou un schéma dédié aux tests afin de ne jamais lancer une migration de test sur les données de développement.

### URL de connexion

Avec psycopg, la forme recommandée de l’URL SQLAlchemy est :

```text
postgresql+psycopg://utilisateur:mot_de_passe@hote:5432/nom_de_base
```

Pour les mots de passe contenant des caractères réservés, construire l’URL avec `sqlalchemy.URL.create` plutôt qu’avec une interpolation de chaîne.

### Livrable attendu

Un module de configuration testable, une liste de dépendances verrouillée et un modèle de fichier d’environnement ne contenant aucun secret réel.

## 5. Créer le socle SQLAlchemy

### 5.1 Définir la base déclarative

La base déclarative est le point commun de tous les modèles ORM. Elle expose la métadonnée que SQLAlchemy et Alembic utiliseront pour connaître les tables attendues.

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

### 5.2 Définir un modèle ORM minimal

Un modèle doit porter les éléments réellement garantis par la base : nom de table, schéma, colonnes, clé primaire, contraintes, index et relations.

```python
from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from indusense.db.base import Base


class Machine(Base):
    __tablename__ = "machine"
    __table_args__ = {"schema": "silver"}

    machine_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    model: Mapped[str] = mapped_column(String(32), nullable=False)
    commissioning_date: Mapped[date] = mapped_column(Date, nullable=False)
```

Le modèle ci-dessus est un exemple pédagogique. Les stagiaires doivent ensuite ajouter les contraintes, index et relations validés par le contrat silver.

### 5.3 Types et contraintes à privilégier

| Besoin | Outil SQLAlchemy / PostgreSQL | Point d’attention |
|---|---|---|
| identifiant métier | `String` + `primary_key` ou `UniqueConstraint` | préserver les zéros initiaux et le format métier |
| entier | `Integer` | utiliser une contrainte de domaine si nécessaire |
| mesure décimale | `Numeric(precision, scale)` + `Decimal` | éviter les erreurs d’arrondi des flottants pour les valeurs exigeant une précision fixe |
| date | `Date` | ne pas ajouter une heure artificielle |
| instant | `DateTime(timezone=True)` | adopter une convention UTC documentée |
| booléen | `Boolean` | définir clairement la règle pour les valeurs nulles |
| texte libre | `Text` | ne pas transformer le texte en catégorie sans règle explicite |
| payload source ou métadonnées flexibles | `JSONB` PostgreSQL | ne pas l’utiliser à la place de colonnes requêtées et contraintes |
| relation | `ForeignKey` + `relationship` | tester l’intégrité référentielle |
| données répétées | `UniqueConstraint` | définir soigneusement la clé métier, notamment pour la télémétrie |
| accès fréquent | `Index` | indexer en fonction des requêtes réelles, pas toutes les colonnes |

### 5.4 Règles de nommage des contraintes

Définir une convention de nommage unique dans `Base.metadata`. Elle rend les contraintes prévisibles et aide Alembic à comparer le modèle au schéma de base.

Les noms doivent distinguer les clés primaires, étrangères, uniques, checks et index. Par exemple : `pk_<table>`, `fk_<table>_<colonne>_<table_cible>`, `uq_<table>_<colonne>` et `ix_<table>_<colonne>`.

### Livrable attendu

Une base déclarative, des modèles ORM importables, un dictionnaire des entités et une convention de nommage documentée.

## 6. Gérer l’Engine, les sessions et les transactions

### 6.1 Rôle de l’Engine

L’`Engine` contient la configuration de connexion et gère le pool de connexions. Il est créé une fois par processus applicatif, pas une fois par requête ou par ligne importée.

### 6.2 Rôle de la Session

La `Session` est une unité de travail courte. Elle sert à charger des objets, enregistrer les changements et valider ou annuler une transaction.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

with SessionLocal.begin() as session:
    # lire, créer ou modifier des objets ORM
    # commit automatique à la sortie si aucune exception ne survient
    pass
```

### Opérations à réaliser

1. Créer l’Engine dans un module dédié.
2. Activer une vérification de santé des connexions (`pool_pre_ping=True`) lorsque l’application conserve un pool.
3. Créer une fabrique de sessions et injecter la session dans les services ou repositories qui en ont besoin.
4. Utiliser des context managers pour garantir `commit` ou `rollback` et la fermeture de session.
5. Garder les transactions courtes : ne pas effectuer de calcul long, d’appel réseau ou de lecture de gros fichier dans une transaction ouverte.
6. Ne pas partager une même session entre plusieurs threads ou tâches asynchrones.
7. Capturer, journaliser et remonter les erreurs de base sans afficher de secrets dans les logs.

### Livrable attendu

Un module Engine/session, des exemples de transactions réussies et annulées, et des tests montrant qu’une erreur ne laisse pas d’écriture partielle.

## 7. Modéliser les relations et les requêtes

### Opérations à réaliser

1. Définir les clés étrangères entre machine, incidents, maintenances, télémétrie et tables de pipeline.
2. Définir des relations ORM utiles à la navigation métier, sans transformer chaque relation possible en chargement automatique.
3. Créer les index adaptés aux accès attendus, en particulier les clés de jointure et les accès temporels tels que `(machine_id, timestamp)`.
4. Écrire des requêtes SQLAlchemy 2.x avec `select`, `where`, `join` et paramètres liés.
5. Vérifier le SQL généré pour les requêtes coûteuses.
6. Détecter et corriger le problème N+1 : charger une collection relationnelle de façon non maîtrisée peut déclencher une requête supplémentaire par machine.
7. Utiliser `selectinload` ou `joinedload` seulement lorsque le besoin est établi et comparer les volumes chargés.
8. Utiliser les insertions en lot pour les gros imports de télémétrie et mesurer leur performance.

### Analogie pour le problème N+1

Demander les incidents de cent machines une par une revient à appeler cent fois l’entrepôt pour savoir ce qui est rangé dans chaque rayon. Une requête groupée demande l’information en moins d’allers-retours.

### Livrable attendu

Des modèles avec relations testées, des requêtes de lecture et d’écriture représentatives, ainsi qu’un document décrivant les index et les stratégies de chargement.

## 8. Pourquoi utiliser Alembic ?

Modifier une classe ORM ne modifie pas automatiquement une base déjà existante. Sans outil de migration, chaque personne doit modifier sa base à la main, ce qui entraîne rapidement des environnements différents et des erreurs de déploiement.

Alembic apporte :

- un historique versionné et relu des changements de schéma ;
- un ordre déterministe d’application des évolutions ;
- la possibilité de créer, modifier ou supprimer tables, index et contraintes de façon reproductible ;
- la vérification de la version de schéma installée dans une base ;
- un mécanisme de retour arrière à utiliser avec prudence, surtout si la migration a supprimé ou transformé des données ;
- un support d’autogénération de migrations candidates à partir de la métadonnée SQLAlchemy.

**Analogie :** Alembic est le carnet de chantier de la base. Le plan actuel de l’ORM dit ce que l’on souhaite obtenir ; chaque migration explique comment passer proprement d’un ancien plan au suivant.

L’autogénération est une aide, jamais une approbation automatique. Alembic compare le schéma de base à la métadonnée du modèle et propose une migration ; les stagiaires doivent la relire et la corriger avant de l’appliquer.

## 9. Initialiser et configurer Alembic

### Opérations à réaliser

1. Initialiser l’environnement Alembic une seule fois dans le projet avec `alembic init migrations`.
2. Conserver `alembic.ini`, `migrations/env.py`, le template et tous les fichiers de `migrations/versions/` dans Git.
3. Dans `migrations/env.py`, charger la configuration de base de données depuis les variables d’environnement, pas depuis un secret commité dans `alembic.ini`.
4. Importer tous les modèles ORM avant d’exposer `target_metadata = Base.metadata`.
5. Configurer l’exécution en ligne avec une connexion PostgreSQL et prévoir le mode SQL hors ligne si le déploiement doit générer un script à faire valider.
6. Ajouter les schémas PostgreSQL au plan de migration si les couches bronze, silver, gold et ops sont retenues.
7. Ajouter des règles de comparaison utiles, par exemple les types, les defaults serveur ou les schémas, seulement après avoir compris leur effet.

### Première migration

1. Créer les modèles ORM initiaux.
2. Générer une migration candidate avec `alembic revision --autogenerate -m "create initial schema"`.
3. Relire manuellement le fichier créé : schémas, types, clés, index, contraintes, defaults et ordre des opérations.
4. Corriger le script de migration si nécessaire.
5. Appliquer la migration avec `alembic upgrade head` sur une base de développement vide.
6. Vérifier la version appliquée avec `alembic current` et consulter l’historique avec `alembic history`.

### Livrable attendu

Un environnement Alembic fonctionnel, une migration initiale relue, une base de test créée uniquement par `alembic upgrade head` et une documentation des commandes de développement.

## 10. Workflow quotidien de migration

Pour chaque changement de structure :

1. Modifier les modèles SQLAlchemy et les tests associés.
2. Créer une migration candidate avec `alembic revision --autogenerate -m "description claire du changement"`.
3. Relire la migration ligne par ligne ; vérifier en particulier les suppressions de colonnes, les changements de type, les contraintes, les index et les opérations sur les données existantes.
4. Compléter manuellement les opérations qu’Alembic ne peut pas déduire ou ne peut pas déduire de façon sûre.
5. Tester `alembic upgrade head` sur une base vide puis sur une base contenant un jeu de données représentatif.
6. Ajouter ou mettre à jour les tests d’intégration et le dictionnaire de données.
7. Commiter ensemble le modèle ORM, la migration, les tests et la documentation associée.
8. Appliquer la migration une seule fois par environnement de déploiement, avant le démarrage des processus applicatifs qui l’utilisent.

### Commandes à connaître

| Commande | But |
|---|---|
| `alembic revision -m "..."` | créer une migration vide à écrire manuellement |
| `alembic revision --autogenerate -m "..."` | créer une migration candidate depuis les modèles ORM |
| `alembic upgrade head` | appliquer toutes les migrations jusqu’à la dernière révision |
| `alembic current` | afficher la révision installée dans la base ciblée |
| `alembic history` | afficher l’historique des révisions |
| `alembic check` | détecter, en intégration continue, un changement de modèle sans migration correspondante |
| `alembic downgrade -1` | revenir d’une révision en développement ou en test, avec prudence |
| `alembic upgrade head --sql` | générer le SQL à examiner sans modifier la base |

### Livrable attendu

Une procédure de migration revue par l’équipe, des migrations lisibles et un contrôle continu empêchant de déployer un modèle sans migration correspondante.

## 11. Gérer les évolutions risquées et les migrations de données

Une migration de schéma n’est pas toujours une migration de données. Ajouter une colonne est souvent rapide ; recalculer des millions de lignes peut être long, verrouiller une table et échouer en production.

### Stratégie recommandée : étendre, migrer, retirer

1. **Étendre** : ajouter une nouvelle colonne, table ou index de manière compatible avec la version actuelle de l’application.
2. **Migrer** : remplir ou transformer les données avec une tâche dédiée, réexécutable et observée.
3. **Basculer** : mettre l’application à jour pour lire et écrire le nouveau format.
4. **Vérifier** : comparer les données anciennes et nouvelles, puis faire valider la qualité.
5. **Retirer** : supprimer l’ancien champ dans une migration ultérieure, seulement après la période de compatibilité.

### Règles de sécurité

- Éviter les suppressions irréversibles sans sauvegarde, fenêtre de maintenance et validation explicite.
- Ne pas faire dépendre un déploiement applicatif d’un backfill long exécuté dans une transaction de migration.
- Écrire des migrations `upgrade` et `downgrade` réalistes ; documenter lorsqu’un retour arrière détruirait des informations.
- Utiliser une migration manuelle pour les renommages, changements de type complexes, index spécifiques PostgreSQL ou opérations métier.
- Tester le temps d’exécution et les verrous sur une copie réaliste des données avant la production.

### Livrable attendu

Une procédure de migration de données documentée, avec plan de reprise, mesure de progression, stratégie de sauvegarde et critères de validation.

## 12. Persister les couches bronze, silver et gold

### Bronze

1. Enregistrer le fichier ou le lot source, son empreinte, sa date d’ingestion et son statut.
2. Conserver les données sources et leurs métadonnées de lignée.
3. Enregistrer les rejets et avertissements sans effacer les données brutes.

### Silver

1. Persister les entités normalisées : machine, incident, maintenance et télémétrie.
2. Imposer les clés, contraintes de domaine et relations validées par le contrat silver.
3. Conserver l’audit de dédoublonnage, les mappings appliqués et les lignes de quarantaine.
4. Utiliser des écritures idempotentes et en lot pour les tâches d’ingestion.

### Gold

1. Persister le catalogue de features, la version des règles et les métadonnées de construction.
2. Stocker ou référencer les snapshots de features, labels d’arrêt, jeux d’entraînement et résultats de qualité.
3. Conserver la lignée vers les sources silver, la date de prédiction et la dernière date de donnée utilisée.
4. Prévoir une table d’audit des prédictions et versions de modèle lorsque l’inférence sera mise en service.

### Livrable attendu

Un schéma PostgreSQL documenté reliant les trois couches et une stratégie claire précisant quelles données restent en tables PostgreSQL et lesquelles sont stockées en Parquet.

## 13. Tester et déployer sans risque

### Tests à mettre en place

1. Lancer une base PostgreSQL de test à partir du conteneur fourni.
2. Créer le schéma uniquement avec `alembic upgrade head`.
3. Vérifier que chaque modèle peut être inséré, lu, modifié et supprimé selon les règles métier.
4. Vérifier les clés étrangères, contraintes uniques, checks, defaults et index importants.
5. Tester les rollbacks transactionnels lors d’une exception.
6. Tester une migration depuis une révision ancienne vers `head`.
7. Tester l’idempotence des ingestions et des écritures de lots.
8. Tester l’échec attendu lors d’une donnée invalide, puis vérifier sa présence dans la quarantaine lorsque la règle le prévoit.
9. Mesurer les requêtes et chargements en lot significatifs afin de repérer les accès N+1 ou les index absents.

### Déploiement

1. Sauvegarder la base et vérifier la possibilité de restauration.
2. Générer et relire le plan de migration.
3. Appliquer la migration avec un compte PostgreSQL dédié, possédant uniquement les droits nécessaires.
4. Vérifier la révision Alembic et les contrôles de santé après l’application.
5. Démarrer ou redémarrer les services consommateurs seulement lorsque le schéma attendu est présent.
6. Journaliser la version de migration, le pipeline applicatif et la personne ou le processus ayant exécuté l’opération.

### Livrable attendu

Une suite de tests d’intégration utilisant PostgreSQL, une procédure de déploiement, une procédure de sauvegarde/restauration et un journal d’audit de migration.

## 14. Références à lire

- [SQLAlchemy ORM — table mapping déclaratif](https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html)
- [SQLAlchemy — dialecte PostgreSQL avec psycopg](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [Alembic — tutoriel](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic — autogénération et limites](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)

## 15. Critères de fin de roadmap

La persistance est prête lorsque :

- le projet se connecte à PostgreSQL avec `postgresql+psycopg://` sans exposer de secret ;
- les modèles ORM décrivent clairement les entités, clés, contraintes, relations et index ;
- les sessions et transactions sont courtes, testées et correctement annulées en cas d’erreur ;
- chaque évolution de schéma passe par une migration Alembic relue et testée ;
- la base peut être reconstruite depuis zéro avec les migrations versionnées ;
- les écritures de données sont traçables, idempotentes et adaptées aux volumes ;
- les couches bronze, silver et gold disposent d’une stratégie de persistance et de lignée documentée.
