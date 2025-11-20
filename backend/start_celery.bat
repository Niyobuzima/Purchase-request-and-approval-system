@echo off
REM Start Celery worker with Upstash Redis configuration
REM This script loads environment variables from .env file

echo Starting Celery worker...
echo NOTE: Make sure .env file is configured with CELERY_BROKER_URL and CELERY_RESULT_BACKEND
echo.

REM The python-decouple library will automatically load from .env file
python -m celery -A config worker -l info --pool=solo
