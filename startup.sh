#!/bin/bash
# Azure App Service startup script for Streamlit
pip install -e /tmp/8deb2f6a3d4a5f3 2>/dev/null || pip install -e .
python -m streamlit run app.py \
    --server.port 8000 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false \
    --server.enableCORS false \
    --server.enableXsrfProtection false
