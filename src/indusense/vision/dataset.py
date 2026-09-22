"""Chargement, normalisation et découpage du dataset MVTec AD."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


DEFAULT_DATA_ROOT = Path("datas/deep-learning")
DEFAULT_CATEGORY = "wood"
DEFAULT_IMAGE_SIZE = 256


def resolve_category_root(category: str, *, data_root: Path = DEFAULT_DATA_ROOT) -> Path:
    """Localise le dossier racine d'une catégorie MVTec AD.

    L'extraction de l'archive Hugging Face imbrique le dossier de la catégorie
    une seconde fois (``wood/wood/...``) : les deux emplacements sont testés.
    """
    nested_root = data_root / category / category
    flat_root = data_root / category
    for candidate in (nested_root, flat_root):
        if (candidate / "train" / "good").is_dir():
            return candidate
    raise FileNotFoundError(
        f"Catégorie MVTec AD introuvable pour {category!r} sous {data_root} "
        f"(testé : {nested_root} et {flat_root})."
    )


def list_defect_categories(category_root: Path) -> list[str]:
    """Liste les sous-dossiers de défauts présents dans ``test/`` (hors ``good``)."""
    test_root = category_root / "test"
    return sorted(
        entry.name for entry in test_root.iterdir() if entry.is_dir() and entry.name != "good"
    )


def list_image_paths(category_root: Path, split: str, subset: str) -> list[Path]:
    """Liste les chemins d'images d'un sous-dossier ``<split>/<subset>`` trié."""
    subset_root = category_root / split / subset
    if not subset_root.is_dir():
        raise FileNotFoundError(f"Sous-dossier introuvable : {subset_root}")
    return sorted(subset_root.glob("*.png"))


def load_image(path: Path, image_size: int = DEFAULT_IMAGE_SIZE) -> np.ndarray:
    """Charge une image RGB, la redimensionne et la normalise dans ``[0, 1]``."""
    with Image.open(path) as image:
        resized = image.convert("RGB").resize((image_size, image_size), Image.BILINEAR)
        return np.asarray(resized, dtype=np.float32) / 255.0


def load_image_batch(paths: list[Path], image_size: int = DEFAULT_IMAGE_SIZE) -> np.ndarray:
    """Charge plusieurs images dans un seul tableau ``(N, H, W, 3)`` normalisé."""
    return np.stack([load_image(path, image_size) for path in paths], axis=0)


def load_ground_truth_mask(path: Path, image_size: int = DEFAULT_IMAGE_SIZE) -> np.ndarray:
    """Charge un masque de vérité terrain et le binarise après redimensionnement."""
    with Image.open(path) as mask:
        resized = mask.convert("L").resize((image_size, image_size), Image.NEAREST)
        return (np.asarray(resized, dtype=np.float32) / 255.0 > 0.5).astype(np.float32)


def list_mask_paths(category_root: Path, defect: str) -> list[Path]:
    """Liste les chemins des masques de vérité terrain d'une catégorie de défaut, triés.

    Le tri par ordre alphabétique des noms de fichiers (``000_mask.png``, ``001_mask.png``, ...)
    correspond à l'ordre des images de ``list_image_paths(category_root, 'test', defect)`` : les deux
    dossiers partagent la même numérotation, image par image.
    """
    mask_root = category_root / "ground_truth" / defect
    if not mask_root.is_dir():
        raise FileNotFoundError(f"Dossier de masques introuvable : {mask_root}")
    return sorted(mask_root.glob("*_mask.png"))


def load_mask_batch(paths: list[Path], image_size: int = DEFAULT_IMAGE_SIZE) -> np.ndarray:
    """Charge plusieurs masques de vérité terrain dans un seul tableau ``(N, H, W)`` binaire."""
    return np.stack([load_ground_truth_mask(path, image_size) for path in paths], axis=0)


@dataclass(frozen=True)
class TrainValidationSplit:
    """Chemins des images saines d'entraînement et de validation."""

    train_paths: list[Path]
    validation_paths: list[Path]


def split_train_validation(
    good_paths: list[Path],
    *,
    validation_fraction: float = 0.15,
    seed: int = 42,
) -> TrainValidationSplit:
    """Réserve une fraction des images saines pour la validation du seuil.

    Le tirage est aléatoire mais reproductible (``seed`` fixé) : la validation
    ne recouvre jamais l'entraînement et sert uniquement, en partie 2, à
    calibrer le seuil de détection d'anomalie sur des images saines inédites.
    """
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction doit être strictement entre 0 et 1.")

    shuffled_paths = list(good_paths)
    np.random.default_rng(seed).shuffle(shuffled_paths)
    validation_size = max(1, round(len(shuffled_paths) * validation_fraction))
    return TrainValidationSplit(
        train_paths=shuffled_paths[validation_size:],
        validation_paths=shuffled_paths[:validation_size],
    )
