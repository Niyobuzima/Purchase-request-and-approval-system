#!/bin/bash
# Setup script for development environment using uv

set -e  # Exit on error

echo "🚀 Purchase Request & Approval System - Setup Script"
echo "=================================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "✅ uv is already installed"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🐍 Creating virtual environment..."
    uv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source .venv/bin/activate || . .venv/Scripts/activate

# Install dependencies
echo "📚 Installing dependencies..."
uv pip install -e ".[dev]"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p media/proforma media/purchase_orders media/receipts
mkdir -p static staticfiles logs templates/emails

# Copy .env.example to .env if it doesn't exist
if [ ! -f "../.env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp ../.env.example ../.env
    echo "⚠️  Please update .env file with your configuration"
fi

echo ""
echo "✨ Setup complete! Next steps:"
echo ""
echo "1. Update ../.env file with your configuration"
echo "2. Start Docker services:"
echo "   cd .. && docker-compose up -d db redis"
echo ""
echo "3. Run migrations:"
echo "   uv run python manage.py migrate"
echo ""
echo "4. Create superuser:"
echo "   uv run python manage.py createsuperuser"
echo ""
echo "5. Start development server:"
echo "   uv run python dev.py"
echo ""
echo "Available uv run commands:"
echo "   uv run python dev.py                # Start dev server with hot reload"
echo "   uv run python manage.py migrate    # Run migrations"
echo "   uv run python manage.py makemigrations"
echo "   uv run python manage.py shell"
echo "   uv run python manage.py createsuperuser"
echo "   uv run pytest"
echo "   uv run pytest --cov=apps --cov-report=html"
echo "   uv run black apps/ config/ core/"
echo "   uv run flake8 apps/ config/ core/"
echo "   uv run celery -A config worker -l info"
echo ""
echo "Or use Docker to run everything:"
echo "   cd .. && docker-compose up --build"
echo ""
