[CmdletBinding()]
param(
    [switch]$EffectsOnly,
    [string]$PalworldPak = $env:PALWORLD_PAK,
    [string]$ModsDirectory = $env:PALWORLD_MODS
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $root "scripts\build_passives.py"
$repak = Join-Path $root "tools\repak\repak.exe"

if (-not $PalworldPak) {
    $PalworldPak = "C:\Program Files (x86)\Steam\steamapps\common\Palworld\Pal\Content\Paks\Pal-Windows.pak"
}
if (-not $ModsDirectory) {
    $ModsDirectory = Join-Path (Split-Path -Parent $PalworldPak) "~mods"
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found. Install Python 3.10+ and run this script again."
}
if (-not (Test-Path -LiteralPath $script)) {
    throw "Build script not found: $script"
}
if (-not (Test-Path -LiteralPath $repak)) {
    throw "repak.exe not found: $repak"
}
if (-not (Test-Path -LiteralPath $PalworldPak)) {
    throw "Palworld pak not found: $PalworldPak`nSet -PalworldPak or PALWORLD_PAK if the game is installed elsewhere."
}

if (Get-Process -Name "Palworld-Win64-Shipping", "Palworld" -ErrorAction SilentlyContinue) {
    throw "Palworld is running. Close it before installing the mod."
}

$buildArguments = @($script)
if ($EffectsOnly) {
    $buildArguments += "--effects-only"
}
$env:PALWORLD_PAK = $PalworldPak
& python $buildArguments
if ($LASTEXITCODE -ne 0) {
    throw "The mod build failed with exit code $LASTEXITCODE."
}

$pakName = if ($EffectsOnly) {
    "ReadablePassiveNames_EffectsOnly_P.pak"
} else {
    "ReadablePassiveNames_P.pak"
}
$builtPak = Join-Path $root "dist\$pakName"
if (-not (Test-Path -LiteralPath $builtPak)) {
    throw "Build completed but the pak was not created: $builtPak"
}

if (-not (Test-Path -LiteralPath $ModsDirectory)) {
    New-Item -ItemType Directory -Path $ModsDirectory | Out-Null
}
$destination = Join-Path $ModsDirectory $pakName
Copy-Item -LiteralPath $builtPak -Destination $destination -Force

Write-Host "Installed $pakName"
Write-Host "Location: $destination"
