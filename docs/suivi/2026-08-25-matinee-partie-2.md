# Suivi de formation — 25 août 2026 — Matinée, partie 2

## Thème

Présentation d’un pipeline de préparation des données organisé en trois niveaux : **Bronze**, **Silver** et **Gold**.

## Déroulé

1. Identification de plusieurs sources et formats possibles : SQL, XML, JSON, CSV, TXT et TSV.
2. Mention des API externes, avec deux vérifications préalables : les droits d’accès et les coûts éventuels.
3. Constitution du dataset Bronze à partir des données collectées. La consigne présentée est de conserver les données sans modification de type, sous forme de texte.
4. Transformation du Bronze en dataset Silver : dédoublonnage, typage, normalisation et gestion des rejets.
5. Préparation du dataset Gold pour le machine learning :
   - ne conserver que les données utiles au modèle ;
   - convertir, minimiser et anonymiser les données lorsque nécessaire ;
   - réaliser le *feature engineering* ;
   - équilibrer les données ;
   - séparer les jeux d’entraînement, de validation et de test.
6. Mention de la conformité au RGPD dans la préparation du dataset Gold.

## État à la fin de cette deuxième partie

- Le cheminement conceptuel des données, de leur collecte jusqu’au dataset destiné au modèle, a été présenté.
- Aucun pipeline n’est mentionné comme ayant été implémenté ou exécuté dans les notes disponibles.
- Les choix techniques précis de stockage, de transformation et de découpage restent à mettre en pratique.

## Source

Notes visuelles du formateur communiquées le 25 août 2026.
