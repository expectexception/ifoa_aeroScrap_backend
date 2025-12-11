#!/bin/bash
# PostgreSQL Setup Script for AeroOps Backend
# This script sets up PostgreSQL database, user, and permissions

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values (can be overridden by .env)
DEFAULT_DB_NAME="aeroops_db"
DEFAULT_DB_USER="aeroops_user"
DEFAULT_DB_PASSWORD="aeroops_secure_pass_$(date +%s)"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}PostgreSQL Setup for AeroOps Backend${NC}"
echo -e "${BLUE}============================================${NC}\n"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL is not installed!${NC}"
    echo -e "${YELLOW}Install with: sudo apt-get install postgresql postgresql-contrib${NC}"
    exit 1
fi

echo -e "${GREEN}✓ PostgreSQL is installed${NC}"

# Check if PostgreSQL service is running
if ! sudo systemctl is-active --quiet postgresql; then
    echo -e "${YELLOW}PostgreSQL service is not running. Starting...${NC}"
    sudo systemctl start postgresql
    sleep 2
fi

echo -e "${GREEN}✓ PostgreSQL service is running${NC}\n"

# Prompt for database details
echo -e "${BLUE}Enter database configuration (press Enter for defaults):${NC}"
read -p "Database name [$DEFAULT_DB_NAME]: " DB_NAME
DB_NAME=${DB_NAME:-$DEFAULT_DB_NAME}

read -p "Database user [$DEFAULT_DB_USER]: " DB_USER
DB_USER=${DB_USER:-$DEFAULT_DB_USER}

read -sp "Database password [$DEFAULT_DB_PASSWORD]: " DB_PASSWORD
echo
DB_PASSWORD=${DB_PASSWORD:-$DEFAULT_DB_PASSWORD}

read -p "Database host [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Database port [5432]: " DB_PORT
DB_PORT=${DB_PORT:-5432}

echo -e "\n${BLUE}============================================${NC}"
echo -e "${BLUE}Creating PostgreSQL Database${NC}"
echo -e "${BLUE}============================================${NC}\n"

# Create SQL commands
SQL_COMMANDS=$(cat <<EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Connect to the new database and grant schema privileges
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
EOF
)

# Execute SQL commands as postgres user
echo "$SQL_COMMANDS" | sudo -u postgres psql

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Database and user created successfully!${NC}\n"
else
    echo -e "\n${RED}✗ Failed to create database${NC}\n"
    exit 1
fi

# Update .env file
ENV_FILE="$(dirname "$0")/.env"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Updating .env file${NC}"
echo -e "${BLUE}============================================${NC}\n"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}No .env file found. Creating from example...${NC}"
    cp "$(dirname "$0")/../documents/.env.example" "$ENV_FILE" 2>/dev/null || true
fi

# Update .env file with new values
if [ -f "$ENV_FILE" ]; then
    # Backup original
    cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Update or add PostgreSQL configuration
    sed -i "s/^DB_USE_POSTGRES=.*/DB_USE_POSTGRES=1/" "$ENV_FILE"
    sed -i "s/^DB_NAME=.*/DB_NAME=$DB_NAME/" "$ENV_FILE"
    sed -i "s/^DB_USER=.*/DB_USER=$DB_USER/" "$ENV_FILE"
    sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=$DB_PASSWORD/" "$ENV_FILE"
    sed -i "s/^DB_HOST=.*/DB_HOST=$DB_HOST/" "$ENV_FILE"
    sed -i "s/^DB_PORT=.*/DB_PORT=$DB_PORT/" "$ENV_FILE"
    
    echo -e "${GREEN}✓ .env file updated${NC}\n"
else
    echo -e "${YELLOW}⚠ Could not find .env file to update${NC}"
    echo -e "${YELLOW}Please manually update your .env file with:${NC}"
    echo -e "DB_USE_POSTGRES=1"
    echo -e "DB_NAME=$DB_NAME"
    echo -e "DB_USER=$DB_USER"
    echo -e "DB_PASSWORD=$DB_PASSWORD"
    echo -e "DB_HOST=$DB_HOST"
    echo -e "DB_PORT=$DB_PORT\n"
fi

# Test connection
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Testing Database Connection${NC}"
echo -e "${BLUE}============================================${NC}\n"

export PGPASSWORD="$DB_PASSWORD"
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database connection successful!${NC}\n"
else
    echo -e "${RED}✗ Database connection failed${NC}\n"
    exit 1
fi

# Run migrations
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Running Django Migrations${NC}"
echo -e "${BLUE}============================================${NC}\n"

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    PYTHON_CMD=".venv/bin/python"
elif [ -d "venv" ]; then
    source venv/bin/activate
    PYTHON_CMD="venv/bin/python"
else
    PYTHON_CMD="python3"
fi

echo -e "${YELLOW}Making migrations...${NC}"
$PYTHON_CMD manage.py makemigrations

echo -e "\n${YELLOW}Applying migrations...${NC}"
$PYTHON_CMD manage.py migrate

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Migrations completed successfully!${NC}\n"
else
    echo -e "\n${RED}✗ Migration failed${NC}\n"
    exit 1
fi

# Create superuser prompt
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Create Django Superuser${NC}"
echo -e "${BLUE}============================================${NC}\n"

read -p "Would you like to create a Django superuser? (y/n): " CREATE_SUPERUSER

if [[ $CREATE_SUPERUSER =~ ^[Yy]$ ]]; then
    $PYTHON_CMD manage.py createsuperuser
fi

# Summary
echo -e "\n${BLUE}============================================${NC}"
echo -e "${GREEN}✓ PostgreSQL Setup Complete!${NC}"
echo -e "${BLUE}============================================${NC}\n"

echo -e "${BLUE}Database Details:${NC}"
echo -e "  Database: ${GREEN}$DB_NAME${NC}"
echo -e "  User:     ${GREEN}$DB_USER${NC}"
echo -e "  Host:     ${GREEN}$DB_HOST${NC}"
echo -e "  Port:     ${GREEN}$DB_PORT${NC}\n"

echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Start your Django server: ${YELLOW}python manage.py runserver${NC}"
echo -e "  2. Access admin panel: ${YELLOW}http://localhost:8000/admin/${NC}"
echo -e "  3. Test your APIs: ${YELLOW}python test_auth.py${NC}\n"

echo -e "${BLUE}Connection String:${NC}"
echo -e "  ${YELLOW}postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME${NC}\n"

echo -e "${BLUE}Useful PostgreSQL Commands:${NC}"
echo -e "  Connect to DB:    ${YELLOW}psql -h $DB_HOST -U $DB_USER -d $DB_NAME${NC}"
echo -e "  List databases:   ${YELLOW}psql -U postgres -l${NC}"
echo -e "  Database shell:   ${YELLOW}python manage.py dbshell${NC}\n"

echo -e "${GREEN}Setup completed successfully!${NC}\n"
