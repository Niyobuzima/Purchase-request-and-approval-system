#!/usr/bin/env python
"""
Simple development server launcher.
Usage: uv run dev
"""
import subprocess
import sys


def main():
    """Start the development server with uvicorn."""
    sys.exit(subprocess.call([
        "uvicorn",
        "config.asgi:application",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]))


if __name__ == "__main__":
    main()
