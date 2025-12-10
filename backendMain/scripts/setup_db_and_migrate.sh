#!/usr/bin/env bash
# Setup / reset Postgres role+DB for the project, install deps and run migrations.
# Usage:
#   ./scripts/setup_db_and_migrate.sh [--reset] [--role NAME] [--db NAME] [--password PWD|--auto-pass] [--venv PATH] [--runserver]
# Examples:
#   ./scripts/setup_db_and_migrate.sh --role aero_user --db aero_db --auto-pass --reset --runserver

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${ROOT_DIR}/.venv"

# Defaults
DB_ROLE="aero_user"
DB_NAME="aero_db"
DB_HOST="127.0.0.1"
DB_PORT="5432"
DB_PASSWORD=""
RESET_DB=0
AUTO_PASS=0
RUNSERVER=0

print_help(){
  sed -n '1,120p' "${BASH_SOURCE[0]}" | sed -n '1,120p'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reset) RESET_DB=1; shift ;;
    --role) DB_ROLE="$2"; shift 2 ;;
    --db) DB_NAME="$2"; shift 2 ;;
    --password) DB_PASSWORD="$2"; shift 2 ;;
    --auto-pass) AUTO_PASS=1; shift ;;
    --venv) VENV_PATH="$2"; shift 2 ;;
    --runserver) RUNSERVER=1; shift ;;
    -h|--help) print_help; exit 0 ;;
    *) echo "Unknown arg: $1"; print_help; exit 1 ;;
  esac
done

if [[ "$AUTO_PASS" -eq 1 && -z "$DB_PASSWORD" ]]; then
  # generate a reasonably strong password
  if command -v openssl >/dev/null 2>&1; then
    DB_PASSWORD=$(openssl rand -base64 18)
  else
    DB_PASSWORD=$(head -c 24 /dev/urandom | base64)
  fi
  echo "Auto-generated DB password: ${DB_PASSWORD}"
fi

if [[ -z "$DB_PASSWORD" ]]; then
  # prompt for password
  echo -n "Enter password for Postgres role '${DB_ROLE}' (leave empty to prompt interactively in psql): "; read -s DB_PASSWORD; echo
fi

echo "Using settings: ROLE=${DB_ROLE}, DB=${DB_NAME}, HOST=${DB_HOST}, PORT=${DB_PORT}, VENV=${VENV_PATH}"

# Ensure postgres control commands will run
echo "Checking for 'sudo -u postgres psql' availability..."
if ! sudo -u postgres psql -c '\l' >/dev/null 2>&1; then
  echo "Warning: unable to run 'sudo -u postgres psql'. Ensure you have sudo rights or run these parts manually."
fi

if [[ "$RESET_DB" -eq 1 ]]; then
  echo "Dropping database and role if they exist (reset mode)"
  sudo -u postgres psql -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS \"${DB_NAME}\";" || true
  sudo -u postgres psql -v ON_ERROR_STOP=1 -c "DROP ROLE IF EXISTS \"${DB_ROLE}\";" || true
fi

# Create or alter role
ROLE_EXISTS=0
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_ROLE}'" | grep -q 1; then
  ROLE_EXISTS=1
fi

if [[ "$ROLE_EXISTS" -eq 1 ]]; then
  echo "Role ${DB_ROLE} exists — updating password"
  sudo -u postgres psql -v ON_ERROR_STOP=1 -c "ALTER ROLE \"${DB_ROLE}\" WITH LOGIN PASSWORD '${DB_PASSWORD}';"
else
  echo "Creating role ${DB_ROLE}"
  sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE ROLE \"${DB_ROLE}\" WITH LOGIN PASSWORD '${DB_PASSWORD}';"
fi

# Create database if missing
DB_EXISTS=0
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
  DB_EXISTS=1
fi

if [[ "$DB_EXISTS" -eq 1 ]]; then
  echo "Database ${DB_NAME} already exists"
else
  echo "Creating database ${DB_NAME} owned by ${DB_ROLE}"
  sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"${DB_NAME}\" OWNER \"${DB_ROLE}\";"
fi

echo "Setting up Python virtualenv and installing requirements"
if [[ ! -d "${VENV_PATH}" ]]; then
  python3 -m venv "${VENV_PATH}"
fi

source "${VENV_PATH}/bin/activate"
pip install --upgrade pip wheel
if [[ -f "${ROOT_DIR}/requirements.txt" ]]; then
  pip install -r "${ROOT_DIR}/requirements.txt"
fi

echo "Exporting environment variables for Django"
export DB_USE_POSTGRES=1
export DB_NAME="${DB_NAME}"
export DB_USER="${DB_ROLE}"
export DB_PASSWORD="${DB_PASSWORD}"
export DB_HOST="${DB_HOST}"
export DB_PORT="${DB_PORT}"

cd "${ROOT_DIR}"

echo "Making migrations and migrating database"
python manage.py makemigrations --noinput || true
python manage.py migrate --noinput

echo "Migrations complete. Creating superuser prompt (optional)."
echo "Run: python manage.py createsuperuser to create an admin user interactively."

if [[ "$RUNSERVER" -eq 1 ]]; then
  echo "Starting Django development server at http://127.0.0.1:8000/"
  python manage.py runserver
fi

echo "Done. To use these DB settings in your shell, run:"
cat <<EOF
export DB_USE_POSTGRES=1
export DB_NAME='${DB_NAME}'
export DB_USER='${DB_ROLE}'
export DB_PASSWORD='${DB_PASSWORD}'
export DB_HOST='${DB_HOST}'
export DB_PORT='${DB_PORT}'
EOF

exit 0
