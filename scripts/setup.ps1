# Create the venvs + install per-lane requirements + the editable package. Idempotent. No global installs.
# .ps1 parity of setup.sh (Felipe runs PowerShell on Windows).
# -Train also provisions the GPU training lane (.venv-train, torch cu124) for the learned tier.
param([switch]$Train)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$py = if ($env:PYTHON) { $env:PYTHON } else { "python" }

function Get-VenvPy($dir) {
  $p = Join-Path $dir "Scripts\python.exe"
  if (-not (Test-Path $p)) { $p = Join-Path $dir "bin/python" }
  return $p
}

Write-Host "[setup] .venv-pipeline (offline lane)..."
if (-not (Test-Path ".venv-pipeline")) { & $py -m venv .venv-pipeline }
$vp = Get-VenvPy ".venv-pipeline"
& $vp -m pip install --upgrade pip -q
& $vp -m pip install -q -r data-pipeline/requirements.txt -r requirements-dev.txt
& $vp -m pip install -q -e .
# pygeotypes (private CAOS_GeoTypes until the PyPI release): sibling checkout, editable
$geo = Join-Path (Split-Path (Get-Location).Path -Parent) "CAOS_GeoTypes"
if (Test-Path $geo) { & $vp -m pip install -q -e "$geo[fast,attr]" }
else { Write-Warning "CAOS_GeoTypes not found next to this repo - clone it and re-run setup (pygeotypes is required)" }
Write-Host "[setup] .venv-pipeline ready."

Write-Host "[setup] .venv (runtime/live-thin lane)..."
if (-not (Test-Path ".venv")) { & $py -m venv .venv }
$vr = Get-VenvPy ".venv"
& $vr -m pip install --upgrade pip -q
& $vr -m pip install -q -r requirements.txt
if (Test-Path $geo) { & $vr -m pip install -q -e $geo }
Write-Host "[setup] .venv ready."

# The GPU training lane (.venv-train): torch cu124 for the learned tier (P2). ISOLATED from
# .venv-pipeline (which stays CPU for the deterministic offline bake + open-DARTS). Opt-in via
# -Train (or PULSO_TRAIN=1): only create it on a CUDA machine; skipped by default so a CPU-only
# checkout still sets up.
if ($Train -or $env:PULSO_TRAIN) {
  Write-Host "[setup] .venv-train (GPU training lane, torch cu124)..."
  if (-not (Test-Path ".venv-train")) { & $py -m venv .venv-train }
  $vt = Get-VenvPy ".venv-train"
  & $vt -m pip install --upgrade pip -q
  & $vt -m pip install -q torch --index-url https://download.pytorch.org/whl/cu124
  & $vt -m pip install -q -r data-pipeline/requirements-train.txt
  if (Test-Path $geo) { & $vt -m pip install -q -e "$geo[fast,attr]" }
  & $vt -m pip install -q -e .
  Write-Host "[setup] .venv-train ready. Verify: & .venv-train/Scripts/python.exe scripts/gpu_smoke.py"
}

Write-Host "[setup] done. Next:  ./scripts/precompute.ps1   then   ./scripts/dev.ps1"
