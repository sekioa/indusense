# Explorer un fichier CSV avec pandas

## Définition et objectif

Un fichier **CSV** (*Comma-Separated Values*) représente des données tabulaires sous forme de texte. Une ligne correspond généralement à une observation et une colonne à une variable.

`pandas` est une bibliothèque Python consacrée à la manipulation de données tabulaires. Sa structure principale, le `DataFrame`, représente un tableau possédant des lignes et des colonnes nommées.

L'objectif d'une première exploration est de vérifier la structure du jeu de données avant toute analyse : dimensions, noms et types des colonnes, aperçu des lignes et valeurs synthétiques.

## Notions essentielles

- `pd.read_csv(...)` charge un fichier CSV dans un `DataFrame`.
- `df.shape` renvoie le nombre de lignes et de colonnes sous la forme d'un tuple.
- `df.columns` contient les en-têtes de colonnes.
- `df.head(10)` sélectionne les dix premières lignes.
- `df.dtypes` indique le type pandas de chaque colonne.
- `pd.to_datetime(...)` convertit une colonne textuelle en dates exploitables.
- `Series.astype("boolean")` convertit un indicateur binaire en booléen pandas (`False`, `True` ou valeur manquante).
- `Series.min()` et `Series.max()` calculent les valeurs minimale et maximale.
- `Series.nunique()` compte les valeurs distinctes d'une colonne.

Un **type de données** décrit la nature et les opérations possibles sur une valeur. Une date chargée comme texte doit être convertie en `datetime` pour effectuer des comparaisons chronologiques fiables.

### Comprendre `datetime64[us]`

- `datetime64` indique que la colonne contient des dates ou des horodatages, et non de simples chaînes de caractères.
- `[us]` indique une résolution à la **microseconde** : la plus petite unité représentable est un millionième de seconde.
- En interne, chaque valeur est stockée comme un nombre entier d'unités temporelles comptées à partir du 1er janvier 1970.
- La résolution ne signifie pas que les données sources possèdent réellement des microsecondes. Une valeur telle que `2025-06-01` est représentée à minuit, soit `2025-06-01 00:00:00`.
- Le type `datetime64[us]` ne contient ici aucune information de fuseau horaire ; la série est dite **timezone-naive**.

Depuis pandas 3.0, `pd.to_datetime()` produit généralement une résolution en microsecondes lors de la conversion de chaînes. Ce type permet de trier chronologiquement les dates, de calculer `min()` et `max()`, de soustraire deux dates et d'utiliser l'accesseur `.dt`, par exemple `incidents["date"].dt.year`.

## Démarche

1. Construire le chemin du fichier avec `pathlib.Path` et vérifier son existence.
2. Charger le CSV avec `pd.read_csv` sans modifier le fichier source.
3. Examiner les dimensions, les en-têtes et les premières lignes.
4. Observer les types détectés, puis convertir explicitement les colonnes qui le nécessitent.
5. Calculer les minimums, maximums et nombres de valeurs distinctes.
6. Regrouper les résultats dans un rapport lisible et vérifier les calculs.

## Convention retenue pour les futurs travaux pratiques

Dans un TP limité à l'exploration du niveau Bronze, **déterminer les types** ne signifie pas les convertir. Le rapport doit distinguer :

- le type effectivement observé après la lecture du Bronze ;
- la signification métier de la colonne ;
- le type cible recommandé pour une future transformation Silver.

Les conversions avec `astype()`, `convert_dtypes()` ou une opération équivalente sont reportées à l'étape Silver, sauf demande explicite de la consigne. Une conversion temporaire destinée à un calcul doit être annoncée comme telle et ne doit pas être présentée comme une transformation du dataset Bronze.

La documentation du notebook doit être **orientée domaine** :

- la cellule Markdown formule la question métier, le choix de la méthode pandas, les hypothèses et le résultat attendu ;
- les noms de variables et de fonctions reprennent le vocabulaire métier ;
- les commentaires Python expliquent les décisions et les comportements non évidents ;
- le code évident n'est pas paraphrasé ligne par ligne.

Cette convention préserve la lisibilité attendue par le clean code tout en rendant les décisions défendables pendant la formation et la soutenance.

## Exemple concret

```python
from pathlib import Path

import pandas as pd

chemin = Path("datas") / "releves_incidents.csv.csv"
incidents = pd.read_csv(chemin).convert_dtypes()
incidents["date"] = pd.to_datetime(incidents["date"], errors="raise")

colonnes_types = [colonne for colonne in incidents if colonne.startswith("type_")]
for colonne in colonnes_types:
    incidents[colonne] = incidents[colonne].astype("boolean")

print("Dimensions :", incidents.shape)
print("Machines distinctes :", incidents["machine_id"].nunique())
print("Date minimale :", incidents["date"].min().date())
```

La conversion se fait ici en mémoire : le fichier CSV source reste inchangé, ce qui respecte la conservation d'une donnée Bronze.

## Erreurs fréquentes et bonnes pratiques

- Ne pas confondre le nombre de lignes avec le nombre total de cellules.
- Ne pas comparer des dates comme de simples chaînes sans avoir vérifié leur format.
- Ne pas conserver automatiquement un indicateur `0`/`1` en entier lorsque sa signification métier est « absent »/« présent » : vérifier ses valeurs, puis utiliser un type booléen.
- Utiliser `errors="raise"` pendant l'apprentissage afin qu'une date invalide provoque une erreur visible.
- Choisir la colonne qui répond directement à la question métier, puis contrôler sa cohérence avec les autres identifiants disponibles. Un badge peut sembler plus stable qu'un nom, mais sa correspondance avec les personnes doit être vérifiée dans les données.
- Vérifier les valeurs manquantes avant d'interpréter `nunique()`, car son comportement par défaut les exclut.
- Conserver le fichier Bronze original et réaliser les conversions dans un nouveau `DataFrame` ou en mémoire.
- Ne pas forcer un tableau texte très large dans une zone d'affichage étroite : Jupyter peut couper les lignes et désaligner les bordures. Répartir les colonnes en vues cohérentes ou résumer les indicateurs binaires dans une colonne dédiée.

## Points à retenir pour le QCM

- `shape[0]` correspond au nombre de lignes et `shape[1]` au nombre de colonnes.
- `head()` renvoie cinq lignes par défaut ; `head(10)` en renvoie dix.
- `dtypes` décrit chaque colonne, tandis que `type(df)` décrit l'objet Python complet.
- `nunique()` compte des valeurs différentes ; `count()` compte des valeurs non nulles.
- `min()` et `max()` s'appliquent aussi à une série de type `datetime64`.

## Points à savoir expliquer lors de la soutenance

- Pourquoi l'exploration précède le nettoyage et la modélisation.
- Pourquoi la conversion explicite des dates sécurise les comparaisons.
- Quelle colonne a été choisie pour identifier une machine ou un opérateur, et pourquoi.
- Comment les données sources ont été préservées pendant l'analyse.
- Quels contrôles permettent de défendre la fiabilité du rapport produit.

La correspondance précise avec les compétences C1 à C9 reste à confirmer à partir du Kit candidat.

## Pour aller plus loin

- [pandas — Guide utilisateur](https://pandas.pydata.org/docs/user_guide/index.html) : référence progressive pour sélectionner, transformer et contrôler les données.
- [pandas — Lecture et écriture de fichiers](https://pandas.pydata.org/docs/user_guide/io.html) : options importantes de `read_csv()` et gestion des formats.
