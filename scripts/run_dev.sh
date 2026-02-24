#!/bin/bash

set -e

# Activate virtual environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate mdz

# Start services with Docker Compose
docker compose -f ../mdz-infra/docker-compose.yml up -d postgres redis

# Wait for services
sleep 5

# Run migrations
alembic upgrade head

# Start FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000