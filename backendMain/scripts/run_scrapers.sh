#!/bin/bash
# AeroOps Scraper Runner Script
# Runs all scrapers with comprehensive logging every 3 hours

# Configuration
PROJECT_DIR="/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain"
VENV_DIR="$PROJECT_DIR/.venv"
LOG_DIR="$PROJECT_DIR/scraper_manager/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/scraper_run_$TIMESTAMP.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") $*" | tee -a "$LOG_FILE"
}

# Error logging
error_log() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") ERROR: $*" >&2 | tee -a "$LOG_FILE"
}

# Check if we're in the right directory
cd "$PROJECT_DIR" || {
    error_log "Cannot change to project directory: $PROJECT_DIR"
    exit 1
}

# Activate virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    log "Virtual environment activated"
else
    error_log "Virtual environment not found at: $VENV_DIR"
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

log "=========================================="
log "🚀 STARTING AEROOOPS SCRAPER SESSION"
log "=========================================="
log "Timestamp: $TIMESTAMP"
log "Project Directory: $PROJECT_DIR"
log "Log File: $LOG_FILE"
log "=========================================="

# Check Django environment
log "Checking Django environment..."
python manage.py check --deploy 2>&1 | tee -a "$LOG_FILE"
if [ $? -ne 0 ]; then
    error_log "Django environment check failed"
    exit 1
fi

# Run all scrapers with logging
log "Starting scraper execution..."
START_TIME=$(date +%s)

python manage.py run_all_scrapers_with_logging \
    --log-level INFO \
    2>&1 | tee -a "$LOG_FILE"

SCRAPER_EXIT_CODE=$?

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

log "=========================================="
log "📊 SESSION SUMMARY"
log "=========================================="
log "Duration: ${DURATION} seconds"
log "Exit Code: $SCRAPER_EXIT_CODE"
log "Log File: $LOG_FILE"

# Check exit code and report
if [ $SCRAPER_EXIT_CODE -eq 0 ]; then
    log "✅ All scrapers completed successfully"
    SUBJECT="✅ AeroOps Scrapers: SUCCESS"
    COLOR=$GREEN
elif [ $SCRAPER_EXIT_CODE -eq 1 ]; then
    log "⚠️  Some scrapers completed with warnings"
    SUBJECT="⚠️  AeroOps Scrapers: PARTIAL SUCCESS"
    COLOR=$YELLOW
else
    log "❌ Scraper execution failed"
    SUBJECT="❌ AeroOps Scrapers: FAILED"
    COLOR=$RED
fi

log "=========================================="
log "🏁 SESSION COMPLETE"
log "=========================================="

# Optional: Send email notification (uncomment and configure if needed)
# echo "Scrapers completed. Check log: $LOG_FILE" | mail -s "$SUBJECT" your-email@example.com

# Clean up old log files (keep last 30 days)
log "Cleaning up old log files..."
find "$LOG_DIR" -name "scraper_run_*.log" -mtime +30 -delete 2>/dev/null || true

log "Cleanup completed"

exit $SCRAPER_EXIT_CODE