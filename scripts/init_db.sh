#!/bin/bash

set -e

echo "Initializing database..."

cd backend

# Wait for PostgreSQL
until PGPASSWORD=eK))4%r9/#HVEf2yub84 psql -h localhost -U mdz -d mdz_db -c '\q'; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

# Run migrations
alembic upgrade head

echo "Database initialized successfully!"