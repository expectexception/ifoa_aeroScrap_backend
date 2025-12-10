#!/bin/bash
# Setup script for Celery scheduling

set -e

echo "🔧 Setting up Celery for AeroOps Backend..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "📦 Installing Celery and Redis dependencies..."
pip install -q celery==5.4.0 redis==5.2.0 django-celery-beat==2.7.0 django-celery-results==2.5.1

# Check if Redis is running
echo "🔍 Checking Redis..."
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  Redis not installed. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y redis-server
    elif command -v yum &> /dev/null; then
        sudo yum install -y redis
    else
        echo "❌ Could not install Redis. Please install manually."
        exit 1
    fi
fi

# Start Redis if not running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "🚀 Starting Redis..."
    sudo systemctl start redis
    sudo systemctl enable redis
fi

# Test Redis connection
if redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis is running"
else
    echo "❌ Redis connection failed"
    exit 1
fi

# Run migrations for celery models
echo "🗄️  Running migrations..."
python manage.py migrate

# Create initial ScheduleConfig
echo "⚙️  Creating initial schedule configuration..."
python manage.py shell -c "
from jobs.schedule_models import ScheduleConfig
config = ScheduleConfig.get_config()
print(f'✅ Schedule config created: {config}')
print(f'   Status: {\"ENABLED\" if config.scheduling_enabled else \"DISABLED (safe default)\"}')
"

# Copy systemd service files
echo "📋 Setting up systemd services..."
sudo cp celery-worker.service /etc/systemd/system/
sudo cp celery-beat.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Show status
echo ""
echo "✅ Celery setup complete!"
echo ""
echo "📋 Services created but NOT started (safe default):"
echo "   • celery-worker.service - Celery Worker"
echo "   • celery-beat.service - Celery Beat Scheduler"
echo ""
echo "🔴 Scheduling is DISABLED by default for safety"
echo ""
echo "📖 To enable scheduling:"
echo "   1. Go to Django Admin → Jobs → Schedule Configuration"
echo "   2. Set 'Scheduling Enabled' to TRUE"
echo "   3. Configure email recipients for reports/alerts"
echo "   4. Start services:"
echo "      sudo systemctl start celery-worker"
echo "      sudo systemctl start celery-beat"
echo "      sudo systemctl enable celery-worker"
echo "      sudo systemctl enable celery-beat"
echo ""
echo "📊 To test Celery manually:"
echo "   celery -A backendMain worker --loglevel=info"
echo ""
echo "🧪 To test a task:"
echo "   python manage.py shell"
echo "   >>> from jobs.tasks import debug_task"
echo "   >>> debug_task.delay()"
echo ""
