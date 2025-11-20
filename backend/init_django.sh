#!/bin/bash

# This script initializes the Django project structure

echo "Installing Django and dependencies..."
pip install Django==5.0.1 djangorestframework==3.14.0

echo "Creating Django project..."
django-admin startproject config .

echo "Creating Django apps..."
python manage.py startapp accounts
python manage.py startapp requests
python manage.py startapp approvals
python manage.py startapp documents

# Create apps directory and move apps into it
mkdir -p apps
mv accounts apps/
mv requests apps/
mv approvals apps/
mv documents apps/

# Create __init__.py in apps directory
touch apps/__init__.py

# Create core directory for shared utilities
mkdir -p core
touch core/__init__.py
touch core/exceptions.py
touch core/mixins.py
touch core/utils.py
touch core/permissions.py

# Create media and static directories
mkdir -p media/proforma
mkdir -p media/purchase_orders
mkdir -p media/receipts
mkdir -p static

# Create templates directory
mkdir -p templates/emails

echo "Django project structure created successfully!"
