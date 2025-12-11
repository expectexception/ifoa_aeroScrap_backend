#!/bin/bash
# Setup Cron Job for AeroOps Scrapers
# This script sets up a cron job to run scrapers every 3 hours

PROJECT_DIR="/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain"
SCRIPT_PATH="$PROJECT_DIR/run_scrapers.sh"
CRON_JOB="0 */3 * * * $SCRIPT_PATH"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}AeroOps Scraper Cron Setup${NC}"
echo "=============================="
echo ""

# Check if script exists and is executable
if [ ! -x "$SCRIPT_PATH" ]; then
    echo -e "${RED}Error: Scraper script not found or not executable: $SCRIPT_PATH${NC}"
    echo "Please run this script from the backendMain directory or check the path."
    exit 1
fi

echo "Script path: $SCRIPT_PATH"
echo "Cron schedule: Every 3 hours (0 */3 * * *)"
echo ""

# Check current cron jobs
echo "Current cron jobs for user:"
crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" || echo "No cron jobs found"
echo ""

# Check if our cron job already exists
EXISTING_JOB=$(crontab -l 2>/dev/null | grep "$SCRIPT_PATH" || true)

if [ -n "$EXISTING_JOB" ]; then
    echo -e "${YELLOW}⚠️  Cron job already exists:${NC}"
    echo "$EXISTING_JOB"
    echo ""
    read -p "Do you want to update it? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cron job setup cancelled."
        exit 0
    fi
    # Remove existing job
    crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH" | crontab -
fi

# Add the new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Cron job added successfully!${NC}"
    echo ""
    echo "New cron job:"
    echo "$CRON_JOB"
    echo ""
    echo "Next runs:"
    for i in {0..7}; do
        NEXT_TIME=$(date -d "+$((i*3)) hours" +"%Y-%m-%d %H:%M")
        echo "  $NEXT_TIME"
    done
    echo ""
    echo -e "${GREEN}🎉 Setup complete! Scrapers will run every 3 hours.${NC}"
    echo ""
    echo "To view logs: tail -f $PROJECT_DIR/scraper_manager/logs/scraper_run_*.log"
    echo "To check cron: crontab -l"
    echo "To remove cron: crontab -r"
else
    echo -e "${RED}❌ Failed to add cron job${NC}"
    exit 1
fi

echo ""
echo "Note: Make sure Celery Beat is also running for additional scheduling:"
echo "  celery -A backendMain beat -l info"
echo "  celery -A backendMain worker -l info"