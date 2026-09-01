# Docker Desktop : démarrage et validation du moteur

## Définition et objectif

Docker Desktop fournit notamment :

- le **client Docker**, c'est-à-dire la commande `docker` saisie dans le terminal ;
- le **moteur Docker**, aussi appelé *daemon*, qui construit les images et exécute les conteneurs ;
- le **backend WSL 2**, qui fournit sous Windows l'environnement Linux utilisé par le moteur.

La présence de la commande `docker` valide seulement l'installation du client. L'objectif est de vérifier séparément que Docker Desktop démarre, que le moteur répond et qu'un conteneur peut réellement être exécuté.

## Prérequis et point de départ

- Docker Desktop doit être installé.
- Ouvrir un terminal PowerShell normal ; les droits administrateur ne sont pas nécessaires pour ce contrôle.
- Une connexion Internet est nécessaire si l'image de test n'est pas déjà présente sur la machine.

## Démarche

### 1. Démarrer l'application

Dans PowerShell, saisir :

```powershell
docker desktop start
```

Cette commande demande à l'application Docker Desktop de démarrer. Si elle n'est pas reconnue, ouvrir le menu Démarrer de Windows, rechercher **Docker Desktop**, puis sélectionner l'application.

Docker Desktop ouvre sa fenêtre ou place une icône en forme de baleine dans la zone de notification de Windows. Attendre que l'interface indique que le moteur fonctionne avant de continuer. Le démarrage peut prendre plusieurs dizaines de secondes.

### 2. Vérifier la communication entre le client et le moteur

Dans le même terminal PowerShell, saisir :

```powershell
docker version
```

Le résultat attendu contient une section `Client` et une section `Server` :

- `Client` prouve que la commande Docker est installée ;
- `Server` prouve que le moteur répond.

Si seule la section `Client` apparaît avec une erreur de connexion, ne pas continuer : le moteur n'est pas encore disponible.

Interroger ensuite son état détaillé :

```powershell
docker info
```

Cette commande doit afficher, sans erreur, des informations telles que le nombre de conteneurs, le nombre d'images, le système d'exploitation du moteur et son répertoire de stockage.

### 3. Exécuter un premier conteneur

Dans PowerShell, saisir :

```powershell
docker run --rm hello-world
```

Décomposition de la commande :

- `docker run` crée puis démarre un conteneur à partir d'une image ;
- `--rm` supprime automatiquement le conteneur lorsqu'il s'arrête ;
- `hello-world` est le nom de l'image de test.

Au premier lancement, Docker peut télécharger l'image. Le résultat attendu contient `Hello from Docker!`. Le conteneur arrêté est supprimé grâce à `--rm`, mais l'image reste dans le cache local pour les prochains essais.

## Interprétation

- Une section `Server` dans `docker version` confirme que le client communique avec le moteur.
- `docker info` affiche l'état global du moteur, les conteneurs, les images et le stockage.
- Le message de succès de `hello-world` confirme que Docker sait récupérer une image, créer un conteneur et l'exécuter.

## Exemple validé : composition PostgreSQL Indusense

Le projet Indusense fournit `.docker/docker-compose.yml`. **Docker Compose** lit ce fichier et démarre ensemble les services qui y sont déclarés. L’option `-p indusense` fixe explicitement le nom du projet Compose afin de ne pas confondre ses conteneurs, réseaux et volumes avec ceux d’un autre projet local.

Depuis le dossier `indusense`, la composition a été démarrée avec :

```powershell
docker compose -p indusense -f .docker/docker-compose.yml up -d
```

- `-p indusense` nomme le projet Compose ;
- `-f` indique le fichier de composition à utiliser ;
- `up` crée puis démarre les ressources nécessaires ;
- `-d` laisse les conteneurs fonctionner en arrière-plan.

La vérification de l’état se fait avec :

```powershell
docker compose -p indusense -f .docker/docker-compose.yml ps
docker compose -p indusense -f .docker/docker-compose.yml exec -T db pg_isready -U <utilisateur> -d <base>
```

`ps` doit afficher `indusense-db-1` et `indusense-admin-1` avec l’état `Up`. `pg_isready` teste PostgreSQL depuis son conteneur : le résultat attendu se termine par `accepting connections`. Les valeurs réelles de configuration doivent être lues depuis l’environnement sans recopier de secret dans la documentation.

Validation finale observée le 31 août 2026 après chargement du nouveau `.env` : PostgreSQL 15.9 répond sur le port local `5432` et pgAdmin est publié sur le port local `8081`. Le volume PostgreSQL initial, qui ne contenait pas encore le schéma métier ni le Bronze, a été supprimé après autorisation explicite puis recréé afin d’appliquer les nouveaux paramètres d’initialisation. Une connexion SQL authentifiée a confirmé la base et l’utilisateur attendus. Cette validation ne prouve pas encore la création du schéma métier ni l’ingestion du Bronze.

Le compte de connexion à l’interface pgAdmin est distinct du rôle PostgreSQL utilisé pour accéder à une base. `GUI_EMAIL` et `GUI_PASSWORD` authentifient l’utilisateur dans l’interface Web ; `DB_USER` et `DB_PASSWORD` servent ensuite à enregistrer une connexion vers PostgreSQL. Saisir le rôle PostgreSQL sur l’écran de connexion pgAdmin provoque notamment l’erreur `Email/Username is not valid` lorsqu’il ne possède pas la forme attendue par pgAdmin.

## Erreurs fréquentes et bonnes pratiques

- `Cannot connect to the Docker daemon` : Docker Desktop n'est pas démarré, n'est pas encore prêt ou son backend est défaillant.
- Une commande qui semble bloquée juste après le démarrage : attendre que Docker Desktop confirme que le moteur est prêt, puis réessayer `docker version`.
- Une erreur de téléchargement de `hello-world` : vérifier la connexion Internet, le proxy ou l'accès au registre Docker.
- `docker` non reconnu alors que Docker Desktop fonctionne : la CLI peut être installée mais absente du `PATH` du terminal ; localiser l’exécutable de l’installation Docker Desktop avant de conclure que le moteur est absent.
- Modifier `POSTGRES_USER`, `POSTGRES_PASSWORD` ou `POSTGRES_DB` puis recréer seulement le conteneur ne reconfigure pas une base déjà initialisée : ces variables sont appliquées par l’image PostgreSQL lors de la création d’un volume de données vide. Avec un volume persistant existant, il faut soit faire évoluer explicitement les rôles et bases, soit réinitialiser le volume après validation de la perte de ses données.
- Ne pas confondre image et conteneur : l'image est le modèle immuable ; le conteneur est une instance exécutée de cette image.
- Utiliser de préférence les conteneurs Linux avec le backend WSL 2 pour les exercices courants sous Windows.
- Ne pas exécuter Docker Desktop en administrateur sans nécessité.

## Points à retenir pour le QCM

- Le client Docker envoie des commandes au moteur Docker.
- `docker info` interroge le moteur ; `docker --version` peut fonctionner même quand le moteur est arrêté.
- Une image sert à créer un ou plusieurs conteneurs.

## Points à savoir expliquer lors de la soutenance

- Pourquoi la conteneurisation améliore la reproductibilité d'une solution IA.
- Comment vérifier qu'une application conteneurisée fonctionne réellement, au-delà de la présence des outils.

## Pour aller plus loin

- [Docker Docs — Bien débuter](https://docs.docker.com/get-started/) : parcours officiel sur images, conteneurs et Docker Compose.
- [Docker Docs — Persister les données](https://docs.docker.com/get-started/docker-concepts/running-containers/persisting-container-data/) : rôle des volumes, essentiel pour PostgreSQL.
