"""
Celery configuration for Purchase Request & Approval System.

This module configures Celery for async task processing:
- Document processing (OCR, GPT-4 Vision extraction)
- Email notifications
- PDF generation
- Scheduled tasks (reminders, report generation)
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Create Celery app
app = Celery('purchase_request_system')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # Send daily pending approval reminders at 9 AM
    'send-daily-approval-reminders': {
        'task': 'apps.purchase_requests.tasks.send_approval_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
    # Generate weekly reports every Monday at 8 AM
    'generate-weekly-reports': {
        'task': 'apps.analytics.tasks.generate_weekly_report',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),
    },
    # Clean up old processed documents every Sunday at 2 AM
    'cleanup-old-documents': {
        'task': 'apps.documents.tasks.cleanup_old_documents',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
    },
    # Check for stale requests (pending > 7 days) daily at 10 AM
    'check-stale-requests': {
        'task': 'apps.purchase_requests.tasks.check_stale_requests',
        'schedule': crontab(hour=10, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')
