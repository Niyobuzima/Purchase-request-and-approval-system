#!/bin/bash
# Start Celery worker with Upstash Redis configuration
# This script loads environment variables from .env file

# Load .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    # Safely source .env without word splitting or globbing
    set -a
    source .env
    set +a
else
    echo "WARNING: .env file not found. Celery may not start correctly."
    echo "Please ensure .env file exists with CELERY_BROKER_URL and CELERY_RESULT_BACKEND"
    exit 1
fi

echo "Starting Celery worker..."
python -m celery -A config worker -l info
