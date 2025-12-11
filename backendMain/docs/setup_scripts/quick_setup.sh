#!/bin/bash
# Quick Setup Script for AeroScrap Backend
# Run this script to set up the project quickly

set -e  # Exit on error

echo "=========================================="
echo "  AeroScrap Backend - Quick Setup"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}[1/8]${NC} Checking Python version..."
python_version=$(python3 --version | awk '{print $2}')
echo "      Found Python $python_version"

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}[2/8]${NC} Creating virtual environment..."
    python3 -m venv .venv
    echo "      ✓ Virtual environment created"
else
    echo -e "${YELLOW}[2/8]${NC} Virtual environment already exists"
fi

# Activate virtual environment
echo -e "${YELLOW}[3/8]${NC} Activating virtual environment..."
source .venv/bin/activate
echo "      ✓ Virtual environment activated"

# Install dependencies
echo -e "${YELLOW}[4/8]${NC} Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "      ✓ Dependencies installed"

# Install Playwright browsers
echo -e "${YELLOW}[5/8]${NC} Installing Playwright browsers..."
playwright install chromium --quiet 2>/dev/null || playwright install chromium
echo "      ✓ Playwright browsers installed"

# Create .env from example if not exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[6/8]${NC} Creating .env file from template..."
    cp .env.example .env
    echo "      ✓ .env file created (please edit with your settings)"
else
    echo -e "${YELLOW}[6/8]${NC} .env file already exists"
fi

# Run migrations
echo -e "${YELLOW}[7/8]${NC} Running database migrations..."
python manage.py makemigrations --noinput 2>/dev/null || true
python manage.py migrate --noinput
echo "      ✓ Database migrations complete"

# Create logs directory
echo -e "${YELLOW}[8/8]${NC} Setting up directories..."
mkdir -p logs
mkdir -p scrapers/logs
echo "      ✓ Directories created"

echo ""
echo -e "${GREEN}=========================================="
echo "  ✓ Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your configuration"
echo "  2. Create superuser: python manage.py createsuperuser"
echo "  3. Start server: python manage.py runserver"
echo "  4. Setup scrapers: cd scrapers && bash setup_scheduler.sh"
echo ""
echo "Documentation:"
echo "  • README.md - Quick start guide"
echo "  • PROJECT_OVERVIEW.md - System architecture"
echo "  • API_DOCUMENTATION.txt - API reference"
echo ""
