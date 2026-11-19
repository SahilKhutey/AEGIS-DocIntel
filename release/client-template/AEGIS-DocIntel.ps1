<#
.SYNOPSIS
    AEGIS-DocIntel Evaluation Client Launcher for Windows
.DESCRIPTION
    Verifies installation integrity, initializes the local loopback proxy,
    launches the standalone application, and connects to the AEGIS Evaluation Gateway.
#>
[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AEGIS-DocIntel — Document Intelligence Evaluation      " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify required Python runtime or executable
$PythonCmd = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command "python3" -ErrorAction SilentlyContinue
}

if (-not $PythonCmd) {
    Write-Error "Python 3.10+ runtime is required to execute the launcher supervisor."
    exit 1
}

$LauncherScript = Join-Path $ScriptDir "app\launcher\launcher.py"

if ($CheckOnly) {
    Write-Host "[1/1] Running installation integrity check..." -ForegroundColor Yellow
    & $PythonCmd.Source -c "from app.launcher.launcher import ClientLauncher; l = ClientLauncher(); l.verify_installation_integrity(); print('Installation integrity verified: PASS')"
    exit $LASTEXITCODE
}

Write-Host "Starting application supervisor..." -ForegroundColor Green
& $PythonCmd.Source $LauncherScript
