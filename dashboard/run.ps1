# Launch the Streamlit dashboard in Windows PowerShell

$ErrorActionPreference = "Stop"

Write-Host "🎨 Starting AEGIS-AMDI-OS Dashboard..." -ForegroundColor Cyan

# Check if API is running
$ApiUrl = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8000" }
Write-Host "📡 Expecting API at: $ApiUrl" -ForegroundColor Yellow

# Check dependencies
try {
    python -c "import streamlit, plotly, requests, pandas, networkx, matplotlib" 2>$null
} catch {
    Write-Host "❌ Dependencies missing. Installing..." -ForegroundColor Red
    pip install streamlit requests pandas plotly networkx matplotlib
}

# Launch
$DashboardPort = if ($env:DASHBOARD_PORT) { $env:DASHBOARD_PORT } else { 8501 }

streamlit run dashboard/app.py `
    --server.port=$DashboardPort `
    --server.address=0.0.0.0 `
    --browser.gatherUsageStats=$false `
    --theme.base=dark `
    --theme.primaryColor=#4fc3f7 `
    --theme.backgroundColor=#0a0e1a `
    --theme.secondaryBackgroundColor=#1a1f2e

Write-Host "✅ Dashboard started at http://localhost:$DashboardPort" -ForegroundColor Green
