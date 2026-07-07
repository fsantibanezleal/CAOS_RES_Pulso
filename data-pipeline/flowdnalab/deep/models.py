"""torch architectures for the learned tier. GPU-trainable (.venv-train, cu124), ONNX-exportable
(fixed input length N = the preprocessed curve length). Input is a single-channel curve (batch, 1, N).

P2d upgrades the tier to SOTA architectures, each with a verified primary source:
- InceptionTime  - Ismail Fawaz et al. 2020 (DAMI): multi-scale Inception modules + residuals (classifier).
- PatchTST-lite  - Nie et al. 2023 (ICLR): patchified series + a Transformer encoder (classifier).
- TS2Vec-style   - Yue et al. 2022 (AAAI): a dilated-conv encoder trained contrastively (retrieval).
- deeper conv-AE - the anomaly / OOD reconstruction model (upgraded depth).
All emit fixed-shape tensors and use only ONNX-friendly ops (conv/linear/softmax/attention).
"""
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


# ===================================================================================================
# P2d SOTA architectures
# ===================================================================================================

class _InceptionModule(nn.Module):
    """One InceptionTime module: a bottleneck 1x1 conv, three parallel convs of increasing kernel
    size (multi-scale), plus a max-pool branch; concatenated -> BN -> ReLU (Ismail Fawaz et al. 2020)."""

    def __init__(self, in_ch: int, nf: int = 32, kernels=(9, 19, 39), bottleneck: int = 32):
        super().__init__()
        self.bottleneck = nn.Conv1d(in_ch, bottleneck, 1, padding=0, bias=False) if in_ch > 1 else None
        cin = bottleneck if self.bottleneck is not None else in_ch
        self.convs = nn.ModuleList([nn.Conv1d(cin, nf, k, padding=k // 2, bias=False) for k in kernels])
        self.pool = nn.Sequential(nn.MaxPool1d(3, stride=1, padding=1),
                                  nn.Conv1d(in_ch, nf, 1, padding=0, bias=False))
        self.bn = nn.BatchNorm1d(nf * (len(kernels) + 1))
        self.act = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.bottleneck(x) if self.bottleneck is not None else x
        branches = [c(z) for c in self.convs] + [self.pool(x)]
        return self.act(self.bn(torch.cat(branches, dim=1)))


class InceptionTime(nn.Module):
    """InceptionTime classifier (Ismail Fawaz et al. 2020): a stack of Inception modules with a residual
    shortcut every 3, global average pool, linear head. Emits logits (softmax at export)."""

    def __init__(self, n_classes: int, n_points: int, depth: int = 6, nf: int = 32):
        super().__init__()
        self.n_points = n_points
        self.modules_ = nn.ModuleList()
        self.shortcuts = nn.ModuleList()
        out_ch = nf * 4
        in_ch = 1
        res_in = 1
        for d in range(depth):
            self.modules_.append(_InceptionModule(in_ch, nf=nf))
            in_ch = out_ch
            if d % 3 == 2:
                self.shortcuts.append(nn.Sequential(nn.Conv1d(res_in, out_ch, 1, bias=False),
                                                    nn.BatchNorm1d(out_ch)))
                res_in = out_ch
        self.act = nn.ReLU()
        self.head = nn.Linear(out_ch, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = x
        si = 0
        for d, m in enumerate(self.modules_):
            x = m(x)
            if d % 3 == 2:
                x = self.act(x + self.shortcuts[si](res))
                res = x
                si += 1
        return self.head(x.mean(dim=2))          # global average pool -> logits


class DeepAutoencoder(nn.Module):
    """Deeper convolutional autoencoder (P2d upgrade): three stride-2 encoder blocks -> latent ->
    three decoder blocks. Reconstruction error is the OOD/anomaly score; latent is a behaviour embedding."""

    def __init__(self, n_points: int, latent: int = 8, width: int = 32):
        super().__init__()
        self.n_points = n_points
        self.latent = latent
        self.enc = nn.Sequential(
            nn.Conv1d(1, width, 5, stride=2, padding=2), nn.BatchNorm1d(width), nn.ReLU(),
            nn.Conv1d(width, width * 2, 5, stride=2, padding=2), nn.BatchNorm1d(width * 2), nn.ReLU(),
            nn.Conv1d(width * 2, width * 2, 3, stride=2, padding=1), nn.BatchNorm1d(width * 2), nn.ReLU(),
        )
        self.enc_len = n_points // 8
        self._width = width
        self.to_latent = nn.Linear(width * 2 * self.enc_len, latent)
        self.from_latent = nn.Linear(latent, width * 2 * self.enc_len)
        self.dec = nn.Sequential(
            nn.ConvTranspose1d(width * 2, width * 2, 4, stride=2, padding=1), nn.ReLU(),
            nn.ConvTranspose1d(width * 2, width, 4, stride=2, padding=1), nn.ReLU(),
            nn.ConvTranspose1d(width, 1, 4, stride=2, padding=1),
        )

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return self.to_latent(self.enc(x).flatten(1))

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        h = self.from_latent(z).view(z.shape[0], self._width * 2, self.enc_len)
        return self.dec(h)

    def forward(self, x: torch.Tensor):
        z = self.encode(x)
        return self.decode(z), z


class TS2VecEncoder(nn.Module):
    """TS2Vec-style encoder (Yue et al. 2022): an input projection + a stack of dilated-conv residual
    blocks (exponentially growing receptive field), max-pooled over time to an instance embedding. We
    train it contrastively (two masked views, NT-Xent). At inference it is a deterministic conv encoder
    -> L2-normalized embedding (b, E), ONNX-friendly."""

    def __init__(self, n_points: int, emb: int = 16, width: int = 32, depth: int = 4):
        super().__init__()
        self.input_proj = nn.Conv1d(1, width, 1)
        blocks = []
        for d in range(depth):
            dil = 2 ** d
            blocks.append(nn.Conv1d(width, width, 3, padding=dil, dilation=dil))
        self.blocks = nn.ModuleList(blocks)
        self.act = nn.GELU()
        self.proj = nn.Linear(width, emb)

    def features(self, x: torch.Tensor) -> torch.Tensor:
        h = self.input_proj(x)
        for b in self.blocks:
            h = h + self.act(b(h))               # residual dilated-conv block
        return h                                  # (b, width, N)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.features(x).max(dim=2).values    # max-pool over time -> (b, width)
        return torch.nn.functional.normalize(self.proj(h), dim=1)


class PatchTSTLite(nn.Module):
    """PatchTST-lite classifier (Nie et al. 2023): split the series into patches, linearly embed each
    patch + a learned positional embedding, run a small Transformer encoder, flatten -> linear head.
    Uses nn.MultiheadAttention (ONNX-exportable). Emits logits (softmax at export)."""

    def __init__(self, n_classes: int, n_points: int, patch: int = 16, stride: int = 8,
                 d_model: int = 64, heads: int = 4, layers: int = 2):
        super().__init__()
        self.patch = patch
        self.stride = stride
        self.n_patches = 1 + (n_points - patch) // stride
        self.embed = nn.Linear(patch, d_model)
        self.pos = nn.Parameter(torch.zeros(1, self.n_patches, d_model))
        enc_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=heads, dim_feedforward=d_model * 2,
                                               dropout=0.1, batch_first=True, activation="gelu")
        self.encoder = nn.TransformerEncoder(enc_layer, num_layers=layers)
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model * self.n_patches, n_classes)
        nn.init.trunc_normal_(self.pos, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (b, 1, N) -> unfold into patches (b, n_patches, patch)
        p = x.squeeze(1).unfold(dimension=1, size=self.patch, step=self.stride)
        h = self.embed(p) + self.pos             # (b, n_patches, d_model)
        h = self.norm(self.encoder(h))
        return self.head(h.flatten(1))           # logits


class ProbaExport(nn.Module):
    """Export wrapper for a logits classifier: emits softmax probabilities (browser reads directly)."""

    def __init__(self, base: nn.Module):
        super().__init__()
        self.base = base

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.base(x), dim=1)
