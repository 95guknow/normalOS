# Alles mit allem verknuepfen — Master-Linker
param([switch]$StartServices)
$ErrorActionPreference = "SilentlyContinue"
. (Join-Path $PSScriptRoot "load-env.ps1")

$Python = "C:\Users\Admin\venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }
$FusionRoot = $env:FUSION_HERO_ROOT

Write-Host "=== Fusion normalOS — Alles verknuepft ===" -ForegroundColor Cyan
Write-Host ""

# 1. Tailscale Konto-Check (GitHub vs Google)
& (Join-Path $PSScriptRoot "tailscale-account-check.ps1")
Write-Host ""

# 2. Optional: Dienste starten
if ($StartServices) {
    Write-Host "[Start] Dienste ..." -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot "start-normalos.ps1") -NoBrowser
    Write-Host ""
}

# 3. Integration Hub — verknuepfter Graph
Write-Host "[Fusion Hub] Unified Graph" -ForegroundColor Cyan
Push-Location $FusionRoot
$hub = & $Python fusion_integration_hub.py status 2>&1 | ConvertFrom-Json
Pop-Location

if ($hub) {
    Write-Host "  Gesamt:      $($hub.health.overall)"
    Write-Host "  Netzwerk:    $($hub.health.network) | Login: $($hub.tailscale.login)"
    Write-Host "  Connectors:  $($hub.health.connectors)"
    Write-Host "  LLM:         $($hub.health.llm)"
    Write-Host "  Graph-Kanten: $($hub.graph.edge_count)"
    Write-Host "  Workstation: $(if ($hub.workstation.configured) { 'verbunden' } else { 'fehlt' })"
    if ($hub.phone_mesh) {
        $pm = $hub.phone_mesh
        $phoneColor = if ($pm.visible) { "Green" } else { "Yellow" }
        Write-Host "  Handy:       $($pm.expected_hostname) visible=$($pm.visible)" -ForegroundColor $phoneColor
        if ($pm.fix_hint) { Write-Host "  Fix:         $($pm.fix_hint)" -ForegroundColor Yellow }
    }
    Write-Host ""
    Write-Host "  Endpunkte:" -ForegroundColor DarkGray
    Write-Host "    Lokal:    http://127.0.0.1:8088/fusion/status"
    Write-Host "    Mesh:     http://127.0.0.1:8088/fusion/graph"
    Write-Host "    Handy:    http://desktop-kpki9e4.tail391adb.ts.net:8088/fusion/status"
}

Write-Host ""
Write-Host "Fertig. Voller JSON: python fusion_integration_hub.py status" -ForegroundColor DarkGray