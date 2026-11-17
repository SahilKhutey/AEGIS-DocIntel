<#
.SYNOPSIS
    AEGIS-DocIntel Demo Edition — Stop Script
.DESCRIPTION
    Gracefully halts AEGIS demo containers.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = (Resolve-Path "$ScriptDir\..").Path
$DeployDir = Join-Path $PackageRoot "deploy"
$ComposeFile = Join-Path $DeployDir "compose.yaml"

Write-Host "Stopping AEGIS Demo containers..." -ForegroundColor Cyan

Push-Location $DeployDir
try {
    docker compose -f $ComposeFile down
    Write-Host "[OK] Containers stopped successfully." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to stop containers." -ForegroundColor Red
} finally {
    Pop-Location
}
