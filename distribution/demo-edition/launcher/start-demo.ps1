<#
.SYNOPSIS
    AEGIS-DocIntel Demo Edition — Quick Start Launcher
.DESCRIPTION
    Verifies environment prerequisites, checks evaluation license, boots Docker Compose,
    and opens the interactive AEGIS workbench in your default browser.
#>

[CmdletBinding()]
param (
    [switch]$SkipBrowser = $false,
    [switch]$SkipVerification = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = (Resolve-Path "$ScriptDir\..").Path
$DeployDir = Join-Path $PackageRoot "deploy"
$ComposeFile = Join-Path $DeployDir "compose.yaml"

Write-Host @"
====================================================================
           AEGIS-DocIntel — Protected Demo Edition v1.1.0           
   Structured Document Intelligence & Context Optimization Workbench 
====================================================================
"@ -ForegroundColor Cyan

# 1. Verification Step
if (-not $SkipVerification) {
    Write-Host "`n[1/5] Verifying package integrity..." -ForegroundColor Yellow
    $verifyScript = Join-Path $ScriptDir "verify-package.ps1"
    if (Test-Path $verifyScript) {
        & powershell -ExecutionPolicy Bypass -File $verifyScript -PackageRoot $PackageRoot
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Package verification failed. Download archive may be corrupted."
            exit 1
        }
    }
} else {
    Write-Host "`n[1/5] Skipping package verification per request." -ForegroundColor DarkGray
}

# 2. Check Docker
Write-Host "`n[2/5] Checking container runtime..." -ForegroundColor Yellow
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Host "[ERROR] Docker not detected in PATH." -ForegroundColor Red
    Write-Host "Please install Docker Desktop (https://www.docker.com/products/docker-desktop) and try again."
    exit 1
}

try {
    $null = docker info 2>&1
    Write-Host " [OK] Docker daemon is running." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker daemon is not running. Please start Docker Desktop and retry." -ForegroundColor Red
    exit 1
}

# 3. Check License
Write-Host "`n[3/5] Inspecting evaluation license..." -ForegroundColor Yellow
$licPath = Join-Path $PackageRoot "license\evaluation.lic"
if (Test-Path $licPath) {
    try {
        $licJson = Get-Content $licPath -Raw | ConvertFrom-Json
        $expDate = [DateTime]::Parse($licJson.payload.expires_at)
        $now = [DateTime]::UtcNow
        $remaining = ($expDate - $now).Days
        if ($remaining -lt 0) {
            Write-Host " [WARNING] Evaluation license expired on $($expDate.ToString('yyyy-MM-dd'))." -ForegroundColor Red
            Write-Host " Please contact sales@aegis-docintel.io for renewal."
        } else {
            Write-Host " [OK] License Active: Evaluation Tier ($remaining days remaining)." -ForegroundColor Green
            Write-Host "      Daily Query Quota: $($licJson.payload.quotas.max_queries_per_day)" -ForegroundColor Gray
            Write-Host "      Max Documents:     $($licJson.payload.quotas.max_documents)" -ForegroundColor Gray
        }
    } catch {
        Write-Host " [INFO] Evaluation license loaded." -ForegroundColor Green
    }
} else {
    Write-Host " [INFO] No local license file found; using automatic trial activation." -ForegroundColor Cyan
}

# 4. Launch Containers
Write-Host "`n[4/5] Starting AEGIS Demo containers..." -ForegroundColor Yellow
Push-Location $DeployDir
try {
    docker compose -f $ComposeFile up -d
    Write-Host " [OK] Containers started." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to start containers via Docker Compose." -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location

# 5. Readiness Probe
Write-Host "`n[5/5] Waiting for workbench readiness..." -ForegroundColor Yellow
$targetUrl = "http://localhost:3000"
$maxRetries = 25
$ready = $false

for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "$targetUrl/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        # Retry
    }
    Start-Sleep -Seconds 1
    Write-Host -NoNewline "."
}

Write-Host ""
if ($ready) {
    Write-Host "`n[SUCCESS] AEGIS-DocIntel Demo is ready!" -ForegroundColor Green
    Write-Host "====================================================================" -ForegroundColor Cyan
    Write-Host " Workbench URL:  $targetUrl" -ForegroundColor White
    Write-Host " Synthetic Data: demo-data/ (Sample hardware specs & security paper)" -ForegroundColor Gray
    Write-Host " Control Script: .\stop-demo.ps1 to halt containers" -ForegroundColor Gray
    Write-Host "====================================================================" -ForegroundColor Cyan

    if (-not $SkipBrowser) {
        Write-Host "Opening $targetUrl in your browser..." -ForegroundColor Cyan
        Start-Process $targetUrl
    }
} else {
    Write-Host "`n[WARNING] Workbench took longer than expected to report healthy." -ForegroundColor Yellow
    Write-Host "Check container logs with: docker compose -f deploy/compose.yaml logs"
}
