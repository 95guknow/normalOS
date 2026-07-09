# normalOS Workstation — Gesamtstatus
$ErrorActionPreference = "SilentlyContinue"
. (Join-Path $PSScriptRoot "load-env.ps1")

$Python = "C:\Users\Admin\venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }
$FusionRoot = $env:FUSION_HERO_ROOT

Write-Host "=== normalOS Workstation Status ===" -ForegroundColor Cyan
Write-Host "Datum: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# Disk
$freeGb = [math]::Round((Get-PSDrive C).Free / 1GB, 1)
Write-Host "[Disk] C: frei: $freeGb GB" -ForegroundColor $(if ($freeGb -lt 20) { "Yellow" } else { "Green" })

# Tailscale + Mesh-Peers
Write-Host "[Tailscale Mesh]" -ForegroundColor Cyan
$tsJson = & "C:\Program Files\Tailscale\tailscale.exe" status --json 2>&1 | ConvertFrom-Json -ErrorAction SilentlyContinue
if ($tsJson -and $tsJson.Self.Online) {
    Write-Host "  Desktop: $($tsJson.Self.DNSName) ($($tsJson.Self.TailscaleIPs[0])) online" -ForegroundColor Green
    $peerCount = 0
    if ($tsJson.Peer) {
        $tsJson.Peer.PSObject.Properties | ForEach-Object {
            $p = $_.Value
            $peerCount++
            $state = if ($p.Online) { "online" } else { "offline" }
            $color = if ($p.Online) { "Green" } else { "DarkGray" }
            Write-Host "  Peer: $($p.DNSName) ($($p.OS)) $state" -ForegroundColor $color
        }
    }
    $phoneExpected = "redmi-note-13-pro-5g"
    $phoneFound = $false
    if ($tsJson.Peer) {
        $tsJson.Peer.PSObject.Properties | ForEach-Object {
            if ($_.Value.HostName -like "*$phoneExpected*" -or $_.Value.DNSName -like "*$phoneExpected*") { $script:phoneFound = $true }
        }
    }
    if (-not $phoneFound) {
        Write-Host "  Phone ($phoneExpected): nicht sichtbar (App offen?)" -ForegroundColor Yellow
    }
    Write-Host "  Peers im Mesh: $peerCount"
} else {
    Write-Host "  Tailscale offline oder nicht installiert" -ForegroundColor Red
}

# Fusion Integration Hub
Write-Host ""
Write-Host "[Fusion Hub]" -ForegroundColor Cyan
if (Test-Path (Join-Path $FusionRoot "fusion_integration_hub.py")) {
    Push-Location $FusionRoot
    $hub = & $Python fusion_integration_hub.py status 2>&1
    Pop-Location
    if ($hub) {
        $parsed = $hub | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($parsed) {
            Write-Host "  Tailscale: $(if ($parsed.tailscale.online) { 'online' } else { 'offline' })"
            Write-Host "  Gesamt: $($parsed.health.overall)" -ForegroundColor Green
            Write-Host "  MCP Connectors: $($parsed.health.connectors)"
            Write-Host "  LLM: $($parsed.health.llm) ($($parsed.llm_summary.available -join ', '))"
            if ($parsed.health.vr) { Write-Host "  VR: $($parsed.health.vr)" }
            Write-Host "  Trinity: thinker=$($parsed.trinity_roles.thinker) worker=$($parsed.trinity_roles.worker) verifier=$($parsed.trinity_roles.verifier)"
        } else {
            $hub | Select-Object -First 8 | ForEach-Object { Write-Host "  $_" }
        }
    }
} else {
    Write-Host "  fusion_integration_hub.py nicht gefunden" -ForegroundColor Yellow
}

# Services (HTTP probes)
Write-Host ""
Write-Host "[Services]" -ForegroundColor Cyan
$services = @{
    "Fusion Dashboard :8000" = "http://127.0.0.1:8000/api/health"
    "Hero Docs        :8088" = "http://127.0.0.1:8088/health"
    "normalOS Bridge  :8765" = "http://127.0.0.1:8765/status"
    "Ollama          :11434" = "http://127.0.0.1:11434/api/tags"
}
foreach ($name in $services.Keys) {
    try {
        $r = Invoke-WebRequest -Uri $services[$name] -UseBasicParsing -TimeoutSec 2
        Write-Host "  $name : OK ($($r.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "  $name : nicht erreichbar" -ForegroundColor DarkGray
    }
}

# API Keys (nur ob gesetzt, nie Werte)
Write-Host ""
Write-Host "[API Keys]" -ForegroundColor Cyan
$keys = @("XAI_API_KEY","ANTHROPIC_API_KEY","OPENAI_API_KEY","GOOGLE_API_KEY","OPENROUTER_API_KEY")
foreach ($k in $keys) {
    $set = [bool]([Environment]::GetEnvironmentVariable($k, "Process") -or [Environment]::GetEnvironmentVariable($k, "User"))
    Write-Host "  $k : $(if ($set) { 'gesetzt' } else { 'fehlt' })" -ForegroundColor $(if ($set) { "Green" } else { "Yellow" })
}
$ollama = try { Invoke-RestMethod "http://127.0.0.1:11434/api/tags" -TimeoutSec 2; "erreichbar" } catch { "offline" }
Write-Host "  Ollama : $ollama"

Write-Host ""
Write-Host "Pfade: $env:NORMALOS_WORKSTATION\paths.json" -ForegroundColor DarkGray