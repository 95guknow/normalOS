# Tailscale Konto-Diagnose: GitHub vs Google = verschiedene Tailnets
$ErrorActionPreference = "SilentlyContinue"
$ts = "C:\Program Files\Tailscale\tailscale.exe"

Write-Host "=== Tailscale Konto-Check ===" -ForegroundColor Cyan
$j = & $ts status --json 2>&1 | ConvertFrom-Json
if (-not $j) { Write-Host "Tailscale nicht erreichbar" -ForegroundColor Red; exit 1 }

$login = ($j.User.PSObject.Properties | Select-Object -First 1).Value.LoginName
$tailnet = $j.CurrentTailnet.Name
$suffix = $j.MagicDNSSuffix
$selfIp = $j.Self.TailscaleIPs[0]
$peerCount = if ($j.Peer) { @($j.Peer.PSObject.Properties).Count } else { 0 }

Write-Host ""
Write-Host "Dieser PC:" -ForegroundColor Yellow
Write-Host "  Login:    $login"
Write-Host "  Tailnet:  $tailnet"
Write-Host "  MagicDNS: $suffix"
Write-Host "  IP:       $selfIp"
Write-Host "  Host:     $($j.Self.DNSName)"
Write-Host "  Peers:    $peerCount"

if ($peerCount -eq 0) {
    Write-Host ""
    Write-Host "KEINE PEERS sichtbar!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Haeufige Ursache: Handy mit ANDEREM Login (z.B. GitHub)" -ForegroundColor Yellow
    Write-Host "als PC (Google: stephan95g@googlemail.com) -> verschiedene Tailnets!"
    Write-Host ""
    Write-Host "Fix auf dem Handy (Redmi):" -ForegroundColor Green
    Write-Host "  1. Tailscale App -> Einstellungen -> Abmelden"
    Write-Host "  2. Neu anmelden mit GOOGLE (stephan95g@googlemail.com)"
    Write-Host "     NICHT GitHub, wenn der PC Google nutzt"
    Write-Host "  3. App offen lassen, dann: Status-normalOS.bat"
    Write-Host ""
    Write-Host "Alternative: https://login.tailscale.com/admin/machines"
    Write-Host "  Beide Konten zur gleichen Tailnet einladen (Account Linking)"
}

if ($j.Peer) {
    Write-Host ""
    Write-Host "Peers in diesem Tailnet:" -ForegroundColor Green
    $j.Peer.PSObject.Properties | ForEach-Object {
        $p = $_.Value
        $st = if ($p.Online) { "online" } else { "offline" }
        Write-Host "  $($p.HostName) ($($p.OS)) $st - $($p.TailscaleIPs[0])"
    }
}

Write-Host ""
Write-Host "Admin: https://login.tailscale.com/admin/machines"