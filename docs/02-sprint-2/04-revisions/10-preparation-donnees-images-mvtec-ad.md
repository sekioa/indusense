# Préparation des données images pour un auto-encodeur de détection d'anomalies (MVTec AD)

## Définition et objectif

La **détection d'anomalies par reconstruction** entraîne un auto-encodeur convolutif à reconstruire uniquement des images **saines**. Une image que le modèle reconstruit mal est jugée suspecte. Cette approche ne nécessite **aucun défaut annoté**, contrairement à une détection/localisation supervisée (type YOLO) qui exigerait des milliers d'exemples de défauts étiquetés. C'est une approche pédagogique et un *baseline* : sa performance dépend fortement de l'architecture et du seuil retenus, pas de l'état de l'art.

L'objectif de cette étape de préparation est de fournir à ce futur auto-encodeur des images chargées, redimensionnées, normalisées, correctement réparties entre `train`/`validation`/`test`, et éventuellement augmentées — sans quoi le modèle de la partie 2 ne peut pas bien fonctionner.

## Notions essentielles

- **MVTec AD** : jeu de données académique de détection d'anomalies industrielles. Chaque catégorie fournit des images saines pour l'entraînement, et des images défectueuses **avec masques de vérité terrain** (`ground_truth/<defect>/*_mask.png`) pour l'évaluation pixel.
- **Normalisation `[0, 1]`** : diviser les pixels bruts (0–255) par 255 pour éviter qu'une forte amplitude de valeurs ne domine l'apprentissage. Elle ne recentre pas et ne standardise pas par canal.
- **Split train/validation** sur les images **saines uniquement** : le train ajuste le futur auto-encodeur, la validation (saine, jamais vue à l'entraînement) sert à calibrer le seuil de détection en partie 2. Le test (saines + défauts) reste à l'écart jusqu'à l'évaluation finale.
- **Augmentation de données (Albumentations)** : appliquée **uniquement aux saines d'entraînement**, jamais au test. Elle élargit la notion de « normal » vue par le modèle sans jamais rapprocher une image saine d'une configuration défectueuse nommée.
- **Objet centré vs texture** : la pertinence d'une augmentation géométrique dépend de la nature de la catégorie. Un objet centré et orienté (ex. `metal_nut`) est sensible aux flips/rotations fortes, qui peuvent imiter un défaut réel (ex. le défaut `flip` de `metal_nut` — une pièce montée à l'envers). Une texture homogène sans orientation privilégiée (ex. `wood`) tolère mieux ces mêmes transformations.

## Démarche

1. Localiser la racine de la catégorie (attention aux imbrications de dossiers liées à l'extraction de l'archive).
2. Charger les images en RGB, redimensionner (256×256 ou 128×128), normaliser dans `[0, 1]`.
3. Réserver une fraction (≈ 15 %) des saines d'entraînement pour la validation, sans recouvrement avec le train.
4. Vérifier visuellement le chargement (saines vs chaque catégorie de défaut).
5. Construire un pipeline d'augmentation pour les saines d'entraînement, en le justifiant selon que la catégorie est un objet centré ou une texture.
6. Vérifier visuellement original vs versions augmentées : aucune version augmentée ne doit ressembler à un défaut nommé.

## Exemple concret : catégorie `wood`

Implémentation de référence : [`dataset.py`](../../../src/indusense/vision/dataset.py) et [`augment.py`](../../../src/indusense/vision/augment.py) dans `src/indusense/vision/`, utilisés par le notebook [`01-preparation-donnees-augmentation-wood.ipynb`](../../../notebooks/02-sprint-2/02-deep-learning-donnees/01-preparation-donnees-augmentation-wood.ipynb).

- Catégorie `wood` (texture, planche de bois) au lieu de `metal_nut` (objet mécanique centré) : **247** images saines d'entraînement, **5** catégories de défauts en test (`color` 8, `combined` 11, `hole` 10, `liquid` 10, `scratch` 21), contre 4 défauts pour `metal_nut` (`bent`, `color`, `flip`, `scratch`).
- Split : **210** images pour le train, **37** (≈ 15 %) pour la validation, sans recouvrement.
- Chargement : images `(256, 256, 3)` en `float32`, valeurs observées dans `[0, 1]`.
- Augmentation retenue : `HorizontalFlip`, `VerticalFlip`, `Rotate(±15°)`, `Affine` (translation/échelle légères), `RandomBrightnessContrast`, avec un `border_mode` en réflexion (`cv2.BORDER_REFLECT_101`) pour prolonger la texture au lieu d'ajouter une bordure noire artificielle.
- Justification : `wood` n'a pas de défaut lié à une orientation (contrairement au `flip` de `metal_nut`), donc les flips et rotations légères sont pertinents. La rotation reste limitée à ±15° (pas 90°/180°) pour ne pas déformer le grain de façon irréaliste, et les variations de luminosité/contraste restent modérées.

## Généralisation : pièges de découpage, déséquilibre et versioning

Le support de séance « Préparation d'un dataset d'images » (S15) présente ces notions de façon plus générale, au-delà du seul cas de l'auto-encodeur InduSense — utile pour toute vision industrielle, y compris une approche supervisée avec défauts annotés.

- **Pièges du découpage train/validation/test**, à vérifier systématiquement : fuite de données (*data leakage*) entre les jeux ; images d'une même pièce ou série réparties dans plusieurs jeux (une pièce doit rester entière dans un seul jeu) ; proportions non représentatives de la réalité terrain.
- **Redimensionnement** : préserver le ratio quand c'est possible (padding plutôt que déformation), choisir une résolution suffisante pour que le défaut reste visible après redimensionnement, et documenter la méthode d'interpolation utilisée (bilinéaire, bicubique, plus proche voisin).
- **Stratégies génériques face au déséquilibre** (au-delà de l'approche par auto-encodeur qui le contourne en n'apprenant que le normal) : suréchantillonnage ou augmentation ciblée des défauts, pondération des classes dans la fonction de coût, et choix de métriques adaptées (rappel, F1) plutôt que l'accuracy — voir la [fiche métriques](03-metriques-evaluation-modeles-machine-learning.md).
- **Qualité des étiquettes** : une étiquette est une vérité terrain dont la qualité plafonne celle du modèle. Distinguer les niveaux d'annotation (étiquette image, boîte englobante, masque pixel — MVTec AD fournit ce dernier niveau), définir une convention claire de ce qu'est un défaut, et faire arbitrer les cas ambigus par un expert métier. En détection d'anomalies non supervisée (l'approche retenue ici), peu ou pas d'étiquettes de défaut sont nécessaires à l'entraînement — seulement à l'évaluation.
- **Versionner un dataset image** : au-delà du code, versionner les images (souvent hors Git, via un stockage dédié), les métadonnées (source, date, capteur, conditions de prise de vue) et les artefacts (découpage train/val/test, statistiques de normalisation, étiquettes). Outils cités : DVC, Git-LFS, ou a minima une convention de nommage stricte accompagnée d'un fichier de métadonnées. Règle d'or : un même identifiant de version doit toujours produire le même dataset. **Non mis en place dans ce dépôt** à ce jour : les images `datas/deep-learning/wood/` sont suivies par une simple archive (`wood.tar.xz`), sans DVC ni Git-LFS.

### Exemples et nuances donnés à l'oral

- **Similarité train / production** : le formateur cite un projet de contrôle qualité où les images d'entraînement avaient été prises dans une pièce bien éclairée, alors que la production réelle l'était moins — le modèle généralisait mal. Principe rappelé : les données d'entraînement doivent être représentatives des conditions de test **et** de production, pas seulement d'un jeu de test propre.
- **Augmentation ciblée sur les échecs du modèle** : sur un projet de détection de plaques d'égout rondes par drone, la rotation était jugée inutile (objet sans orientation), mais le modèle échouait sur les plaques partiellement dans l'ombre. Le formateur a construit manuellement des images synthétiques avec ombre, puis démultiplié ces cas par symétries/rotations — amélioration nette des résultats. Illustration concrète du principe « augmenter sur les cas d'échec observés », plus qu'une liste générique de transformations.
- **Cohérence physique, exemple affiné** : une bouteille photographiée debout ne doit jamais être tournée à l'horizontale ou à l'envers (jamais observée ainsi en production) ; une symétrie axiale verticale (miroir gauche-droite) reste en revanche acceptable, **sauf** si l'étiquette porte du texte, qui deviendrait alors illisible/inversé de façon irréaliste.
- **Fuite de données lors de la standardisation** : si la normalisation va au-delà de la simple division par 255 (moyenne/écart-type par canal), ces statistiques doivent être calculées **uniquement sur le train**, puis appliquées telles quelles à la validation et au test — jamais recalculées sur ces derniers, sous peine de fuite de données.
- **Catégories MVTec AD citées comme plus faciles à détecter** : `hazelnut` et `metal_nut` sont présentées comme donnant de bons résultats pédagogiques, `bottle` comme ayant peu de défauts bien visibles. Une indication complémentaire au choix de `wood` déjà retenu et documenté dans ce dépôt.

## Erreurs fréquentes et bonnes pratiques

- Appliquer l'augmentation aux images de test ou de validation : elle doit rester réservée aux saines d'entraînement.
- Copier telle quelle une augmentation « objet centré » (ex. flips forts sur `metal_nut`) sur une texture, ou l'inverse, sans reconsidérer si une transformation peut imiter un défaut nommé.
- Oublier de vérifier que chaque image de défaut possède bien son masque `ground_truth` correspondant avant la partie 2.
- Laisser une bordure noire (`border_mode` constant) après rotation/translation : elle introduit un artefact que le modèle pourrait apprendre à tort comme un indice de « normal ».
- Vérifier la compatibilité de version Python avant d'installer un groupe de dépendances Deep Learning : TensorFlow (2.21.0) ne publie pas de roue pour Python 3.14 (`cp314`, sorti trop récemment pour que la chaîne de build TensorFlow ait suivi), contrairement à Albumentations, Pillow, OpenCV et scikit-image qui le supportent déjà. La préparation des données (partie 1) ne dépend pas de TensorFlow.

  **Solution retenue dans ce projet** : `requires-python` a été assoupli à `>=3.13` et `tensorflow>=2.21.0 ; python_version < '3.14'` a été ajouté au groupe `dl` avec un **marqueur d'environnement** — `uv sync` l'ignore sous Python 3.14 (environnement principal `.venv`, inchangé) et l'installe sous Python 3.13. Un second environnement dédié est créé à côté du principal, sans le remplacer :

  ```bash
  uv venv --python 3.13 .venv-py313
  UV_PROJECT_ENVIRONMENT=.venv-py313 uv sync --python 3.13 --group dl --group dev
  .venv-py313/Scripts/python -m ipykernel install --user --name indusense-py313-tf --display-name "Python 3.13 (indusense, TensorFlow)"
  ```

  Le notebook de la partie 2 se sélectionne alors le noyau Jupyter **`Python 3.13 (indusense, TensorFlow)`**, pendant que tous les autres notebooks du projet gardent le noyau `python3` par défaut (3.14).
- **GPU AMD (ex. RX 9070 XT, RDNA4/gfx1201) sous Windows** : ROCm 7.2.1 supporte officiellement cette famille de GPU, mais **seul PyTorch** figure dans la matrice de compatibilité Windows d'AMD — TensorFlow+ROCm reste documenté pour Linux uniquement, et `tensorflow-directml-plugin` (alternative Microsoft) est en développement arrêté, limité à `tensorflow-cpu` ≤ 2.12 et Python < 3.11. Pour entraîner sur GPU AMD sous Windows, il faut donc **PyTorch**, avec les wheels ROCm officielles (Python 3.12 requis, pilote Adrenalin ≥ 26.2.2) :

  ```bash
  uv venv --python 3.12 .venv-py312-rocm
  uv pip install --python .venv-py312-rocm/Scripts/python.exe --no-cache \
    https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/rocm_sdk_core-7.2.1-py3-none-win_amd64.whl \
    https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/rocm_sdk_devel-7.2.1-py3-none-win_amd64.whl \
    https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/rocm_sdk_libraries_custom-7.2.1-py3-none-win_amd64.whl \
    https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/rocm-7.2.1.tar.gz
  uv pip install --python .venv-py312-rocm/Scripts/python.exe --no-cache \
    "https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/torch-2.9.1%2Brocm7.2.1-cp312-cp312-win_amd64.whl" \
    "https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/torchaudio-2.9.1%2Brocm7.2.1-cp312-cp312-win_amd64.whl" \
    "https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/torchvision-0.24.1%2Brocm7.2.1-cp312-cp312-win_amd64.whl"
  ```

  Ces wheels (URLs directes, ~2,2 Go) ne sont pas déclarées dans `pyproject.toml` : spécifiques à Windows et à cette famille de GPU, elles ne seraient pas reproductibles sur une autre machine. Cet environnement est donc installé manuellement, hors gestion `uv sync`.

  **Vérifié** sur une RX 9070 XT (pilote Adrenalin du 17/08/2026) : `torch.cuda.is_available()` renvoie `True`, `torch.cuda.get_device_name(0)` renvoie `'AMD Radeon RX 9070 XT'`, et un produit matriciel 4096×4096 s'exécute correctement sur le GPU. Trois noyaux Jupyter coexistent donc sur ce projet : `python3` (3.14, par défaut), `indusense-py313-tf` (TensorFlow, CPU) et `indusense-py312-rocm` (PyTorch, GPU AMD).
- Installer à la fois `opencv-python` et `opencv-python-headless` : les deux fournissent le module `cv2` et peuvent entrer en conflit. Albumentations installe déjà `opencv-python-headless` en dépendance ; il est inutile d'ajouter `opencv-python` en plus pour un usage sans interface graphique.

## Points à retenir pour le QCM

- L'auto-encodeur de détection d'anomalies s'entraîne uniquement sur des images saines.
- La normalisation `[0, 1]` s'obtient par simple division par 255.
- La validation (saine) sert à calibrer le seuil, pas à entraîner le modèle.
- L'augmentation ne s'applique jamais aux images de test.
- La pertinence d'une augmentation géométrique dépend de la nature de l'objet (centré/orienté vs texture).
- Un dataset versionné doit toujours produire le même contenu pour un même identifiant de version.

## Points à savoir expliquer lors de la soutenance

- Pourquoi l'approche par reconstruction ne nécessite aucun défaut annoté, et quelle est sa limite principale.
- Pourquoi la validation est constituée d'images saines et non de défauts.
- Pourquoi une augmentation pertinente pour `metal_nut` (objet) ne l'est pas nécessairement pour `wood` (texture), et inversement.
- Comment vérifier qu'une transformation d'augmentation ne rapproche pas une image saine d'un défaut nommé.
- Pourquoi la partie 2 (entraînement) peut nécessiter un environnement Python différent de la partie 1.
- Ce que versionner dans un dataset image au-delà des images elles-mêmes, et pourquoi ce n'est pas encore en place ici.

## Sources du cours

- `13_Preparation_dataset_images.pdf`, support Aelion « Préparation d'un dataset d'images » (Séance 15), diapositives 1 à 16.
- [Transcription de la séance](../02-transcriptions/10-jour-3-preparation-dataset-images-autoencodeur.txt) (exemples oraux : éclairage, plaques d'égout, bouteilles, standardisation).
