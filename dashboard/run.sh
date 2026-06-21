#!/bin/bash
# Launch the Streamlit dashboard

set -e

echo "🎨 Starting AEGIS-AMDI-OS Dashboard..."

# Check if API is running
API_URL="${API_URL:-http://localhost:8000}"
echo "📡 Expecting API at: $API_URL"

# Check dependencies
if ! python -c "import streamlit, plotly, requests, pandas, networkx, matplotlib" 2>/dev/null; then
    echo "❌ Dependencies missing. Installing..."
    pip install streamlit requests pandas plotly networkx matplotlib
fi

# Launch
streamlit run dashboard/app.py \
    --server.port=${DASHBOARD_PORT:-8501} \
    --server.address=0.0.0.0 \
    --browser.gatherUsageStats=false \
    --theme.base=dark \
    --theme.primaryColor=#4fc3f7 \
    --theme.backgroundColor=#0a0e1a \
    --theme.secondaryBackgroundColor=#1a1f2e

echo "✅ Dashboard started at http://localhost:8501"
