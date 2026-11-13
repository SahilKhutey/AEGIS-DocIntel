<#
.SYNOPSIS
    AEGIS-DocIntel Demo Edition — Status Probe
.DESCRIPTION
    Inspects running container state, health status, and license expiration.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = (Resolve-Path "$ScriptDir\..").Path
$DeployDir = Join-Path $PackageRoot "deploy"
$ComposeFile = Join-Path $DeployDir "compose.yaml"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " AEGIS-DocIntel Demo Edition — System Status" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Container status
Push-Location $DeployDir
try {
    docker compose -f $ComposeFile ps
} catch {
    Write-Host "[WARNING] Unable to query docker compose status." -ForegroundColor Yellow
} finally {
    Pop-Location
}

# 2. Probe endpoint
try {
    $res = Invoke-WebRequest -Uri "http://localhost:3000/health" -UseBasicParsing -TimeoutSec 2
    Write-Host "`n[OK] HTTP Endpoint reachable: http://localhost:3000 (Status: $($res.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "`n[OFFLINE] Endpoint http://localhost:3000 is not responding." -ForegroundColor Yellow
}

# 3. License Inspection
$licPath = Join-Path $PackageRoot "license\evaluation.lic"
if (Test-Path $licPath) {
    try {
        $licJson = Get-Content $licPath -Raw | ConvertFrom-Json
        $expDate = [DateTime]::Parse($licJson.payload.expires_at)
        $now = [DateTime]::UtcNow
        $remaining = ($expDate - $now).Days
        Write-Host "`nLicense ID: $($licJson.payload.license_id)" -ForegroundColor White
        Write-Host "Tier:       $($licJson.payload.tier)" -ForegroundColor White
        Write-Host "Expires:    $($licJson.payload.expires_at) ($remaining days left)" -ForegroundColor White
    } catch {
        Write-Host "`n[WARN] Failed to parse license JSON." -ForegroundColor Yellow
    }
}
