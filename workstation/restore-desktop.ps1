# Desktop-Wiederherstellung: Ordner\* eine Ebene hoch, 100% Manifest-Check
param([switch]$VerifyOnly)
$ErrorActionPreference = "Stop"
$Desktop = [Environment]::GetFolderPath("Desktop")
$Ordner = Join-Path $Desktop "Ordner"
$Workstation = Split-Path -Parent $MyInvocation.MyCommand.Path
$Log = Join-Path $Workstation "restore-desktop-log.txt"
$ManifestPath = Join-Path $Workstation "desktop-manifest.json"
$lines = @("Restore Desktop: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")

function Log([string]$msg) { $script:lines += $msg; Write-Host $msg }

function Move-Safe([string]$Src, [string]$DestDir) {
    if (-not (Test-Path $Src)) { return }
    New-Item -ItemType Directory -Force -Path $DestDir | Out-Null
    $name = Split-Path $Src -Leaf
    $dest = Join-Path $DestDir $name
    if (Test-Path $dest) {
        $base = [IO.Path]::GetFileNameWithoutExtension($name)
        $ext = [IO.Path]::GetExtension($name)
        $dest = Join-Path $DestDir "${base}_dup_$(Get-Date -Format 'HHmmss')$ext"
    }
    Move-Item -LiteralPath $Src -Destination $dest -Force
    Log "OK  $Src -> $dest"
}

if (-not $VerifyOnly) {
    if (-not (Test-Path $Ordner)) {
        Log "WARN: Ordner-Wrapper fehlt bereits"
    } else {
        $countBefore = (Get-ChildItem $Ordner -Recurse -File -EA SilentlyContinue | Measure-Object).Count
        Log "Snapshot Ordner: $countBefore Dateien"

        # Temp-Dateien aus projekt_archiv nach Fusion-Hero\archiv-temp
        $tempSrc = Join-Path $Ordner "Projekte\projekt_archiv\desktop-temp-2026-07"
        $tempDest = Join-Path $Ordner "Fusion-Hero\archiv-temp"
        if (Test-Path $tempSrc) {
            New-Item -ItemType Directory -Force -Path $tempDest | Out-Null
            Get-ChildItem $tempSrc -Force | ForEach-Object { Move-Safe $_.FullName $tempDest }
            Remove-Item $tempSrc -Force -EA SilentlyContinue
            Log "OK  desktop-temp-2026-07 -> Fusion-Hero\archiv-temp"
        }

        # Unterordner von Ordner\ eine Ebene auf Desktop\
        $keep = @("LESE-MICH.txt")
        Get-ChildItem $Ordner -Directory | ForEach-Object {
            $target = Join-Path $Desktop $_.Name
            if (Test-Path $target) {
                Log "MERGE  $($_.Name) (Ziel existiert)"
                Get-ChildItem $_.FullName -Force | ForEach-Object { Move-Safe $_.FullName $target }
                Remove-Item $_.FullName -Recurse -Force -EA SilentlyContinue
            } else {
                Move-Item -LiteralPath $_.FullName -Destination $target -Force
                Log "OK  Ordner\$($_.Name) -> Desktop\$($_.Name)"
            }
        }

        # LESE-MICH und leeren Ordner-Wrapper entfernen
        foreach ($f in $keep) {
            $p = Join-Path $Ordner $f
            if (Test-Path $p) { Remove-Item $p -Force }
        }
        Remove-Item $Ordner -Recurse -Force -EA SilentlyContinue
        Log "OK  Ordner-Wrapper entfernt"
    }

    # best-FuHOS Desktop-Stub: nur löschen wenn Projekte\best-FuHOS existiert
    $stub = Join-Path $Desktop "best-FuHOS"
    $canonical = Join-Path $Desktop "Projekte\best-FuHOS"
    if ((Test-Path $stub) -and (Test-Path $canonical)) {
        $stubFiles = @(Get-ChildItem $stub -Recurse -File -EA SilentlyContinue)
        if ($stubFiles.Count -eq 0) {
            try {
                Remove-Item $stub -Recurse -Force -EA Stop
                Log "OK  leerer best-FuHOS-Stub entfernt"
            } catch {
                Log "SKIP best-FuHOS-Stub (gesperrt): $($_.Exception.Message)"
            }
        } else {
            Log "KEEP best-FuHOS-Stub ($($stubFiles.Count) Dateien - manuell pruefen)"
        }
    }
}

# Manifest-Check
$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$searchRoots = @(
    $Desktop,
    (Join-Path $Desktop "Apps")
)
$ok = 0; $missing = @()
foreach ($f in $manifest.files) {
    $found = $false
    foreach ($root in $searchRoots) {
        if (Get-ChildItem $root -Recurse -Filter $f -File -EA SilentlyContinue | Select-Object -First 1) {
            $found = $true; break
        }
        # Wildcard-Fallback fuer Encoding-Sonderfaelle (TM-Zeichen, Umlaute)
        if ($f -match 'Crash Bandicoot') {
            if (Get-ChildItem $root -Recurse -File -EA SilentlyContinue | Where-Object { $_.Name -like '*Crash Bandicoot*.url' } | Select-Object -First 1) {
                $found = $true; break
            }
        }
        if ($f -match 'Aktivierungsschl') {
            if (Get-ChildItem $root -Recurse -File -EA SilentlyContinue | Where-Object { $_.Name -like '*Aktivierungsschl*.pdf' } | Select-Object -First 1) {
                $found = $true; break
            }
        }
    }
    if ($found) { $ok++ } else { $missing += "FILE: $f" }
}
foreach ($d in $manifest.folders) {
    $found = $false
    foreach ($root in $searchRoots) {
        if (Test-Path (Join-Path $root $d)) { $found = $true; break }
        if (Get-ChildItem $root -Recurse -Directory -Filter $d -EA SilentlyContinue | Select-Object -First 1) {
            $found = $true; break
        }
    }
    if ($found) { $ok++ } else { $missing += "DIR: $d" }
}
$total = $manifest.files.Count + $manifest.folders.Count
Log ""
Log "=== Manifest: $ok / $total ==="
if ($missing.Count -gt 0) {
    $missing | ForEach-Object { Log "FEHLT $_" }
} else {
    Log "100% VOLLSTAENDIG"
}

$lines | Set-Content $Log -Encoding UTF8
Write-Host "Log: $Log"