#Requires -Version 5.1
<#
.SYNOPSIS
  Start LocalMusicTune with ROCm env vars on AMD Windows.

.PARAMETER Fast
  Use bfloat16 (fast). Avoid duration×steps > 1500 (e.g. 30s×60step produces noise).

.PARAMETER Float32
  Force float32 (slow, best quality for long tracks).
#>
param(
    [switch]$Fast,
    [switch]$Float32
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$env:HSA_OVERRIDE_GFX_VERSION = "11.0.0"
$env:ACESTEP_LM_BACKEND = "pt"
$env:MIOPEN_FIND_MODE = "FAST"
$env:ACESTEP_INIT_LLM = "false"

if ($Float32) {
    $env:ACESTEP_ROCM_DTYPE = "float32"
} elseif ($Fast) {
    $env:ACESTEP_ROCM_DTYPE = "bfloat16"
    Write-Host "Fast mode: bfloat16 — keep duration×steps <= 1500 (e.g. 30s×30step OK, 30s×60step NG)" -ForegroundColor Yellow
} else {
    Remove-Item Env:ACESTEP_ROCM_DTYPE -ErrorAction SilentlyContinue
    Write-Host "Default: ACE-Step ROCm float32 (safe). Use -Fast for bfloat16 speed." -ForegroundColor Cyan
}

Write-Host "Starting LocalMusicTune on http://127.0.0.1:7860" -ForegroundColor Green
uv run --no-sync localmusictune
