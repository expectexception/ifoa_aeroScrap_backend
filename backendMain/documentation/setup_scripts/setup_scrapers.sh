#!/bin/bash
# Setup script for new scraper system
# Run this to install dependencies and prepare the system

set -e  # Exit on error

echo "=================================="
echo "Scraper System Setup"
echo "=================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

echo "Project root: $PROJECT_ROOT"

# Activate virtual environment
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    echo "✓ Activating virtual environment..."
    source "$PROJECT_ROOT/.venv/bin/activate"
else
    echo "❌ Virtual environment not found at $PROJECT_ROOT/.venv"
    echo "Please create one first: python3 -m venv .venv"
    exit 1
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install playwright aiohttp beautifulsoup4 lxml

# Install Playwright browsers
echo ""
echo "🌐 Installing Playwright browsers..."
playwright install chromium
echo "✓ Chromium installed"

# Create log directories
echo ""
echo "📁 Creating log directories..."
mkdir -p "$PROJECT_ROOT/backendMain/logs/scrapers"
chmod 755 "$PROJECT_ROOT/backendMain/logs"
chmod 755 "$PROJECT_ROOT/backendMain/logs/scrapers"
echo "✓ Log directories created"

# Create output directory for scrapers
echo ""
echo "📁 Creating scraper output directory..."
mkdir -p "$PROJECT_ROOT/backendMain/scraper_manager/Scrapers/output"
chmod 755 "$PROJECT_ROOT/backendMain/scraper_manager/Scrapers/output"
echo "✓ Output directory created"

# Run migrations
echo ""
echo "🗄️  Running database migrations..."
cd "$PROJECT_ROOT/backendMain"
python manage.py makemigrations scraper_manager
python manage.py migrate
echo "✓ Migrations complete"

# Create scraper configs (if needed)
echo ""
echo "⚙️  Setting up scraper configurations..."
python manage.py shell << EOF
from scraper_manager.models import ScraperConfig

# Define new scrapers
scrapers = [
    ('signature', 'Signature Aviation'),
    ('flygosh', 'Flygosh Jobs'),
    ('aap', 'AAP Aviation'),
    ('aviationjobsearch', 'Aviation Job Search'),
    ('goose', 'GOOSE Recruitment'),
]

for scraper_name, display_name in scrapers:
    config, created = ScraperConfig.objects.get_or_create(
        scraper_name=scraper_name,
        defaults={
            'is_enabled': True,
            'description': f'{display_name} scraper',
            'max_pages': 10,
            'timeout': 300,
            'retry_count': 3,
        }
    )
    if created:
        print(f'✓ Created config for {scraper_name}')
    else:
        print(f'  Config for {scraper_name} already exists')

print('\\n✓ Scraper configurations ready')
EOF

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "🚀 Quick Start:"
echo ""
echo "1. List available scrapers:"
echo "   python manage.py run_scraper --list"
echo ""
echo "2. Test a scraper:"
echo "   python manage.py run_scraper signature --max-jobs 10"
echo ""
echo "3. Check recent jobs:"
echo "   python manage.py scraper_status --recent"
echo ""
echo "4. Start Django server (in another terminal):"
echo "   python manage.py runserver"
echo ""
echo "5. Test API endpoint:"
echo "   curl http://localhost:8000/api/scrapers/list/"
echo ""
echo "📚 Documentation:"
echo "   - backendMain/scraper_manager/UNIFIED_SCRAPER_SYSTEM.md"
echo "   - SCRAPER_INTEGRATION_SUMMARY.md"
echo ""
