# Lädt .env in die aktuelle PowerShell-Session
$Workstation = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvFile = Join-Path $Workstation ".env"
$FusionEnv = "C:\Users\Admin\fusion-hero-os\.env"

function Import-DotEnv([string]$Path) {
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { return }
        $eq = $line.IndexOf("=")
        if ($eq -lt 1) { return }
        $key = $line.Substring(0, $eq).Trim()
        $val = $line.Substring($eq + 1).Trim()
        if ($val.StartsWith('"') -and $val.EndsWith('"')) { $val = $val.Substring(1, $val.Length - 2) }
        [Environment]::SetEnvironmentVariable($key, $val, "Process")
    }
}

Import-DotEnv $EnvFile
Import-DotEnv $FusionEnv

$env:FUSION_HERO_ROOT = if ($env:FUSION_HERO_ROOT) { $env:FUSION_HERO_ROOT } else { "C:\Users\Admin\fusion-hero-os" }
$env:NORMALOS_ROOT = if ($env:NORMALOS_ROOT) { $env:NORMALOS_ROOT } else { "C:\Users\Admin\normalOS" }
$env:NORMALOS_WORKSTATION = $Workstation