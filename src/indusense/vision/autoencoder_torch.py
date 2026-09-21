"""Auto-encodeur convolutif (PyTorch) pour la détection d'anomalies par reconstruction."""

import numpy as np
import torch
from torch import nn


class ConvAutoencoder(nn.Module):
    """Encodeur/décodeur symétrique à 3 niveaux (stride 2), sortie dans ``[0, 1]``."""

    def __init__(self, base_channels: int = 64):
        super().__init__()
        c = base_channels
        self.encoder = nn.Sequential(
            nn.Conv2d(3, c, 3, stride=2, padding=1), nn.ReLU(inplace=True),
            nn.Conv2d(c, c * 2, 3, stride=2, padding=1), nn.ReLU(inplace=True),
            nn.Conv2d(c * 2, c * 4, 3, stride=2, padding=1), nn.ReLU(inplace=True),
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(c * 4, c * 2, 3, stride=2, padding=1, output_padding=1), nn.ReLU(inplace=True),
            nn.ConvTranspose2d(c * 2, c, 3, stride=2, padding=1, output_padding=1), nn.ReLU(inplace=True),
            nn.ConvTranspose2d(c, 3, 3, stride=2, padding=1, output_padding=1), nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))


def count_trainable_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def images_to_tensor(images_hwc: np.ndarray) -> torch.Tensor:
    """Convertit un tableau ``(N, H, W, 3)`` en tenseur PyTorch ``(N, 3, H, W)``."""
    return torch.from_numpy(images_hwc.transpose(0, 3, 1, 2).copy()).float()


def tensor_to_images(tensor_nchw: torch.Tensor) -> np.ndarray:
    """Convertit un tenseur PyTorch ``(N, 3, H, W)`` en tableau NumPy ``(N, H, W, 3)``."""
    return tensor_nchw.detach().cpu().numpy().transpose(0, 2, 3, 1)
