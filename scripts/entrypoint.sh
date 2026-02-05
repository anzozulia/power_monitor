#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! pg_isready -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER:-power_monitor}" -q; do
    sleep 1
done
echo "PostgreSQL is ready!"

# Run migrations
echo "Running migrations..."
python src/manage.py migrate --noinput

# Create admin user if it doesn't exist
echo "Ensuring admin user exists..."
python src/manage.py createadmin || true

# Run startup recovery
echo "Running startup recovery..."
python src/manage.py startup

# Execute the main command
exec "$@"
