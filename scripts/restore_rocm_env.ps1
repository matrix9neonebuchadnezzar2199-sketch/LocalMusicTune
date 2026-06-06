#Requires -Version 5.1
<#
.SYNOPSIS
  Restore ROCm PyTorch + ACE-Step in LocalMusicTune venv after uv sync rollback.

.NOTES
  Run from EXTERNAL PowerShell (not inside a Python/Gradio session).
  Close Cursor terminals / `uv run localmusictune` / Jupyter using this venv first,
  or c10.dll install fails with "Access denied".

  Usage:
    cd H:\CURSOR\LocalMusicTune
    .\scripts\restore_rocm_env.ps1
    .\scripts\restore_rocm_env.ps1 -AceStepPath H:\CURSOR\ACE-Step-1.5
#>
param(
    [string]$AceStepPath = "H:\CURSOR\ACE-Step-1.5",
    [string]$RocrmRel = "rocm-rel-7.2",
    [string]$TorchTag = "rocmsdk20260116"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$Base = "https://repo.radeon.com/rocm/windows/$RocrmRel"
$Wheels = @(
    "$Base/rocm-7.2.0.dev0.tar.gz",
    "$Base/rocm_sdk_core-7.2.0.dev0-py3-none-win_amd64.whl",
    "$Base/rocm_sdk_devel-7.2.0.dev0-py3-none-win_amd64.whl",
    "$Base/rocm_sdk_libraries_custom-7.2.0.dev0-py3-none-win_amd64.whl",
    "$Base/torch-2.9.1+${TorchTag}-cp312-cp312-win_amd64.whl",
    "$Base/torchaudio-2.9.1+${TorchTag}-cp312-cp312-win_amd64.whl",
    "$Base/torchvision-0.24.1+${TorchTag}-cp312-cp312-win_amd64.whl"
)

Write-Host "=== LocalMusicTune ROCm env restore ===" -ForegroundColor Cyan
Write-Host "venv: $(Resolve-Path .venv)"

Write-Host "`n[1/4] Removing broken PyPI torch (if present)..." -ForegroundColor Yellow
uv pip uninstall torch torchaudio torchvision 2>$null | Out-Null
foreach ($dir in @("torch", "torchaudio", "torchvision")) {
    $p = ".venv\Lib\site-packages\$dir"
    if (Test-Path $p) {
        Remove-Item -Recurse -Force $p -ErrorAction SilentlyContinue
    }
}
Get-ChildItem ".venv\Lib\site-packages\torch-*.dist-info" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n[2/4] Installing ROCm SDK + PyTorch wheels..." -ForegroundColor Yellow
uv pip install --no-cache-dir --link-mode=copy @Wheels

Write-Host "`n[3/4] Verifying torch..." -ForegroundColor Yellow
$env:PYTHONIOENCODING = "utf-8"
uv run --no-sync python -c "import torch; print('torch:', torch.__version__); print('cuda:', torch.cuda.is_available())"
if ($LASTEXITCODE -ne 0) { throw "torch verification failed" }

if (Test-Path $AceStepPath) {
    Write-Host "`n[4/4] Installing ACE-Step editable (--no-deps)..." -ForegroundColor Yellow
    uv pip install -e $AceStepPath --no-deps
    uv run --no-sync python -c "import torch; print('torch:', torch.__version__); import acestep; print('acestep OK')"
} else {
    Write-Host "`n[4/4] SKIP acestep — path not found: $AceStepPath" -ForegroundColor DarkYellow
    Write-Host "  uv pip install -e <ACE-Step-1.5> --no-deps"
}

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "Use: uv run --no-sync localmusictune"
Write-Host "Avoid: uv sync --extra cpu  (overwrites ROCm torch)"
