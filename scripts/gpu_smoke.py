"""GPU training-lane smoke test: run in .venv-train to confirm CUDA torch works end to end.

    data-pipeline/.venv-train/Scripts/python.exe scripts/gpu_smoke.py

Asserts CUDA is available, prints the device, and runs a tiny 1D-conv forward + backward on the GPU
(the shape of the learned tier's InceptionTime/AE inputs: batch x 1 x length). Exits non-zero if the
GPU is not usable, so CI / setup can fail loudly instead of silently training on the CPU.
"""
from __future__ import annotations

import sys


def main() -> int:
    try:
        import torch
    except ImportError:
        print("FAIL: torch not installed in this environment", file=sys.stderr)
        return 2

    print(f"torch {torch.__version__}")
    if not torch.cuda.is_available():
        print("FAIL: CUDA not available (this venv must have the cu124 wheel, not +cpu)", file=sys.stderr)
        return 1
    dev = torch.device("cuda")
    print(f"device: {torch.cuda.get_device_name(0)} | capability {torch.cuda.get_device_capability(0)}")

    # a tiny 1D conv block on the GPU: forward + backward + an optimizer step
    torch.manual_seed(0)
    x = torch.randn(8, 1, 96, device=dev)              # batch x channels x length (a curve)
    conv = torch.nn.Conv1d(1, 16, kernel_size=5, padding=2).to(dev)
    head = torch.nn.Linear(16, 3).to(dev)
    opt = torch.optim.Adam(list(conv.parameters()) + list(head.parameters()), lr=1e-3)
    y = torch.randint(0, 3, (8,), device=dev)

    opt.zero_grad()
    h = conv(x).mean(dim=2)                             # global average pool over length
    logits = head(h)
    loss = torch.nn.functional.cross_entropy(logits, y)
    loss.backward()
    opt.step()

    assert logits.shape == (8, 3)
    assert loss.item() > 0
    print(f"conv1d forward+backward OK on GPU | loss={loss.item():.4f}")
    print("PASS: GPU training lane is usable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
