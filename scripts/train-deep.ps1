# Offline hard-processing: train the learned tier (1D-CNN + AE + contrastive) -> ONNX. Needs torch.
$ErrorActionPreference = "Stop"; Set-Location (Join-Path $PSScriptRoot "..")
$env:PYTHONUTF8 = "1"
.\.venv-pipeline\Scripts\python.exe -c "from fracpta.deep.train import train_all; print(train_all('models/deep'))"
