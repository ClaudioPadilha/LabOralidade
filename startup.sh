#!/bin/bash
# Azure App Service startup script for Streamlit

# Install local package (not in requirements.txt — Oryx doesn't support -e .)
pip install --no-deps -e . 2>/dev/null

python -m streamlit run app.py \
    --server.port 8000 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false \
    --server.enableCORS false \
    --server.enableXsrfProtection false
