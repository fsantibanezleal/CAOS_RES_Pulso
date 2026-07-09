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
        DeepAutoencoder,
        InceptionTime,
        PatchTSTLite,
        ProbaExport,
        TS2VecEncoder,
    )

    torch.manual_seed(seed)
    np.random.seed(seed)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    data = build_training_set(seed=seed)
    X = data["X"]                     # (n, N)
    y = data["labels"]
    n, N = X.shape
    K = data["k"]
    Xt = torch.from_numpy(X).unsqueeze(1).to(dev)  # (n,1,N)
    yt = torch.from_numpy(y).to(dev)
    tr, te = _split(n, seed)
    tr_t, te_t = torch.from_numpy(tr).to(dev), torch.from_numpy(te).to(dev)

    metrics: dict = {"n_train": int(tr.size), "n_test": int(te.size), "k": K, "n_points": N,
                     "silhouette_train": data["silhouette"], "device": dev.type}

    def train_classifier(model, tag, key, lr=1e-3, wd=1e-4, ep=None):
        model = model.to(dev)
        opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=ep or epochs)
        for _ in range(ep or epochs):
            model.train()
            opt.zero_grad()
            loss = F.cross_entropy(model(Xt[tr_t]), yt[tr_t])
            loss.backward()
            opt.step()
            sched.step()
        model.eval()
        with torch.no_grad():
            acc = (model(Xt[te_t]).argmax(1) == yt[te_t]).float().mean().item()
        metrics[key] = round(acc, 4)
        ProbaExport(model).eval().to("cpu")
        _export(ProbaExport(model).eval().to("cpu"), Xt[:1].to("cpu"), out / tag, ["curve"], ["proba"])
        return model

    # ---------- InceptionTime classifier (SOTA CNN) ----------
    train_classifier(InceptionTime(n_classes=K, n_points=N), "geotype_incep.onnx",
                     "incep_test_accuracy", lr=1e-3, wd=1e-4)

    # ---------- PatchTST-lite classifier (SOTA transformer) ----------
    train_classifier(PatchTSTLite(n_classes=K, n_points=N), "geotype_patchtst.onnx",
                     "patchtst_test_accuracy", lr=8e-4, wd=1e-4)

    # ---------- deeper conv autoencoder (anomaly / OOD) ----------
    ae = DeepAutoencoder(n_points=N).to(dev)
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
    ae_cpu = ae.to("cpu").eval()
    _export(AEExport(ae_cpu).eval(), Xt[:1].to("cpu"), out / "curve_ae.onnx", ["curve"], ["latent", "recon_error"])

    # ---------- TS2Vec-style contrastive embedding (NT-Xent over two masked views) ----------
    enc = TS2VecEncoder(n_points=N).to(dev)
    opt = torch.optim.Adam(enc.parameters(), lr=1e-3, weight_decay=1e-5)
    gen = torch.Generator(device=dev).manual_seed(seed)
    Xtr = Xt[tr_t]
    for _ in range(epochs * 4):
        enc.train()
        v1 = _mask_view(Xtr, 0.15, gen)
        v2 = _mask_view(Xtr, 0.15, gen)
        z1, z2 = enc(v1), enc(v2)
        loss = _nt_xent(z1, z2, temp=0.2)
        opt.zero_grad()
        loss.backward()
        opt.step()
    enc = enc.to("cpu").eval()
    Xt_cpu = Xt.to("cpu")
    metrics["embed_retrieval_at1"] = round(_retrieval_at1(enc, Xt_cpu, y, tr, te), 4)
    _export(enc, Xt_cpu[:1], out / "curve_embed.onnx", ["curve"], ["embedding"])

    # committed reference artifacts the browser needs alongside the ONNX: the training-set embedding
    # cloud (for the latent/retrieval viz) + the medoids + preprocessing spec
    with torch.no_grad():
        emb = enc(Xt_cpu).numpy()
        latents = ae_cpu.encode(Xt_cpu).numpy()
    # class-conditional split-conformal calibration: DTW distance of each training curve to its
    # class medoid (the browser's live conformal assignment reads these).
    from pygeotypes.distance import distances_to_references

    dtw_window = 10
    medoids = data["medoids"]
    cal: dict[str, list[float]] = {}
    for g in range(K):
        rows = X[y == g]
        d = np.array([distances_to_references(r, medoids[g], window=dtw_window)[0] for r in rows])
        cal[str(g)] = np.round(np.sort(d), 5).tolist()

    # committed HELD-OUT test set (curves + true labels) so the Benchmark page can run BOTH the learned
    # ONNX and the classical DTW-nearest-medoid on the SAME held-out curves live and build a real
    # confusion matrix. Capped to keep reference.json compact. NOTE: this training set is synthetic
    # Warren-Root/homogeneous archetypes; a real-4TU-trained learned benchmark is a documented roadmap.
    n_bench = int(min(120, te.size))
    bi = te[:n_bench]
    benchmark = {
        "domain": "synthetic-archetypes",
        "curves": np.round(X[bi], 4).tolist(),
        "labels": y[bi].tolist(),
    }

    ref = {
        "k": K, "n_points": N, "labels": y.tolist(),
        "dtw_window": dtw_window,
        "embedding": np.round(emb, 4).tolist(),
        "latent": np.round(latents, 4).tolist(),
        "medoids": np.round(medoids, 5).tolist(),
        "calibration_scores": cal,
        "benchmark": benchmark,
        "preprocessing": {"derivative_order": 1, "norm": "zscore", "n_points": N},
        "metrics": metrics,
    }
    (out / "reference.json").write_text(json.dumps(ref, separators=(",", ":")), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(
        {"models": ["geotype_incep", "geotype_patchtst", "curve_ae", "curve_embed"],
         "opset": 18, "metrics": metrics}, indent=2), encoding="utf-8")
    # remove the superseded 1D-CNN artifact if a previous run left it
    for stale in ("geotype_cnn.onnx", "geotype_cnn.onnx.data"):
        (out / stale).unlink(missing_ok=True)
    return metrics


def _mask_view(x, frac, gen):
    """A TS2Vec augmentation: zero out a random contiguous span (per sample) of the input curve."""
    import torch

    b, _, n = x.shape
    out = x.clone()
    span = max(1, int(frac * n))
    starts = torch.randint(0, n - span + 1, (b,), generator=gen, device=x.device)
    for i in range(b):
        out[i, :, starts[i]:starts[i] + span] = 0.0
    return out


def _nt_xent(z1, z2, temp: float = 0.2):
    """NT-Xent contrastive loss over two views: each sample's two views are positives, all other
    samples (both views) are negatives (SimCLR/TS2Vec instance contrast)."""
    import torch
    import torch.nn.functional as F

    b = z1.shape[0]
    z = torch.cat([z1, z2], dim=0)               # (2b, E), already L2-normalized
    sim = (z @ z.t()) / temp                       # cosine similarity matrix
    sim.fill_diagonal_(-1e9)                        # exclude self
    targets = torch.arange(b, device=z.device)
    targets = torch.cat([targets + b, targets], dim=0)  # positive index for each row
    return F.cross_entropy(sim, targets)


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
    import onnx
    import onnxruntime as ort
    import torch

    torch.onnx.export(model, sample, str(path), input_names=inputs, output_names=outputs,
                      opset_version=18, dynamic_axes={inputs[0]: {0: "batch"}})
    # Re-save as a SINGLE self-contained file (embed weights). onnxruntime-web cannot resolve the
    # `.onnx.data` external-data sidecar from a URL, so the browser needs the weights inside the .onnx.
    m = onnx.load(str(path))
    for f in path.parent.glob(path.name + ".data"):
        f.unlink()
    onnx.save(m, str(path), save_as_external_data=False)
    # parity: torch vs onnxruntime on the sample
    with torch.no_grad():
        ref = model(sample)
    ref = [ref] if isinstance(ref, torch.Tensor) else list(ref)
    sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    got = sess.run(None, {inputs[0]: sample.numpy()})
    for r, g in zip(ref, got):
        err = float(np.max(np.abs(r.numpy() - g)))
        assert err < 1e-4, f"ONNX parity failure for {path.name}: {err}"
