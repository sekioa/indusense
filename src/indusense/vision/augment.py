"""Pipeline d'augmentation Albumentations pour les images saines d'entraînement."""

import albumentations as A
import cv2
import numpy as np


def build_augmentation_pipeline(*, seed: int = 42) -> A.Compose:
    """Construit le pipeline d'augmentation appliqué aux saines d'entraînement.

    `wood` est une **texture** sans orientation privilégiée : contrairement à un
    objet centré comme `metal_nut`, un retournement ou une petite rotation
    produisent toujours un aspect plausible de planche de bois. Les
    transformations restent malgré tout modérées pour ne pas fabriquer de
    motifs de grain irréalistes :

    - `HorizontalFlip` / `VerticalFlip` : le grain du bois n'a pas de sens
      "haut/bas" ou "gauche/droite" fixe.
    - `Rotate` (± 15°) : rotation légère, une rotation forte déformerait la
      texture au-delà de ce qu'on observe en production.
    - `Affine` (translation/échelle légères) : simule un cadrage caméra
      imparfait sans déformer la texture.
    - `RandomBrightnessContrast` : simule les variations d'éclairage.
    """
    return A.Compose(
        [
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.Rotate(limit=15, border_mode=cv2.BORDER_REFLECT_101, p=0.7),
            A.Affine(
                translate_percent=0.05,
                scale=(0.95, 1.05),
                border_mode=cv2.BORDER_REFLECT_101,
                p=0.5,
            ),
            A.RandomBrightnessContrast(brightness_limit=0.15, contrast_limit=0.15, p=0.5),
        ],
        seed=seed,
    )


def apply_augmentations(image: np.ndarray, pipeline: A.Compose, n_samples: int) -> list[np.ndarray]:
    """Applique le pipeline ``n_samples`` fois à une image normalisée ``[0, 1]``."""
    return [pipeline(image=image)["image"] for _ in range(n_samples)]


def augment_batch(images: np.ndarray, pipeline: A.Compose) -> np.ndarray:
    """Applique une transformation fraîche du pipeline à chaque image d'un lot pré-chargé.

    Utilisé pour régénérer une version augmentée différente des saines d'entraînement à
    chaque époque, sans recharger les images depuis le disque.
    """
    return np.stack([pipeline(image=image)["image"] for image in images], axis=0)
