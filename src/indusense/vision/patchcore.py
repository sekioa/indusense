"""PatchCore (Roth et al., 2022) — détecteur d'anomalies par mémoire de features pré-entraînées.

**Modèle retenu pour la production**, après comparaison empirique avec l'auto-encodeur convolutif de
``autoencoder_torch.py`` : sur la catégorie ``wood``, PatchCore atteint un rappel de 100 % (0 défaut
manqué sur 60) pour 2,7 % de fausses alertes sur la validation, alors que l'auto-encodeur plafonne à un
rappel de 81,7 % *quel que soit le seuil choisi* — une limite du score de reconstruction lui-même, pas
de la politique de seuil. Voir
``notebooks/02-sprint-2/02-deep-learning-donnees/03-choix-final-detection-maximale-wood.ipynb`` et la
fiche de révision ``docs/02-sprint-2/04-revisions/15-auto-encodeur-heatmaps-ratio-compression-ssim.md``.

Contrairement à l'auto-encodeur, PatchCore n'entraîne aucun poids par rétropropagation : il extrait des
features d'un réseau pré-entraîné sur ImageNet (robuste aux variations photométriques), les stocke dans
une mémoire de patchs sains sous-échantillonnée par *coreset*, puis score chaque patch de test par sa
distance au plus proche voisin dans cette mémoire.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from anomalib.models.image.patchcore.torch_model import PatchcoreModel

from indusense.vision.anomaly import choose_threshold_percentile
from indusense.vision.autoencoder_torch import images_to_tensor

DEFAULT_BACKBONE = "wide_resnet50_2"
DEFAULT_LAYERS = ("layer2", "layer3")
DEFAULT_NUM_NEIGHBORS = 9
DEFAULT_SAMPLING_RATIO = 0.1
# Politique de seuil retenue après le balayage de 03-choix-final-detection-maximale-wood.ipynb :
# seule politique testée qui atteint un rappel de 100 % avec le moins de fausses alertes.
DEFAULT_THRESHOLD_PERCENTILE = 99.0

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def to_imagenet_tensor(images_hwc: np.ndarray, device: torch.device) -> torch.Tensor:
    """Convertit un lot d'images ``[0, 1]`` en tenseur normalisé ImageNet, sur ``device``.

    Le backbone de PatchCore est pré-entraîné sur ImageNet : il attend cette normalisation précise
    (moyenne/écart-type par canal), différente du simple ``[0, 1]`` utilisé par l'auto-encodeur.
    """
    tensor = images_to_tensor(images_hwc).to(device)
    mean = torch.tensor(IMAGENET_MEAN, device=device).view(1, 3, 1, 1)
    std = torch.tensor(IMAGENET_STD, device=device).view(1, 3, 1, 1)
    return (tensor - mean) / std


@dataclass
class PatchCoreConfig:
    """Hyperparamètres d'un détecteur PatchCore, sérialisables tels quels."""

    backbone: str = DEFAULT_BACKBONE
    layers: tuple[str, ...] = DEFAULT_LAYERS
    num_neighbors: int = DEFAULT_NUM_NEIGHBORS
    sampling_ratio: float = DEFAULT_SAMPLING_RATIO
    seed: int = 42


class PatchCoreDetector:
    """Détecteur d'anomalies PatchCore : mémoire de patchs sains + seuil de décision calibré.

    Usage typique :

    >>> detector = PatchCoreDetector(device=torch.device("cuda"))
    >>> detector.fit(train_good_images)                                  # mémoire de patchs
    >>> detector.calibrate_threshold(validation_good_images)             # seuil, 99e centile
    >>> scores = detector.score(test_images)                             # score par image
    >>> is_defect = detector.predict(test_images)                        # décision au seuil retenu
    >>> heatmap = detector.anomaly_map(test_images)                      # carte d'anomalie par pixel
    """

    def __init__(self, config: PatchCoreConfig | None = None, device: torch.device | None = None):
        self.config = config or PatchCoreConfig()
        self.device = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
        self.model: PatchcoreModel | None = None
        self.threshold: float | None = None

    def _require_fitted(self) -> PatchcoreModel:
        if self.model is None:
            raise RuntimeError("PatchCoreDetector n'est pas entraîné : appeler .fit(...) d'abord.")
        return self.model

    def fit(self, train_good_images: np.ndarray, batch_size: int = 16) -> "PatchCoreDetector":
        """Construit la mémoire de patchs à partir d'images saines uniquement, normalisées `[0, 1]`.

        Fixe la seed PyTorch (`config.seed`) avant le sous-échantillonnage coreset : le point de départ
        de l'algorithme glouton (`KCenterGreedy`, dans `anomalib`) est tiré aléatoirement et rend sinon
        la mémoire de patchs — donc le seuil calibré et les prédictions — différente d'un entraînement à
        l'autre. Cela stabilise fortement le résultat (vérifié : même matrice de confusion sur
        plusieurs essais avec `wood`), mais **la valeur numérique du seuil peut encore varier
        légèrement** d'un entraînement à l'autre : l'extraction de features du backbone convolutif sur
        GPU n'est pas garantie bit-exacte (contrairement à l'auto-encodeur `ConvAutoencoder`, vérifié
        déterministe — voir `docs/02-sprint-2/04-revisions/11-...md`), ce qui peut faire dévier
        l'algorithme glouton après quelques milliers d'itérations. Toujours recalibrer le seuil
        (`calibrate_threshold`) après chaque `fit`, jamais réutiliser un seuil d'un entraînement
        précédent avec un nouveau modèle.
        """
        torch.manual_seed(self.config.seed)
        model = PatchcoreModel(
            layers=list(self.config.layers),
            backbone=self.config.backbone,
            pre_trained=True,
            num_neighbors=self.config.num_neighbors,
        ).to(self.device)
        model.train()
        with torch.no_grad():
            for start in range(0, len(train_good_images), batch_size):
                batch = to_imagenet_tensor(train_good_images[start:start + batch_size], self.device)
                model(batch)
        model.subsample_embedding(sampling_ratio=self.config.sampling_ratio)
        model.eval()
        self.model = model
        return self

    @torch.no_grad()
    def _infer(self, images_hwc: np.ndarray, batch_size: int = 16) -> tuple[np.ndarray, np.ndarray]:
        model = self._require_fitted()
        scores, maps = [], []
        for start in range(0, len(images_hwc), batch_size):
            batch = to_imagenet_tensor(images_hwc[start:start + batch_size], self.device)
            output = model(batch)
            scores.append(output.pred_score.cpu().numpy())
            maps.append(output.anomaly_map.squeeze(1).cpu().numpy())
        return np.concatenate(scores), np.concatenate(maps)

    def score(self, images_hwc: np.ndarray, batch_size: int = 16) -> np.ndarray:
        """Score d'anomalie par image (distance au plus proche voisin, pondérée — plus haut = plus suspect)."""
        scores, _ = self._infer(images_hwc, batch_size)
        return scores

    def anomaly_map(self, images_hwc: np.ndarray, batch_size: int = 16) -> np.ndarray:
        """Carte d'anomalie par pixel ``(N, H, W)``, à la résolution des images d'entrée."""
        _, maps = self._infer(images_hwc, batch_size)
        return maps

    def calibrate_threshold(
        self, validation_good_images: np.ndarray, percentile: float = DEFAULT_THRESHOLD_PERCENTILE,
        batch_size: int = 16,
    ) -> float:
        """Calibre le seuil de décision au `percentile` des scores d'une validation **saine uniquement**.

        Par défaut au 99e centile : la politique retenue par le balayage de seuils de
        `03-choix-final-detection-maximale-wood.ipynb`, qui atteint un rappel de 100 % sur `wood` avec
        le moins de fausses alertes parmi les politiques testées.
        """
        validation_scores = self.score(validation_good_images, batch_size)
        self.threshold = choose_threshold_percentile(validation_scores, percentile=percentile)
        return self.threshold

    def predict(self, images_hwc: np.ndarray, batch_size: int = 16) -> np.ndarray:
        """Décision binaire (`True` = anomalie) au seuil calibré par `calibrate_threshold`."""
        if self.threshold is None:
            raise RuntimeError("Seuil non calibré : appeler .calibrate_threshold(...) d'abord.")
        return self.score(images_hwc, batch_size) >= self.threshold

    def save(self, path: Path) -> None:
        """Sauvegarde la mémoire de patchs (état complet du modèle), le seuil et la config."""
        model = self._require_fitted()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "config": self.config,
            "threshold": self.threshold,
            "state_dict": model.state_dict(),
        }, path)

    @classmethod
    def load(cls, path: Path, device: torch.device | None = None) -> "PatchCoreDetector":
        """Recharge un détecteur sauvegardé par `save` (mémoire de patchs déjà constituée)."""
        device = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
        checkpoint = torch.load(Path(path), map_location=device, weights_only=False)
        config: PatchCoreConfig = checkpoint["config"]
        detector = cls(config=config, device=device)
        model = PatchcoreModel(
            layers=list(config.layers), backbone=config.backbone, pre_trained=False,
            num_neighbors=config.num_neighbors,
        ).to(device)
        model.load_state_dict(checkpoint["state_dict"])
        model.eval()
        detector.model = model
        detector.threshold = checkpoint["threshold"]
        return detector
