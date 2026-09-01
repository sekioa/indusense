# Git : commits conventionnels et publication ciblée

## Définition et objectif

Un **commit atomique** regroupe un seul sujet cohérent. Les **Conventional Commits** donnent à son message une structure explicite, par exemple `feat(database): ...`, `docs(architecture): ...` ou `chore(docker): ...`.

L’objectif est de produire un historique lisible, vérifiable et facile à corriger sans mélanger le code, l’infrastructure, la documentation et les changements de dépendances.

## Démarche

1. Exécuter `git status --short --branch` pour identifier la branche et les changements présents.
2. Examiner les diffs et distinguer les sujets ainsi que les fichiers hors périmètre.
3. Ajouter chaque groupe avec `git add -- <chemins explicites>` plutôt qu’avec un ajout global dans un arbre de travail mixte.
4. Contrôler l’index avec `git diff --cached --name-only`, `git diff --cached --stat` et `git diff --cached --check`.
5. Créer un commit conventionnel par sujet.
6. Exécuter les tests et validations sur l’état commité.
7. Pousser la branche explicitement, par exemple `git push origin main`.
8. Comparer `git rev-parse HEAD` au SHA retourné par `git ls-remote origin refs/heads/main`.

## Types courants

- `feat` : nouvelle capacité fonctionnelle ou technique ;
- `fix` : correction d’un défaut ;
- `docs` : documentation uniquement ;
- `build` : dépendances ou système de construction ;
- `chore` : entretien ou infrastructure sans fonctionnalité applicative directe ;
- `test` : ajout ou modification de tests uniquement.

Le **scope**, placé entre parenthèses, précise le domaine concerné : `database`, `docker` ou `architecture`.

## Exemple Indusense validé

La publication du socle de persistance a séparé quatre sujets :

```text
build: add matplotlib dependency
chore(docker): add local PostgreSQL stack
feat(database): add SQLAlchemy persistence foundation
docs(architecture): document persistence target
```

Les notebooks, datasets et sorties préexistants sont restés non suivis. Après le push, le SHA de `origin/main` correspondait au `HEAD` local.

## Erreurs fréquentes et bonnes pratiques

- Utiliser `git add -A` dans un arbre mixte peut publier des données ou travaux sans rapport.
- Mélanger code, documentation et infrastructure rend le commit difficile à relire ou annuler.
- Un `git diff --check` doit interrompre le commit s’il détecte des espaces de fin de ligne ; ne pas enchaîner la commande sans contrôler son code de sortie.
- Un message correct ne garantit pas un bon commit : vérifier aussi la liste réelle des fichiers indexés.
- Un message de succès de `git push` doit être complété par une vérification du SHA distant avant d’affirmer que la publication est synchronisée.

## Points à retenir pour le QCM

- Un commit atomique couvre un sujet cohérent.
- L’index Git contient les changements préparés pour le prochain commit.
- `git diff --cached` inspecte l’index, pas seulement le répertoire de travail.
- Un push publie des commits déjà créés ; il ne publie pas directement les fichiers non suivis.

## Points à savoir expliquer lors de la soutenance

- Pourquoi les sujets ont été séparés en plusieurs commits.
- Comment les fichiers hors périmètre ont été protégés.
- Quelles validations ont été exécutées avant la publication.
- Comment l’égalité des SHA local et distant confirme la publication.

## Pour aller plus loin

- [Pro Git — Les bases de Git](https://git-scm.com/book/fr/v2/D%C3%A9marrage-rapide-Les-bases-de-Git) : explication de l’index, des commits et des branches.
- [Conventional Commits](https://www.conventionalcommits.org/fr/v1.0.0/) : convention de structuration des messages de commit.
