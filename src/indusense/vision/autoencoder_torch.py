"""Auto-encodeur convolutif (PyTorch) pour la détection d'anomalies par reconstruction."""

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn


class ConvAutoencoder(nn.Module):
    """Encodeur/décodeur symétrique à 3 niveaux (stride 2), sortie dans ``[0, 1]``.

    ``kernel_size`` doit être impair : le padding (``kernel_size // 2``) et le
    ``output_padding`` (fixé à 1) sont calculés pour que chaque niveau divise
    ou multiplie exactement par 2 la résolution spatiale, quel que soit le
    noyau choisi (validé pour ``kernel_size`` ∈ {3, 5, 7, ...}).
    """

    def __init__(self, base_channels: int = 64, kernel_size: int = 3):
        super().__init__()
        c = base_channels
        k = kernel_size
        padding = k // 2
        self.encoder = nn.Sequential(
            nn.Conv2d(3, c, k, stride=2, padding=padding), nn.ReLU(inplace=True),
            nn.Conv2d(c, c * 2, k, stride=2, padding=padding), nn.ReLU(inplace=True),
            nn.Conv2d(c * 2, c * 4, k, stride=2, padding=padding), nn.ReLU(inplace=True),
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(c * 4, c * 2, k, stride=2, padding=padding, output_padding=1), nn.ReLU(inplace=True),
            nn.ConvTranspose2d(c * 2, c, k, stride=2, padding=padding, output_padding=1), nn.ReLU(inplace=True),
            nn.ConvTranspose2d(c, 3, k, stride=2, padding=padding, output_padding=1), nn.Sigmoid(),
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


def _gaussian_window(window_size: int, sigma: float, channels: int, device, dtype) -> torch.Tensor:
    coords = torch.arange(window_size, dtype=dtype, device=device) - window_size // 2
    gauss_1d = torch.exp(-(coords ** 2) / (2 * sigma ** 2))
    gauss_1d = (gauss_1d / gauss_1d.sum()).unsqueeze(0)
    gauss_2d = gauss_1d.t() @ gauss_1d
    return gauss_2d.expand(channels, 1, window_size, window_size).contiguous()


def ssim_loss(pred: torch.Tensor, target: torch.Tensor, window_size: int = 11, sigma: float = 1.5) -> torch.Tensor:
    """Perte ``1 - SSIM`` (similarité structurelle), différentiable, calculée par fenêtre glissante
    gaussienne. Contrairement à la MSE (écart pixel à pixel), le SSIM compare luminance, contraste et
    structure locale : une altération de texture (grain, motif) qui ne décale pas beaucoup les valeurs
    de pixel individuelles peut rester quasi invisible à la MSE mais faire chuter le SSIM.
    """
    channels = pred.shape[1]
    window = _gaussian_window(window_size, sigma, channels, pred.device, pred.dtype)
    padding = window_size // 2

    mu_pred = F.conv2d(pred, window, padding=padding, groups=channels)
    mu_target = F.conv2d(target, window, padding=padding, groups=channels)
    mu_pred_sq, mu_target_sq = mu_pred.pow(2), mu_target.pow(2)
    mu_pred_target = mu_pred * mu_target

    sigma_pred_sq = F.conv2d(pred * pred, window, padding=padding, groups=channels) - mu_pred_sq
    sigma_target_sq = F.conv2d(target * target, window, padding=padding, groups=channels) - mu_target_sq
    sigma_pred_target = F.conv2d(pred * target, window, padding=padding, groups=channels) - mu_pred_target

    c1, c2 = 0.01 ** 2, 0.03 ** 2
    ssim_map = ((2 * mu_pred_target + c1) * (2 * sigma_pred_target + c2)) / (
        (mu_pred_sq + mu_target_sq + c1) * (sigma_pred_sq + sigma_target_sq + c2)
    )
    return 1.0 - ssim_map.mean()


@torch.no_grad()
def evaluate_loss(images_hwc: np.ndarray, model: nn.Module, loss_fn, device, batch_size: int = 32) -> float:
    """Perte moyenne (même fonction que l'entraînement) sur un jeu d'images non augmenté, sans gradient.

    Utilisé pour suivre la perte de **validation** époque par époque, en plus de la perte de train.
    """
    model.eval()
    tensor = images_to_tensor(images_hwc)
    total_loss, total_count = 0.0, 0
    for start in range(0, tensor.shape[0], batch_size):
        batch = tensor[start:start + batch_size].to(device)
        reconstruction = model(batch)
        loss = loss_fn(reconstruction, batch)
        total_loss += loss.item() * batch.shape[0]
        total_count += batch.shape[0]
    return total_loss / total_count
