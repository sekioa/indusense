# Pipeline de données Bronze, Silver et Gold

## Définition et objectif

L’architecture **Bronze–Silver–Gold**, aussi appelée architecture en médaillon, organise progressivement les données selon leur niveau de préparation. Un **pipeline de données** est l’enchaînement des opérations qui collecte, transforme et rend les données utilisables.

L’objectif est de conserver une source fidèle, de rendre les données fiables, puis de produire un dataset adapté au besoin de machine learning.

## Les trois niveaux

| Niveau | Rôle | Opérations principales |
| --- | --- | --- |
| Bronze | Conserver les données collectées au plus près de leur état d’origine | Ingestion, ajout de métadonnées techniques et traçabilité de la source |
| Silver | Obtenir des données propres, cohérentes et protégées selon le besoin du pipeline | Dédoublonnage, typage, normalisation, contrôles de qualité, gestion des rejets et transformations de protection nécessaires |
| Gold | Fournir les données utiles à un usage précis | Sélection, minimisation, anonymisation, *feature engineering* et préparation des jeux pour le modèle |

Un **dataset** est un ensemble structuré de données. Le **typage** associe à chaque valeur un type exploitable, comme une date, un nombre ou un booléen. La **normalisation** harmonise les formats ou les échelles. Les **rejets** sont les enregistrements qui ne satisfont pas les règles de qualité et qui doivent rester traçables pour être analysés ou corrigés.

## Démarche

### 1. Recenser et qualifier les sources

Les données peuvent venir de bases SQL, de fichiers XML, JSON, CSV, TXT ou TSV, ainsi que d’API externes. Une **API** est une interface permettant à un programme d’échanger avec un autre service.

Avant l’ingestion, vérifier notamment :

- les droits d’accès et les conditions d’utilisation ;
- les coûts, quotas et limites des API ;
- le format et la fréquence de mise à jour ;
- la présence éventuelle de données personnelles.

### 2. Construire le niveau Bronze

Le Bronze conserve une copie fidèle des données reçues afin de pouvoir rejouer le pipeline et auditer les transformations. Les notes du formateur recommandent de ne pas modifier les types à ce stade et de conserver les valeurs sous forme de texte.

Le principe général à retenir est la fidélité à la source. Le stockage systématique en texte est un choix d’implémentation dépendant du contexte : certains systèmes conservent plutôt le fichier brut et ses métadonnées sans le convertir.

### 3. Nettoyer le niveau Silver

Le passage au Silver comprend notamment :

1. la suppression ou le rapprochement des doublons ;
2. la conversion vers les types attendus ;
3. l’harmonisation des unités, libellés et formats ;
4. l’application de règles de qualité ;
5. l’isolement des lignes rejetées avec la raison du rejet.

Le résultat attendu est un dataset cohérent, contrôlé et encore réutilisable pour plusieurs usages.

Dans le TP `releves_incidents`, la consigne impose également de rendre les données qualifiées de sensibles non identifiables dès la production du Silver. Cela précise le pipeline propre à l’exercice : une transformation de protection n’est pas réservée par principe au Gold. Elle doit être appliquée au niveau approprié, avant qu’une donnée identifiable soit exposée ou utilisée sans nécessité. La méthode exacte reste à choisir après l’analyse des colonnes et du risque de réidentification.

Pour l'analyse incidents-maintenance, la décision retenue est une **minimisation par suppression** de `operator_name`, `operator_badge` et `shift`. Le commentaire libre `comment` est conservé dans Silver : il peut contenir une information métier sur un arrêt de machine absente des indicateurs structurés. Le fichier Bronze reste inchangé et le Silver est relu pour vérifier à la fois l'absence des trois colonnes opérateur et la présence du commentaire métier.

Cette minimisation réduit les identifiants directs, mais elle ne suffit pas à démontrer une anonymisation irréversible face à tout recoupement possible. Le commentaire libre doit également être contrôlé avant toute diffusion, car il peut contenir des éléments identifiants. Un horodatage précis associé à une machine peut encore constituer un quasi-identifiant si un tiers possède, par exemple, le planning détaillé des opérateurs.

### 4. Préparer le niveau Gold

Le Gold répond à un cas d’usage déterminé. Pour un modèle de machine learning, il peut inclure :

- la sélection des seules variables utiles ;
- la **minimisation**, c’est-à-dire la limitation des données personnelles au strict nécessaire ;
- l’**anonymisation**, qui vise à empêcher l’identification des personnes ;
- le **feature engineering**, c’est-à-dire la création ou la transformation de variables utiles au modèle ;
- le traitement d’un éventuel déséquilibre entre les classes ;
- la séparation en jeux d’entraînement, de validation et de test.

Le jeu d’entraînement sert à ajuster le modèle. Le jeu de validation sert à choisir les réglages. Le jeu de test sert à mesurer une dernière fois les performances sur des données restées à l’écart.

## Exemple concret

Pour prévoir une panne industrielle :

- Bronze conserve les relevés bruts des capteurs et leur date de collecte ;
- Silver convertit les dates et mesures, harmonise les unités, retire les doublons et isole les valeurs invalides ;
- Gold sélectionne les capteurs pertinents, calcule par exemple une moyenne glissante, puis produit les jeux d’entraînement, de validation et de test.

Dans Indusense, le métier confirme que plusieurs télémétries portant la même machine et le même timestamp sont des répétitions techniques dues à l'occupation du bus. Les 1 340 groupes observés présentent des écarts très faibles, inférieurs à `0,15 %` de la moyenne du groupe au maximum, et aucune différence sur le nombre de pièces produites. Bronze conserve toutes les lignes ; Silver conserve la ligne la plus complète, puis la première ligne source en cas d'égalité, et audite les 1 346 lignes écartées.

Une valeur de capteur manquante n'est pas automatiquement une ligne invalide. Dans le Bronze Indusense, 2 828 télémétries ont au moins une température, pression ou rotation absente. Comme les autres mesures de ces lignes restent valides, Silver conserve la ligne avec `NULL` et un avertissement. L'imputation éventuelle appartient à une future vue de features, avec une règle explicite, et non au nettoyage Silver.

## Erreurs fréquentes et bonnes pratiques

- Modifier ou écraser les données Bronze empêche de rejouer fidèlement les traitements.
- Supprimer silencieusement les rejets masque les problèmes de qualité ; conserver leur cause et leur provenance.
- Construire les variables ou équilibrer les classes avant la séparation peut provoquer une **fuite de données**, c’est-à-dire transmettre au modèle une information provenant indirectement de la validation ou du test.
- Équilibrer aussi les jeux de validation et de test peut fausser l’évaluation ; ils doivent généralement rester représentatifs des données réelles.
- Collecter des données « au cas où » s’oppose au principe de minimisation du RGPD.
- Utiliser une API sans vérifier ses droits, quotas et coûts peut rendre le pipeline non conforme ou non reproductible.

## Points à retenir pour le QCM

- Bronze conserve les données proches de la source.
- Silver nettoie, type, normalise et contrôle la qualité.
- Gold prépare les données pour un usage métier ou analytique précis.
- Selon le pipeline et le risque, les transformations de protection des données peuvent être nécessaires dès le niveau Silver.
- Les rejets doivent être explicables et traçables.
- Les jeux de validation et de test ne servent pas à entraîner le modèle.

## Points à savoir expliquer lors de la soutenance

- Pourquoi séparer les données en plusieurs niveaux plutôt que de modifier directement la source.
- Comment garantir la traçabilité d’une donnée depuis son origine jusqu’au modèle.
- Quelles transformations sont effectuées à chaque niveau et pourquoi.
- Comment éviter une fuite de données lors du *feature engineering* et de l’équilibrage.
- Comment la minimisation et l’anonymisation participent à la conformité RGPD.

La correspondance exacte avec les compétences C1 à C9 reste à confirmer avec le Kit candidat.

## Pour aller plus loin

- [Databricks — Architecture Medallion](https://www.databricks.com/glossary/medallion-architecture) : présentation détaillée des responsabilités Bronze, Silver et Gold.
- [scikit-learn — Données incohérentes et fuite de données](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage) : pièges à éviter lors des transformations et de l’évaluation.
- [CNIL — Principes clés du RGPD](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre2) : repère pour la minimisation et la traçabilité des traitements.
