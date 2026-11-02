<#
.SYNOPSIS
    AEGIS-DocIntel — Windows PowerShell Audit Suite Launcher.

.DESCRIPTION
    Executes the multi-phase release verification, validation, and benchmark audit
    for the AEGIS-DocIntel repository.

.PARAMETER Profile
    Audit profile to execute: 'quick', 'full', 'tests', 'benchmarks', 'security'. Default is 'full'.

.PARAMETER Phase
    Run a specific phase only (1 to 7).

.PARAMETER RunRealCorpus
    Include the real PDF benchmark corpus evaluation run.

.PARAMETER ValidateOnly
    Skip audit execution and run artifact validation only.

.EXAMPLE
    .\run_audit.ps1 -Profile quick
    .\run_audit.ps1 -Profile full -RunRealCorpus
    .\run_audit.ps1 -Profile security
    .\run_audit.ps1 -ValidateOnly
#>

[CmdletBinding()]
param(
    [ValidateSet("quick", "full", "tests", "benchmarks", "security")]
    [string]$Profile = "full",

    [ValidateRange(1, 7)]
    [int]$Phase = 0,

    [switch]$RunRealCorpus,

    [switch]$ValidateOnly,

    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit 0
}

$RepoRoot = $PSScriptRoot
Set-Location $RepoRoot

$env:PYTHONPATH = $RepoRoot
$env:PYTHONIOENCODING = "utf-8"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  AEGIS-DocIntel Complete MVP Audit Suite Launcher (PowerShell)  " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Repository Root: $RepoRoot"
Write-Host "Target Profile:  $Profile"
if ($Phase -gt 0) {
    Write-Host "Target Phase:    Phase $Phase"
}
if ($RunRealCorpus) {
    Write-Host "Real Corpus:     Enabled"
}
Write-Host ""

if ($ValidateOnly) {
    Write-Host "[*] Executing audit artifact validation only..." -ForegroundColor Yellow
    python scripts/validate_audit_artifacts.py
    exit $LASTEXITCODE
}

# Build arguments for run_mvp_audit.py
$AuditArgs = @("scripts/run_mvp_audit.py")

if ($Phase -gt 0) {
    $AuditArgs += @("--phase", "$Phase")
} else {
    $AuditArgs += @("--profile", "$Profile")
}

if ($RunRealCorpus) {
    $AuditArgs += "--run-real-corpus"
}

Write-Host "[*] Launching: python $($AuditArgs -join ' ')" -ForegroundColor Green
python @AuditArgs
$AuditExit = $LASTEXITCODE

Write-Host ""
if ($AuditExit -eq 0) {
    Write-Host "[OK] Audit executed successfully. Validating generated artifacts..." -ForegroundColor Green
    python scripts/validate_audit_artifacts.py
    $ValExit = $LASTEXITCODE
    if ($ValExit -eq 0) {
        Write-Host ""
        Write-Host "=================================================================" -ForegroundColor Green
        Write-Host "  AUDIT COMPLETE AND ARTIFACTS VERIFIED: PASS                    " -ForegroundColor Green
        Write-Host "=================================================================" -ForegroundColor Green
    } else {
        Write-Host "[-] Audit execution passed but artifact validation failed." -ForegroundColor Red
        exit $ValExit
    }
} else {
    Write-Host "[-] Audit execution encountered failures. Code: $AuditExit" -ForegroundColor Red
    exit $AuditExit
}
