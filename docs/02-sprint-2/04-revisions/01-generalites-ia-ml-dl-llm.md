# Généralités sur l'IA, le Machine Learning, le Deep Learning et les LLM

## Définition et objectif

L'**intelligence artificielle (IA)** désigne un ensemble de techniques permettant à une machine de réaliser des tâches associées à des capacités humaines, par exemple raisonner, planifier, reconnaître une image ou produire du texte.

Le **Machine Learning (ML)**, ou apprentissage automatique, est une manière de construire un système : au lieu d'écrire explicitement toutes les règles, on lui fournit des données afin qu'il apprenne un modèle utilisable sur de nouvelles observations.

Le **Deep Learning (DL)**, ou apprentissage profond, est une famille de techniques de Machine Learning reposant sur des réseaux de neurones comportant plusieurs couches. Il est particulièrement utilisé pour traiter des données complexes comme les images, le son et le texte.

L'**IA générative** produit un nouveau contenu, par exemple du texte, une image, du son, une vidéo ou du code, à partir de régularités apprises dans des données d'entraînement.

Un **LLM** (*Large Language Model*, grand modèle de langage) est un modèle de Deep Learning entraîné sur une grande quantité de textes pour traiter et générer du langage. Lors de la génération, il prédit successivement des **tokens**, c'est-à-dire des unités de texte qui peuvent être des mots, des parties de mots ou des signes de ponctuation.

## Notions essentielles

La relation présentée dans le cours est une imbrication :

```text
Intelligence artificielle
└── Machine Learning
    └── Deep Learning
        └── IA générative moderne, dont les LLM pour le langage
```

Cette représentation est un repère pédagogique. Elle décrit bien les systèmes génératifs modernes étudiés dans le cours, même si l'histoire de l'IA comporte aussi d'autres approches génératives.

### Programme traditionnel et Machine Learning

- En programmation traditionnelle, le développeur fournit les données et les règles ; le programme calcule la sortie.
- En Machine Learning supervisé, le data scientist fournit des exemples d'entrées et de sorties attendues ; l'algorithme d'entraînement apprend les paramètres d'un modèle.
- En exploitation, le modèle reçoit une nouvelle entrée et produit une prédiction.

Un **algorithme d'entraînement** est la procédure qui ajuste automatiquement le modèle. Le **modèle** est le résultat appris et réutilisable. Ces deux termes ne sont donc pas synonymes.

## Exemple concret

Pour estimer le prix d'un logement, les données historiques contiennent des caractéristiques comme la surface, le nombre de pièces et le type de logement, ainsi qu'un prix connu. L'algorithme utilise ces exemples pour apprendre un modèle. Une fois entraîné, ce modèle peut estimer le prix d'un logement qu'il n'a jamais vu.

La sortie attendue est ici une valeur numérique continue : il s'agit d'un problème de **régression**. La classification, qui prédit une catégorie, et les autres familles d'algorithmes seront détaillées dans une fiche dédiée.

## Erreurs fréquentes et bonnes pratiques

- Ne pas employer « IA », « ML », « DL », « IA générative » et « LLM » comme des synonymes.
- Ne pas confondre l'algorithme d'entraînement avec le modèle obtenu.
- Ne pas dire qu'un modèle « comprend » automatiquement au sens humain : il apprend des régularités statistiques adaptées à un objectif.
- Ne pas évaluer un modèle uniquement sur les données qui ont servi à l'entraîner ; sa capacité à fonctionner sur des données jamais vues doit être vérifiée.
- Considérer les chiffres de marché du support comme des éléments à sourcer avant de les réutiliser dans un livrable ou à l'oral.

## Points à retenir pour le QCM

- Le Machine Learning est un sous-ensemble de l'intelligence artificielle.
- Le Deep Learning est un sous-ensemble du Machine Learning.
- Un LLM est un modèle de langage fondé sur le Deep Learning.
- Un token est une unité de texte manipulée par un modèle de langage.
- En Machine Learning, les règles de décision sont apprises à partir des données plutôt qu'intégralement écrites à la main.
- L'entraînement produit un modèle ; l'exploitation utilise ce modèle sur de nouvelles données.

## Points à savoir expliquer lors de la soutenance

- Pourquoi le besoin métier relève ou non du Machine Learning.
- Quelle prédiction ou quel contenu le système doit produire.
- Quelles données permettent d'apprendre et quelles données seront présentées au modèle en exploitation.
- La différence entre une règle métier codée explicitement et une relation apprise à partir d'exemples.
- Pourquoi les performances doivent être mesurées sur des données que le modèle n'a pas utilisées pour apprendre.

## Sources du cours

- `01_acculturation_IA.pdf`, support Aelion, diapositives 1 à 29.
- `02_machine_learning.pdf`, support Aelion, diapositives 1 à 6.
- `pipeline_entrainement_ml_role_data_scientist.png`, schéma du pipeline d'entraînement et des responsabilités.

## Pour aller plus loin

- [Commission européenne - Définition et capacités d'un système d'IA](https://digital-strategy.ec.europa.eu/en/library/definition-artificial-intelligence-main-capabilities-and-scientific-disciplines)
- [Google for Developers - Introduction to Machine Learning](https://developers.google.com/machine-learning/intro-to-ml)
- [Vaswani et al. - Attention Is All You Need](https://arxiv.org/abs/1706.03762), article fondateur de l'architecture Transformer utilisée par les LLM modernes.
