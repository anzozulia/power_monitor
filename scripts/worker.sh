#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! pg_isready -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER:-power_monitor}" -q; do
    sleep 1
done
echo "PostgreSQL is ready!"

# Wait for migrations to be applied (give app container time)
sleep 5

# Run the background tasks
exec python src/manage.py runworker
