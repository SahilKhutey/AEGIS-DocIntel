<#
.SYNOPSIS
    AEGIS-DocIntel Client Release Packaging Script
.DESCRIPTION
    PROT-FINAL-11 Production Client Packaging Pipeline.
    Validates source tree, scans for credentials, packages allowlisted artifacts,
    generates checksums, SBOM, and signs release metadata.
#>
[CmdletBinding()]
param(
    [string]$Version = "1.0.0-beta.1",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AEGIS-DocIntel — Release Packaging Pipeline v$Version  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Run build_production_package.py
$BuildScript = Join-Path $RepoRoot "scripts\release\build_production_package.py"
& python $BuildScript

if ($LASTEXITCODE -ne 0) {
    Write-Error "Production package build failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "Production package build completed successfully." -ForegroundColor Green
