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
echo "   uv run migrate"
echo ""
echo "4. Create superuser:"
echo "   uv run createsuperuser"
echo ""
echo "5. Start development server with uvicorn:"
echo "   uv run dev"
echo ""
echo "Available uv run commands:"
echo "   uv run dev              # Start dev server with hot reload"
echo "   uv run migrate          # Run migrations"
echo "   uv run makemigrations   # Create migrations"
echo "   uv run shell            # Django shell"
echo "   uv run test             # Run tests"
echo "   uv run coverage         # Test coverage"
echo "   uv run format           # Format code"
echo "   uv run lint             # Lint code"
echo "   uv run celery-worker    # Start Celery worker"
echo ""
echo "Or use Docker to run everything:"
echo "   cd .. && docker-compose up --build"
echo ""
