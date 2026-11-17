<#
.SYNOPSIS
    AEGIS-DocIntel Demo Edition — Reset Session
.DESCRIPTION
    Purges evaluation session documents and restores initial clean benchmark state.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = (Resolve-Path "$ScriptDir\..").Path
$licPath = Join-Path $PackageRoot "license\evaluation.lic"

Write-Host "Resetting AEGIS Demo session..." -ForegroundColor Cyan

$token = ""
if (Test-Path $licPath) {
    try {
        $raw = Get-Content $licPath -Raw
        $token = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($raw))
    } catch {
        # ignore
    }
}

try {
    $headers = @{}
    if ($token) {
        $headers["X-Evaluation-License"] = $token
    }
    $res = Invoke-RestMethod -Uri "http://localhost:3000/api/v1/gateway/demo/reset" -Method Post -Headers $headers -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[OK] Demo session reset successfully: $($res.status)" -ForegroundColor Green
} catch {
    Write-Host "[INFO] Local web proxy reset attempted. If backend is offline, restart containers using start-demo.ps1." -ForegroundColor Yellow
}
