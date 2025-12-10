#!/bin/bash

# Playwright Setup Script
# Installs Playwright browsers and system dependencies

echo "=========================================="
echo "PLAYWRIGHT SETUP FOR SCRAPERS"
echo "=========================================="
echo ""

cd "/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend"

echo "Step 1: Activate virtual environment"
echo "-------------------------------------"
source .venv/bin/activate

echo "✅ Virtual environment activated"
echo ""

echo "Step 2: Install Playwright browsers"
echo "------------------------------------"
python -m playwright install chromium

echo ""
echo "Step 3: Verify installation"
echo "----------------------------"
python -c "
from playwright.sync_api import sync_playwright
print('✅ Playwright installed successfully')
print('✅ Chromium browser ready')
"

echo ""
echo "=========================================="
echo "PLAYWRIGHT SETUP COMPLETE"
echo "=========================================="
echo ""
echo "You can now run scrapers with:"
echo "  cd backendMain"
echo "  python3 manage.py run_scraper linkedin --max-jobs 5"
echo ""
