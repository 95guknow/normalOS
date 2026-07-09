# Desktop-Aufräumen für normalOS — sortiert Dateien, behält normalOS sichtbar
$ErrorActionPreference = "Stop"
$Desktop = [Environment]::GetFolderPath("Desktop")
$Log = Join-Path $PSScriptRoot "desktop-organize-log.txt"
$moves = @()

function Move-To([string]$Src, [string]$DestDir) {
    if (-not (Test-Path $Src)) { return }
    New-Item -ItemType Directory -Force -Path $DestDir | Out-Null
    $name = Split-Path $Src -Leaf
    $dest = Join-Path $DestDir $name
    if (Test-Path $dest) {
        $base = [IO.Path]::GetFileNameWithoutExtension($name)
        $ext = [IO.Path]::GetExtension($name)
        $dest = Join-Path $DestDir "${base}_dup_$(Get-Date -Format 'HHmmss')$ext"
    }
    try {
        Move-Item -LiteralPath $Src -Destination $dest -Force -ErrorAction Stop
        $script:moves += "OK  $Src -> $dest"
    } catch {
        $script:moves += "SKIP (gesperrt) $Src"
    }
}

$Apps       = Join-Path $Desktop "Apps"
$Ordner     = Join-Path $Desktop "Ordner"
$Docs       = Join-Path $Ordner "Dokumente"
$Vertraege  = Join-Path $Docs "Vertraege"
$Bilder     = Join-Path $Ordner "Bilder"
$Videos     = Join-Path $Ordner "Videos"
$Spiele     = Join-Path $Ordner "Spiele"
$Fusion     = Join-Path $Ordner "Fusion-Hero"
$Forschung  = Join-Path $Ordner "Forschung"
$System     = Join-Path $Ordner "System-Tools"
$Sonstiges  = Join-Path $Ordner "Sonstiges"
$Projekte   = Join-Path $Ordner "Projekte"

# Tägliche Shortcuts direkt unter Apps/
$dailyApps = @(
    "Visual Studio Code.lnk", "Discord.lnk", "Telegram.lnk",
    "GitHub Desktop.lnk", "Google Drive.lnk", "Kepler.lnk",
    "Antigravity.lnk", "Chrome Remote Desktop.lnk"
)

Get-ChildItem $Desktop -File | ForEach-Object {
    $f = $_
    switch -Regex ($f.Extension.ToLower()) {
        "\.lnk" {
            if ($dailyApps -contains $f.Name) {
                Move-To $f.FullName $Apps
            } elseif ($f.Name -match "Tor|Widelands|Rockstar|Afterburner|SpeedFan|Adwcleaner|NiceHash|UserBenchmark|TeamSpeak|Scrivener") {
                if ($f.Name -match "Tor") { Move-To $f.FullName $System }
                elseif ($f.Name -match "Rockstar|Widelands") { Move-To $f.FullName $Spiele }
                else { Move-To $f.FullName $System }
            } else {
                Move-To $f.FullName $Apps
            }
        }
        "\.url" { Move-To $f.FullName $Spiele }
        "\.(pdf)" {
            if ($f.Name -match "vertrag|Schenkung|konto|BuFDi") { Move-To $f.FullName $Vertraege }
            elseif ($f.Name -match "Geisteskrankheiten|Heroik") { Move-To $f.FullName $Forschung }
            else { Move-To $f.FullName $Docs }
        }
        "\.(docx?)" { Move-To $f.FullName $Docs }
        "\.(jpg|jpeg|png|webp)" { Move-To $f.FullName $Bilder }
        "\.(mp4|mkv|avi)" { Move-To $f.FullName $Videos }
        "\.(md)" {
            if ($f.Name -match "Geisteskrankheiten|Heroik") { Move-To $f.FullName $Forschung }
            else { Move-To $f.FullName $Docs }
        }
        "\.(bat|py|html|ipynb)" {
            if ($f.Name -match "ALTE_Frau|FusionHero|Fusion") { Move-To $f.FullName $Fusion }
            else { Move-To $f.FullName $Sonstiges }
        }
        "\.(exe)" {
            if ($f.Name -match "Heroisch|Firefox") { Move-To $f.FullName $Fusion }
            else { Move-To $f.FullName $Sonstiges }
        }
        "\.(zip|jsonl)" { Move-To $f.FullName $Sonstiges }
        default { Move-To $f.FullName $Sonstiges }
    }
}

# Bestehende Desktop-Ordner (außer normalOS, Apps, Ordner) → Projekte
$keepOnDesktop = @("normalOS", "Apps", "Ordner")
Get-ChildItem $Desktop -Directory | Where-Object { $keepOnDesktop -notcontains $_.Name } | ForEach-Object {
    Move-To $_.FullName $Projekte
}

$lines = @(
    "Desktop organize: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "Moved: $($moves.Count) items",
    ""
) + $moves
$lines | Set-Content $Log -Encoding UTF8
Write-Host "Fertig: $($moves.Count) Elemente sortiert" -ForegroundColor Green
Write-Host "Log: $Log"
Write-Host ""
Write-Host "Desktop jetzt:" -ForegroundColor Cyan
Get-ChildItem $Desktop | Select-Object Name, @{N='Typ';E={if($_.PSIsContainer){'Ordner'}else{'Datei'}}}