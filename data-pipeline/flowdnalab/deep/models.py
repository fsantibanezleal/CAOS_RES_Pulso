"""torch architectures for the learned tier. Small, CPU-trainable, ONNX-exportable (fixed input
length N = the preprocessed curve length). Input is a single-channel curve (batch, 1, N)."""
from __future__ import annotations

import torch
import torch.nn as nn


class GeoTypeCNN(nn.Module):
    """1D-CNN GeoType classifier: curve (b,1,N) -> class logits (b,K).

    Three Conv1d blocks (dilated, to see multi-scale regime structure) + global average pool + head.
    Small enough to train on a few hundred curves on CPU in seconds and to run live in the browser.
    """

    def __init__(self, n_classes: int, n_points: int, width: int = 24):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv1d(1, width, 7, padding=3), nn.BatchNorm1d(width), nn.ReLU(),
            nn.Conv1d(width, width * 2, 5, padding=4, dilation=2), nn.BatchNorm1d(width * 2), nn.ReLU(),
            nn.Conv1d(width * 2, width * 2, 3, padding=4, dilation=4), nn.BatchNorm1d(width * 2), nn.ReLU(),
        )
        self.head = nn.Sequential(nn.Linear(width * 2, width * 2), nn.ReLU(), nn.Dropout(0.1),
                                  nn.Linear(width * 2, n_classes))
        self.n_points = n_points

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.features(x)
        h = h.mean(dim=2)                    # global average pool over time
        return self.head(h)                  # logits; softmax applied at export


class GeoTypeCNNProba(nn.Module):
    """Export wrapper: emits softmax probabilities (what onnxruntime-web reads directly)."""

    def __init__(self, base: GeoTypeCNN):
        super().__init__()
        self.base = base

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.base(x), dim=1)


class CurveAutoencoder(nn.Module):
    """Convolutional autoencoder: curve (b,1,N) -> latent (b,L) -> reconstruction (b,1,N).

    The reconstruction error is an out-of-distribution / anomaly score (a curve unlike the training
    catalogue reconstructs poorly). The latent is a 2-D-projectable embedding of behaviour.
    """

    def __init__(self, n_points: int, latent: int = 8, width: int = 24):
        super().__init__()
        self.n_points = n_points
        self.latent = latent
        self.enc = nn.Sequential(
            nn.Conv1d(1, width, 5, stride=2, padding=2), nn.ReLU(),
            nn.Conv1d(width, width * 2, 5, stride=2, padding=2), nn.ReLU(),
        )
        self.enc_len = n_points // 4
        self.to_latent = nn.Linear(width * 2 * self.enc_len, latent)
        self.from_latent = nn.Linear(latent, width * 2 * self.enc_len)
        self.dec = nn.Sequential(
            nn.ConvTranspose1d(width * 2, width, 4, stride=2, padding=1), nn.ReLU(),
            nn.ConvTranspose1d(width, 1, 4, stride=2, padding=1),
        )
        self._width = width

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        h = self.enc(x).flatten(1)
        return self.to_latent(h)

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        h = self.from_latent(z).view(z.shape[0], self._width * 2, self.enc_len)
        return self.dec(h)

    def forward(self, x: torch.Tensor):
        z = self.encode(x)
        return self.decode(z), z


class AEExport(nn.Module):
    """Export wrapper: curve (b,1,N) -> (latent (b,L), recon_error (b,1)). What the browser needs
    for the latent-space point + the anomaly score, in one call."""

    def __init__(self, ae: CurveAutoencoder):
        super().__init__()
        self.ae = ae

    def forward(self, x: torch.Tensor):
        recon, z = self.ae(x)
        err = ((recon - x) ** 2).mean(dim=(1, 2), keepdim=False).unsqueeze(1)
        return z, err


class ContrastiveEncoder(nn.Module):
    """Embedding encoder trained with a triplet loss (same GeoType closer than different): curve
    (b,1,N) -> L2-normalized embedding (b,E). Enables nearest-neighbour retrieval in the browser."""

    def __init__(self, n_points: int, emb: int = 16, width: int = 24):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(1, width, 7, padding=3), nn.ReLU(),
            nn.Conv1d(width, width * 2, 5, stride=2, padding=2), nn.ReLU(),
            nn.Conv1d(width * 2, width * 2, 3, stride=2, padding=1), nn.ReLU(),
        )
        self.proj = nn.Linear(width * 2 * (n_points // 4), emb)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.net(x).flatten(1)
        e = self.proj(h)
        return torch.nn.functional.normalize(e, dim=1)
