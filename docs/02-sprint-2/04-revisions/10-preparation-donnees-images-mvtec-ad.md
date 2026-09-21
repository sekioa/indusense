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

## Points à savoir expliquer lors de la soutenance

- Pourquoi l'approche par reconstruction ne nécessite aucun défaut annoté, et quelle est sa limite principale.
- Pourquoi la validation est constituée d'images saines et non de défauts.
- Pourquoi une augmentation pertinente pour `metal_nut` (objet) ne l'est pas nécessairement pour `wood` (texture), et inversement.
- Comment vérifier qu'une transformation d'augmentation ne rapproche pas une image saine d'un défaut nommé.
- Pourquoi la partie 2 (entraînement) peut nécessiter un environnement Python différent de la partie 1.
