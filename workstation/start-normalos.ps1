# normalOS Workstation — Startet alle Kern-Dienste
param(
    [switch]$FusionOnly,
    [switch]$BridgeOnly,
    [switch]$DocsOnly,
    [switch]$NoBrowser
)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "load-env.ps1")

$Python = "C:\Users\Admin\venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }
$FusionRoot = $env:FUSION_HERO_ROOT
$NormalRoot = $env:NORMALOS_ROOT

function Start-BackgroundJob([string]$Name, [string]$Dir, [string]$Command) {
    $existing = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match [regex]::Escape($Name) }
    if ($existing) {
        Write-Host "[$Name] läuft bereits (PID $($existing.ProcessId))" -ForegroundColor Yellow
        return
    }
    Start-Process -FilePath $Python -ArgumentList $Command -WorkingDirectory $Dir -WindowStyle Minimized
    Write-Host "[$Name] gestartet" -ForegroundColor Green
}

Write-Host "=== normalOS Workstation Start ===" -ForegroundColor Cyan

if (-not $BridgeOnly -and -not $DocsOnly) {
    Write-Host "[Fusion Hero OS] start_all.ps1 ..." -ForegroundColor Cyan
    & (Join-Path $FusionRoot "start_all.ps1")
}

if (-not $FusionOnly -and -not $DocsOnly) {
    Start-BackgroundJob "grok_pc_bridge" $NormalRoot "-m src.normal_os.bridge.grok_pc_bridge"
}

if (-not $FusionOnly -and -not $BridgeOnly) {
    $docsScript = Join-Path $FusionRoot "tools\hero-docs-server\hero-docs-server.py"
    if (Test-Path $docsScript) {
        Start-BackgroundJob "hero-docs-server" $FusionRoot $docsScript
    } else {
        $docsRoot = Join-Path $FusionRoot "hero-docs-server.py"
        if (Test-Path $docsRoot) {
            Start-BackgroundJob "hero-docs-server" $FusionRoot "hero-docs-server.py"
        }
    }
}

Start-Sleep -Seconds 3
& (Join-Path $PSScriptRoot "status.ps1")

if (-not $NoBrowser) {
    Start-Process "http://127.0.0.1:8000"
}