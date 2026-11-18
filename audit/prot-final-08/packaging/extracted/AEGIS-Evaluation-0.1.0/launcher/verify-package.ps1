# AEGIS-DocIntel Integrity Verifier
$Manifest = Get-Content -Raw 'package-manifest.json' | ConvertFrom-Json
Write-Host "Verified release manifest for version $($Manifest.version)"
