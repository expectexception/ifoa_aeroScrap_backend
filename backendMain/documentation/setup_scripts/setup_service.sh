#!/bin/bash
# Setup script to install and enable the AeroOps Backend service

set -e

echo "============================================"
echo "AeroOps Backend Service Setup"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_FILE="$SCRIPT_DIR/aeroops-backend.service"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}✗ This script must be run as root (use sudo)${NC}" 
   exit 1
fi

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}✗ Service file not found: $SERVICE_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Installing Gunicorn (if not already installed)...${NC}"
cd "$SCRIPT_DIR"
su - rajat -c "cd '$SCRIPT_DIR' && .venv/bin/pip install gunicorn whitenoise psycopg2-binary"
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

echo -e "${YELLOW}Step 2: Creating logs directory...${NC}"
mkdir -p "$SCRIPT_DIR/logs"
chown rajat:rajat "$SCRIPT_DIR/logs"
echo -e "${GREEN}✓ Logs directory created${NC}"
echo ""

echo -e "${YELLOW}Step 3: Copying service file to systemd...${NC}"
cp "$SERVICE_FILE" /etc/systemd/system/aeroops-backend.service
echo -e "${GREEN}✓ Service file copied${NC}"
echo ""

echo -e "${YELLOW}Step 4: Reloading systemd daemon...${NC}"
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd daemon reloaded${NC}"
echo ""

echo -e "${YELLOW}Step 5: Enabling service to start on boot...${NC}"
systemctl enable aeroops-backend.service
echo -e "${GREEN}✓ Service enabled${NC}"
echo ""

echo -e "${YELLOW}Step 6: Starting the service...${NC}"
systemctl start aeroops-backend.service
sleep 2
echo -e "${GREEN}✓ Service started${NC}"
echo ""

echo "============================================"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "============================================"
echo ""
echo "Service Commands:"
echo "  sudo systemctl status aeroops-backend    # Check status"
echo "  sudo systemctl start aeroops-backend     # Start service"
echo "  sudo systemctl stop aeroops-backend      # Stop service"
echo "  sudo systemctl restart aeroops-backend   # Restart service"
echo "  sudo systemctl disable aeroops-backend   # Disable auto-start"
echo "  sudo journalctl -u aeroops-backend -f    # View live logs"
echo ""
echo "Application will be available at: http://localhost:8000"
echo ""

# Show current status
echo "Current Status:"
systemctl status aeroops-backend.service --no-pager
