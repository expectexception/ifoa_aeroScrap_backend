#!/bin/bash
# Start Celery Worker and Beat for AeroOps Intel Backend

cd "$(dirname "$0")/backendMain"

echo "=================================="
echo "🚀 Starting Celery Services"
echo "=================================="
echo ""

# Activate virtual environment
if [ -f "../.venv/bin/activate" ]; then
    source ../.venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found, using system Python"
fi

echo ""
echo "Starting Celery worker and beat..."
echo "Press Ctrl+C to stop"
echo ""

# Start both worker and beat in development mode
celery -A backendMain worker --beat --loglevel=info

# Note: For production, run these as separate processes:
# Terminal 1: celery -A backendMain worker -l info
# Terminal 2: celery -A backendMain beat -l info
