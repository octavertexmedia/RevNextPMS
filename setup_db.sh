#!/bin/bash
# Database setup script for Channel Manager

echo "Setting up database for Channel Manager..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "ERROR: PostgreSQL is not running or not accessible."
    echo "Please start PostgreSQL first:"
    echo "  macOS: brew services start postgresql"
    echo "  Linux: sudo systemctl start postgresql"
    exit 1
fi

# Database configuration (from .env or defaults)
DB_NAME="${DB_NAME:-channel_manager}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

echo "Creating database: $DB_NAME"

# Try to create database (will fail if it exists, which is okay)
psql -h localhost -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database may already exist or connection failed"

echo "Database setup complete!"
echo ""
echo "Next steps:"
echo "1. Run migrations: python manage.py migrate"
echo "2. Create superuser: python manage.py createsuperuser"
echo "3. Load initial data: python manage.py setup_initial_data"

