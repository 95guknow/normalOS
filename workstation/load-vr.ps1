# VR-Layer laden: Env-Variablen, Asset-Audit, optional Generierung
$ErrorActionPreference = "Stop"
$Workstation = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $Workstation "load-env.ps1")

$FusionRoot = $env:FUSION_HERO_ROOT
if (-not $FusionRoot) { $FusionRoot = "C:\Users\Admin\fusion-hero-os" }
$env:FUSION_VR_ASSETS_ROOT = Join-Path $FusionRoot "03_VR_Assets"
$env:HEROIC_HIGHEST_LAYER = Join-Path $FusionRoot "03_Code\heroic-highest-layer"

$Python = if ($env:PYTHON_EXE) { $env:PYTHON_EXE } else { "C:\Users\Admin\venv\Scripts\python.exe" }
$GenScript = Join-Path $FusionRoot "03_Code\tools\generate_missing_assets.py"

Write-Host "=== Fusion Hero VR Load ===" -ForegroundColor Cyan
Write-Host "FUSION_VR_ASSETS_ROOT = $($env:FUSION_VR_ASSETS_ROOT)"

if (-not (Test-Path $GenScript)) {
    Write-Warning "generate_missing_assets.py nicht gefunden: $GenScript"
    exit 1
}

# Audit alle Kategorien
& $Python $GenScript --audit 2>&1 | Out-String | Write-Host

if ($args -contains "-Generate") {
    Write-Host "Generiere fehlende Assets (alle Kategorien)..." -ForegroundColor Yellow
    & $Python $GenScript --generate 2>&1 | Out-String | Write-Host
}

Write-Host ""
Write-Host "Endpunkte:" -ForegroundColor Green
Write-Host "  VR Viewer:    http://127.0.0.1:8000/vr/viewer"
Write-Host "  Highest VR:   http://127.0.0.1:8000/highest-layer-vr"
Write-Host "  VR Status:    http://127.0.0.1:8000/api/vr/status"
$PathsFile = Join-Path $Workstation "paths.json"
if (Test-Path $PathsFile) {
    $paths = Get-Content $PathsFile -Raw | ConvertFrom-Json
    $dns = $paths.tailscale.nodes.desktop.magicdns
    if ($dns) {
        Write-Host "  Tailscale:    http://${dns}:8000/vr/viewer"
    }
}