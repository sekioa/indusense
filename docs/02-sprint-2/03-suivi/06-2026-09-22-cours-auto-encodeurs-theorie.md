# Sprint 2 - 2026-09-22 : cours oral auto-encodeurs (théorie et questions-réponses)

## Objectif concret

L'utilisateur a déposé `docs/02-sprint-2/01-cours/videos/Auto encodeur.m4a` (≈27 min), un enregistrement
de cours sans support de slides associé, et a demandé la mise à jour des documents de cours et de
révision à partir de son contenu.

## Transcription

Fichier converti en WAV 16 kHz mono (`ffmpeg`), transcrit avec whisper.cpp (modèle `large-v3-turbo`,
VAD Silero, GPU AMD via Vulkan) sur la VM personnelle de l'utilisateur dédiée à l'inférence locale, puis
déposé dans [`docs/02-sprint-2/02-transcriptions/11-jour-4-cours-auto-encodeurs.txt`](../02-transcriptions/11-jour-4-cours-auto-encodeurs.txt).
Une ligne d'hallucination de fin d'enregistrement (« Sous-titrage Société Radio-Canada », artefact
classique de Whisper sur un silence de fin de piste) a été retirée avant dépôt.

Contenu : explication de l'architecture encodeur-décodeur et de l'espace latent, discussion en
questions-réponses (multi-type d'entrée, encodeur seul/décodeur seul/encodeur-décodeur, lien avec les
LLM), variantes d'auto-encodeurs et leurs usages, retour sur les résultats de TP des apprenants
(bois, pilules, `metal_nut`), et consignes de fin de séance pour le rapport de TP.

## Correspondance avec l'état du dépôt

La quasi-totalité du contenu théorique oral (architecture, hyperparamètre de l'espace latent, variantes
débruiteur/parcimonieux/convolutif/VAE, applications) était déjà couverte, en des termes très proches,
par la section « Auto-encodeurs (aperçu) » de la [fiche 14](../04-revisions/14-reseaux-de-neurones-mlp-cnn-transfer-learning.md)
et par la [fiche 15](../04-revisions/15-auto-encodeur-heatmaps-ratio-compression-ssim.md). Aucune
consigne de TP nouvelle : le contenu recoupe `docs/02-sprint-2/05-consignes/b6_deep_learning_auto_encodeur.md`.

Trois apports réellement nouveaux, absents des fiches avant ce jour, ajoutés à la fiche 14 :

- Un encodeur et un décodeur peuvent porter sur deux types de données différents (exemple donné à
  l'oral : encoder une image en vecteur, décoder ce vecteur en légende textuelle).
- Un auto-encodeur entraîné sur un seul type d'entrée ne sait pas en traiter un autre à l'inférence :
  il faut soit l'entraîner conjointement sur les deux types dès le départ, soit utiliser deux modèles
  séparés.
- Nuance de la formatrice sur le vocabulaire « decoder-only » des LLM : un abus de langage courant, car
  décoder suppose toujours qu'une représentation a été encodée quelque part au préalable.

Une remarque orale non chiffrée sur des différences de détection par sous-type de défaut (bois : trous et
rayures mieux détectés que les taches ; `metal_nut` : déformation plus visible qu'un scratch) a été
ajoutée à la fiche 15, explicitement marquée comme non quantifiée dans ce dépôt — à ne pas confondre avec
les métriques mesurées de cette même fiche.

## Non retenu

- Les instructions de fin de séance (rendre un rapport, encapsuler le code en modules Python plutôt
  qu'un seul notebook) sont des consignes organisationnelles, déjà couvertes en substance par les
  livrables attendus de `b6_deep_learning_auto_encodeur.md` : pas de nouvelle fiche.
- Le rappel du compromis métier « mieux vaut trop d'alertes que pas assez » recoupe exactement la section
  dédiée déjà présente dans la fiche 15 ; aucun ajout pour éviter la redite.

## Points à retenir pour le QCM

- Ce cours n'apporte pas de nouveau support PDF ; son contenu oral recoupe très largement les fiches 14
  et 15 déjà rédigées, à trois nuances théoriques près (voir ci-dessus).

## Points à savoir expliquer lors de la soutenance

- Pourquoi un encodeur-décodeur peut relier deux types de données différents, avec l'exemple de la
  légende d'image.
- Pourquoi qualifier un LLM de « decoder-only » est, au sens strict, un abus de langage.
