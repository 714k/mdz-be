#!/bin/bash

set -e

cd backend

# Activate virtual environment
source venv/bin/activate

# Start services with Docker Compose
docker-compose -f ../docker/docker-compose.yml up -d postgres redis

# Wait for services
sleep 5

# Run migrations
alembic upgrade head

# Start FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000