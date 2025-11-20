#!/usr/bin/env python
"""
Command-line scripts for development tasks.
Use with: uv run python scripts.py <command>
"""
import subprocess
import sys


def dev():
    """Start development server with uvicorn"""
    subprocess.run([
        "uvicorn", "config.asgi:application",
        "--reload", "--host", "0.0.0.0", "--port", "8000"
    ])


def migrate():
    """Run database migrations"""
    subprocess.run(["python", "manage.py", "migrate"])


def makemigrations():
    """Create new migrations"""
    subprocess.run(["python", "manage.py", "makemigrations"])


def shell():
    """Start Django shell"""
    subprocess.run(["python", "manage.py", "shell"])


def createsuperuser():
    """Create superuser"""
    subprocess.run(["python", "manage.py", "createsuperuser"])


def test():
    """Run tests"""
    subprocess.run(["pytest"])


def coverage():
    """Run tests with coverage"""
    subprocess.run([
        "pytest", "--cov=apps",
        "--cov-report=html", "--cov-report=term-missing"
    ])


def format_code():
    """Format code with black and isort"""
    subprocess.run(["black", "apps/", "config/", "core/"])
    subprocess.run(["isort", "apps/", "config/", "core/"])


def lint():
    """Lint code with flake8"""
    subprocess.run(["flake8", "apps/", "config/", "core/"])


def celery_worker():
    """Start Celery worker"""
    subprocess.run(["celery", "-A", "config", "worker", "-l", "info"])


def celery_beat():
    """Start Celery beat scheduler"""
    subprocess.run(["celery", "-A", "config", "beat", "-l", "info"])


if __name__ == "__main__":
    commands = {
        "dev": dev,
        "migrate": migrate,
        "makemigrations": makemigrations,
        "shell": shell,
        "createsuperuser": createsuperuser,
        "test": test,
        "coverage": coverage,
        "format": format_code,
        "lint": lint,
        "celery-worker": celery_worker,
        "celery-beat": celery_beat,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Available commands:")
        for cmd in commands.keys():
            print(f"  - {cmd}")
        sys.exit(1)

    commands[sys.argv[1]]()
