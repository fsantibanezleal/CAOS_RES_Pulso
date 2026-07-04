"""Train the learned tier + export ONNX + verify parity + write the metrics manifest.

Offline hard-processing lane. Run in `.venv-pipeline` (torch): trains the 1D-CNN classifier, the
conv autoencoder, and the contrastive encoder on the labeled GeoType curves, exports each to ONNX
(opset 18), checks ONNX-vs-torch parity (<1e-4), and writes small committed `.onnx` + a manifest
(`models/deep/manifest.json`) with honest held-out metrics. The browser runs the ONNX via
onnxruntime-web (live inference); this module never runs in the browser.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def _split(n: int, seed: int, frac_test: float = 0.25):
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n)
    n_test = max(1, int(frac_test * n))
    return perm[n_test:], perm[:n_test]


def train_all(out_dir: str | Path, seed: int = 0, epochs: int = 60) -> dict:
    import torch
    import torch.nn.functional as F

    from .datasets import build_training_set
    from .models import (
        AEExport,
        ContrastiveEncoder,
        CurveAutoencoder,
        GeoTypeCNN,
        GeoTypeCNNProba,
    )

    torch.manual_seed(seed)
    np.random.seed(seed)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    data = build_training_set(seed=seed)
    X = data["X"]                     # (n, N)
    y = data["labels"]
    n, N = X.shape
    K = data["k"]
    Xt = torch.from_numpy(X).unsqueeze(1)          # (n,1,N)
    yt = torch.from_numpy(y)
    tr, te = _split(n, seed)
    tr_t, te_t = torch.from_numpy(tr), torch.from_numpy(te)

    metrics: dict = {"n_train": int(tr.size), "n_test": int(te.size), "k": K, "n_points": N,
                     "silhouette_train": data["silhouette"]}

    # ---------- 1D-CNN classifier ----------
    cnn = GeoTypeCNN(n_classes=K, n_points=N)
    opt = torch.optim.Adam(cnn.parameters(), lr=2e-3, weight_decay=1e-4)
    for _ in range(epochs):
        cnn.train()
        opt.zero_grad()
        loss = F.cross_entropy(cnn(Xt[tr_t]), yt[tr_t])
        loss.backward()
        opt.step()
    cnn.eval()
    with torch.no_grad():
        acc = (cnn(Xt[te_t]).argmax(1) == yt[te_t]).float().mean().item()
    metrics["cnn_test_accuracy"] = round(acc, 4)
    cnn_proba = GeoTypeCNNProba(cnn).eval()
    _export(cnn_proba, Xt[:1], out / "geotype_cnn.onnx", ["curve"], ["proba"])

    # ---------- conv autoencoder ----------
    ae = CurveAutoencoder(n_points=N)
    opt = torch.optim.Adam(ae.parameters(), lr=2e-3, weight_decay=1e-5)
    for _ in range(epochs):
        ae.train()
        opt.zero_grad()
        recon, _ = ae(Xt[tr_t])
        loss = F.mse_loss(recon, Xt[tr_t])
        loss.backward()
        opt.step()
    ae.eval()
    with torch.no_grad():
        rec_te, _ = ae(Xt[te_t])
        rec_err = F.mse_loss(rec_te, Xt[te_t]).item()
    metrics["ae_test_recon_mse"] = round(rec_err, 5)
    ae_export = AEExport(ae).eval()
    _export(ae_export, Xt[:1], out / "curve_ae.onnx", ["curve"], ["latent", "recon_error"])

    # ---------- contrastive embedding (triplet) ----------
    enc = ContrastiveEncoder(n_points=N)
    opt = torch.optim.Adam(enc.parameters(), lr=2e-3, weight_decay=1e-5)
    rng = np.random.default_rng(seed)
    for _ in range(epochs * 3):
        enc.train()
        a, p, ng = _triplets(y[tr], rng, 64)
        A, P, Ng = tr[a], tr[p], tr[ng]
        ea, ep, en = enc(Xt[A]), enc(Xt[P]), enc(Xt[Ng])
        loss = F.triplet_margin_loss(ea, ep, en, margin=0.4)
        opt.zero_grad()
        loss.backward()
        opt.step()
    enc.eval()
    metrics["embed_retrieval_at1"] = round(_retrieval_at1(enc, Xt, y, tr, te), 4)
    _export(enc, Xt[:1], out / "curve_embed.onnx", ["curve"], ["embedding"])

    # committed reference artifacts the browser needs alongside the ONNX: the training-set embedding
    # cloud (for the latent/retrieval viz) + the medoids + preprocessing spec
    with torch.no_grad():
        emb = enc(Xt).numpy()
        lat, _ = ae(Xt)
        latents = ae.encode(Xt).numpy()
    ref = {
        "k": K, "n_points": N, "labels": y.tolist(),
        "embedding": np.round(emb, 4).tolist(),
        "latent": np.round(latents, 4).tolist(),
        "medoids": np.round(data["medoids"], 5).tolist(),
        "preprocessing": {"derivative_order": 1, "norm": "zscore", "n_points": N},
        "metrics": metrics,
    }
    (out / "reference.json").write_text(json.dumps(ref, separators=(",", ":")), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps({"models": ["geotype_cnn", "curve_ae", "curve_embed"],
                                                   "opset": 18, "metrics": metrics}, indent=2), encoding="utf-8")
    return metrics


def _triplets(labels: np.ndarray, rng, m: int):
    a, p, n = [], [], []
    idx_by = {c: np.where(labels == c)[0] for c in np.unique(labels)}
    classes = list(idx_by)
    for _ in range(m):
        c = rng.choice(classes)
        if idx_by[c].size < 2:
            continue
        ai, pi = rng.choice(idx_by[c], 2, replace=False)
        oc = rng.choice([x for x in classes if x != c])
        ni = rng.choice(idx_by[oc])
        a.append(ai)
        p.append(pi)
        n.append(ni)
    return np.array(a), np.array(p), np.array(n)


def _retrieval_at1(enc, Xt, y, tr, te) -> float:
    import torch

    with torch.no_grad():
        e_tr = enc(Xt[torch.from_numpy(tr)]).numpy()
        e_te = enc(Xt[torch.from_numpy(te)]).numpy()
    hits = 0
    for i, q in enumerate(e_te):
        d = np.linalg.norm(e_tr - q, axis=1)
        if y[tr][int(d.argmin())] == y[te][i]:
            hits += 1
    return hits / len(te)


def _export(model, sample, path: Path, inputs: list[str], outputs: list[str]) -> None:
    import numpy as np
    import onnxruntime as ort
    import torch

    torch.onnx.export(model, sample, str(path), input_names=inputs, output_names=outputs,
                      opset_version=18, dynamic_axes={inputs[0]: {0: "batch"}})
    # parity: torch vs onnxruntime on the sample
    with torch.no_grad():
        ref = model(sample)
    ref = [ref] if isinstance(ref, torch.Tensor) else list(ref)
    sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    got = sess.run(None, {inputs[0]: sample.numpy()})
    for r, g in zip(ref, got):
        err = float(np.max(np.abs(r.numpy() - g)))
        assert err < 1e-4, f"ONNX parity failure for {path.name}: {err}"
