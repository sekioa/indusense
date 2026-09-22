# Sprint 2 - 2026-09-21 : revue des cours du jour (POC ML, MLflow, métriques ROC/PR AUC, Deep Learning, dataset images)

## Objectif concret

L'utilisateur a déposé dans `docs/02-sprint-2/01-cours/` les slides de cinq séances (`07_poc_ml.pdf`, `08_mlflow_aelion.pdf`, `10_metriques_ROC_PR_AUC.pdf`, `12_Deep_Learning.pdf`, `13_Preparation_dataset_images.pdf`) ainsi que quatre enregistrements vidéo dans `docs/02-sprint-2/01-cours/videos/` (« Sprint 2 - Cours 2109 #1 » à « #4 »), en demandant une mise à jour des notes de cours, des fiches de révision et des notebooks.

## Contenu vidéo : transcription obtenue après coup

Cette revue a d'abord été rédigée uniquement à partir des cinq PDF de slides, faute d'outil de transcription disponible dans l'environnement de départ. Les quatre vidéos ont ensuite été transcrites (Whisper local, modèle `large-v3-turbo`, détection d'activité vocale) et déposées dans `docs/02-sprint-2/02-transcriptions/` :

- [`07-jour-3-poc-ml-metriques-roc-pr-auc.txt`](../02-transcriptions/07-jour-3-poc-ml-metriques-roc-pr-auc.txt) (≈100 min — POC ML + rappel ROC/PR-AUC, correspond à `07_poc_ml.pdf` et `10_metriques_ROC_PR_AUC.pdf`)
- [`08-jour-3-revue-tp-transition-deep-learning.txt`](../02-transcriptions/08-jour-3-revue-tp-transition-deep-learning.txt) (≈5 min — fin de la revue de TP, annonce du Deep Learning l'après-midi)
- [`09-jour-3-deep-learning-reseaux-de-neurones.txt`](../02-transcriptions/09-jour-3-deep-learning-reseaux-de-neurones.txt) (≈63 min — correspond à `12_Deep_Learning.pdf`)
- [`10-jour-3-preparation-dataset-images-autoencodeur.txt`](../02-transcriptions/10-jour-3-preparation-dataset-images-autoencodeur.txt) (≈38 min — correspond à `13_Preparation_dataset_images.pdf`)

Constat après vérification par mots-clés dans les transcriptions : **aucune des quatre vidéos ne mentionne MLflow, le Model Registry ni pytest**. Le support `08_mlflow_aelion.pdf` (Séance 13) n'a donc pas de contrepartie orale dans ce lot de vidéos — soit cette séance a eu lieu un autre jour non fourni, soit son enregistrement n'a pas été déposé. La [fiche 13](../04-revisions/13-mlflow-tracking-autolog-model-registry.md) reste donc construite uniquement à partir des slides, comme les autres avant cette transcription.

Les horodatages des transcriptions sont approximatifs (segmentation par détection d'activité vocale) et le texte peut contenir des erreurs de reconnaissance ; à corriger éditorialement si réutilisé tel quel.

## Correspondance entre les slides et l'état du dépôt

| Support | Séance | Couverture avant ce jour | Action réalisée |
|---|---|---|---|
| `07_poc_ml.pdf` | S11 — POC ML & métriques métier | Métriques déjà couvertes en détail (fiche 03) ; règle des 3 baselines, coût métier € et plan d'expérience absents | Nouvelle [fiche 12](../04-revisions/12-poc-ml-baseline-cout-metier-plan-experience.md) |
| `08_mlflow_aelion.pdf` | S13 — MLOps léger : MLflow | Méthode et résultats des campagnes déjà documentés ([fiche notebook-spécifique](../../revisions/mlflow-et-optimisation-reproductible.md)) ; architecture générale de l'outil, autolog, Model Registry et tests pytest absents | Nouvelle [fiche 13](../04-revisions/13-mlflow-tracking-autolog-model-registry.md) |
| `10_metriques_ROC_PR_AUC.pdf` | Rappel métriques | Déjà entièrement couvert par la [fiche 03](../04-revisions/03-metriques-evaluation-modeles-machine-learning.md) (sections ROC-AUC et PR-AUC) | Ajout d'un tableau de traduction technique → métier et des sources dans la fiche 03 |
| `12_Deep_Learning.pdf` | Deep Learning (fondations) | Seule l'application « auto-encodeur InduSense » était documentée (fiche 11) ; MLP, rétropropagation, optimiseurs, régularisation, CNN, architectures classiques, transfer learning absents | Nouvelle [fiche 14](../04-revisions/14-reseaux-de-neurones-mlp-cnn-transfer-learning.md) |
| `13_Preparation_dataset_images.pdf` | S15 — Préparation dataset images | Cas MVTec AD/wood déjà très détaillé (fiche 10) ; pièges génériques de découpage, stratégies de déséquilibre hors auto-encodeur, versioning dataset (DVC/Git-LFS) absents | Section « Généralisation » ajoutée à la [fiche 10](../04-revisions/10-preparation-donnees-images-mvtec-ad.md) |

Constat général : une bonne partie du contenu de ces cinq séances était déjà appliquée et documentée dans ce dépôt lors de sprints précédents (notebooks de comparaison de modèles, campagnes MLflow, préparation du dataset `wood`, auto-encodeur TensorFlow/PyTorch). Le travail du jour a donc surtout consisté à **compléter la couche théorique/méthodologique manquante** (POC ML formel, mécanique interne de MLflow, fondations MLP/CNN) plutôt qu'à découvrir un thème entièrement nouveau.

## Écart identifié : Model Registry et tests pytest (S13)

Le TP de la séance 13 demande, en plus du tracking déjà en place dans les notebooks 06 et 07 (`notebooks/02-sprint-2/01-maintenance-predictive/`) :

- la promotion du meilleur run en `Staging` dans le Model Registry MLflow ;
- des tests `pytest` validant le modèle candidate (chargement, prédiction, seuil de rappel) ;
- un `README.md` du modèle candidate.

Vérification faite ce jour : `pytest` n'est pas installé dans `.venv`, et aucun code de ce dépôt n'appelle `register_model` ni `transition_model_version_stage`. Ce point est **volontairement laissé en l'état** plutôt que traité par un ajout de notebook non exécuté et non vérifié : l'implémenter correctement demande de relancer une campagne d'entraînement complète (`.mlflow/` n'existe pas localement sur cette machine, il est recréé par le notebook) puis de valider effectivement les tests, ce qui dépasse une simple mise à jour de notes. Le détail est documenté dans la [fiche 13](../04-revisions/13-mlflow-tracking-autolog-model-registry.md#exemple-concret-dans-ce-dépôt) pour être repris lors d'une prochaine séance de travail sur ce dépôt.

## Notebooks : aucune modification de code ce jour

Après vérification, les notebooks existants (`01` à `07` dans `01-maintenance-predictive/`, `01` à `07` dans `02-deep-learning-donnees/`) couvrent déjà, avec du code exécuté et vérifié lors de sessions antérieures, l'essentiel des TP décrits par ces cinq supports : comparaison LR/RF/HistGradientBoosting (règle des 3 baselines, avec XGBoost sciemment remplacé par HistGradientBoosting — non installé, absence documentée dans les notebooks 01-03), tracking MLflow de deux campagnes (Random Search, Optuna), préparation et augmentation du dataset `wood`, auto-encodeur convolutif TensorFlow et PyTorch (CPU/GPU). Aucune ligne de code n'a donc été changée dans les notebooks : le seul écart réel (Model Registry + pytest, ci-dessus) demande une exécution complète plutôt qu'une retouche ponctuelle, et reste sciemment non fait à ce stade.

## Points à retenir pour le QCM

- Cinq nouveaux supports datés du 21/09/2026 : POC ML (S11), MLflow (S13), rappel ROC/PR AUC, Deep Learning, préparation dataset images (S15).
- Les quatre vidéos ont finalement été transcrites (voir section précédente) ; le contenu oral a été comparé aux fiches et a apporté quelques précisions (early stopping, arbitrage précision/rappel, exemples d'augmentation, standardisation) répercutées dans les fiches 10, 12 et 14.
- Le Model Registry MLflow et les tests pytest du candidate model restent à implémenter dans ce dépôt.

## Apports de la transcription par rapport aux slides

Une lecture complète des quatre transcriptions, comparée aux fiches déjà rédigées à partir des seuls PDF, confirme que l'essentiel du contenu oral recoupe les slides (aucun ajout substantiel pour les fiches 03 et 13). Quelques précisions orales, absentes des slides, ont été ajoutées :

- **Fiche 12** : ordres de grandeur d'hyperparamètres Random Forest, méthode Random Search → Optuna en deux passes, principe de l'early stopping en boosting (chiffres oraux de nombre d'arbres marqués comme à vérifier, trop bas pour un usage réel), et une précision importante : l'arbitrage précision/rappel doit être fixé par le data scientist en amont, pas demandé au métier après coup.
- **Fiche 10** : anecdote sur le décalage d'éclairage train/production, exemple d'augmentation ciblée sur les cas d'échec (détection de plaques d'égout), nuance sur la symétrie d'une bouteille (interdite si étiquette texte), et rappel que les statistiques de standardisation (moyenne/écart-type) doivent être calculées uniquement sur le train.
- **Fiche 14** : motif d'architecture « pyramide » (neurones croissants puis décroissants par couche).

Un exemple chiffré donné par une apprenante (variation de PR-AUC en changeant de seuil) a été **volontairement écarté** : la définition même du PR-AUC (indépendant du seuil) rend cet exemple incohérent tel qu'il a été formulé à l'oral, probablement une confusion avec précision/rappel au seuil — à ne pas réutiliser sans clarification.

**Ressource mentionnée mais non retrouvée dans le dépôt** : dans `08-jour-3-revue-tp-transition-deep-learning.txt`, un apprenant évoque un fichier partagé par le formateur, un « projet MLDL Pipeline » au format Markdown, décrit comme reprenant toute la méthodologie du machine learning, déposé dans les ressources partagées « sprint 2 ». Aucun fichier de ce nom n'existe dans ce dépôt (`docs/` ou ailleurs) : si l'utilisateur y a accès, cela pourrait valoir la peine de le récupérer et de le comparer au contenu déjà versionné.

## Points à savoir expliquer lors de la soutenance

- Ce qui, dans les cinq séances du jour, était déjà pratiqué dans le dépôt avant même d'en recevoir le support théorique correspondant (ordre pédagogique inversé, fréquent sur un fil rouge).
- Pourquoi XGBoost, mentionné dans le support S11, n'est pas utilisé dans ce dépôt.
- L'état d'avancement réel du volet MLOps (tracking fait, registry et tests restant à faire) et pourquoi ce n'est pas un oubli mais un choix assumé de ne pas livrer un ajout non vérifié.
