# Setup script for Windows development environment using uv

Write-Host "🚀 Purchase Request & Approval System - Setup Script" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if uv is installed
try {
    $uvVersion = uv --version
    Write-Host "✅ uv is already installed: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "📦 Installing uv..." -ForegroundColor Yellow
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "🐍 Creating virtual environment..." -ForegroundColor Yellow
    uv venv
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "⚡ Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "📚 Installing dependencies..." -ForegroundColor Yellow
uv pip install -e ".[dev]"

# Create necessary directories
Write-Host "📁 Creating necessary directories..." -ForegroundColor Yellow
$directories = @(
    "media/proforma",
    "media/purchase_orders",
    "media/receipts",
    "static",
    "staticfiles",
    "logs",
    "templates/emails"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Copy .env.example to .env if it doesn't exist
if (-not (Test-Path "../.env")) {
    Write-Host "📝 Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item "../.env.example" "../.env"
    Write-Host "⚠️  Please update .env file with your configuration" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✨ Setup complete! Next steps:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Update ..\.env file with your configuration" -ForegroundColor White
Write-Host "2. Start Docker services:" -ForegroundColor White
Write-Host "   cd .. && docker-compose up -d db redis" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Run migrations:" -ForegroundColor White
Write-Host "   uv run python scripts.py migrate" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Create superuser:" -ForegroundColor White
Write-Host "   uv run python scripts.py createsuperuser" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Start development server with uvicorn:" -ForegroundColor White
Write-Host "   uv run python scripts.py dev" -ForegroundColor Cyan
Write-Host ""
Write-Host "Available commands (via scripts.py):" -ForegroundColor White
Write-Host "   uv run python scripts.py dev              # Start dev server with hot reload" -ForegroundColor Cyan
Write-Host "   uv run python scripts.py migrate          # Run migrations" -ForegroundColor Cyan
Write-Host "   uv run python scripts.py makemigrations   # Create migrations" -ForegroundColor Cyan
Write-Host "   uv run python scripts.py shell            # Django shell" -ForegroundColor Cyan
Write-Host "   uv run python scripts.py test             # Run tests" -ForegroundColor Cyan
Write-Host "   uv run python scripts.py coverage         # Test coverage" -ForegroundColor Cyan
Write-Host "   uv run python scripts.py format           # Format code" -ForegroundColor Cyan
Write-Host "   uv run python scripts.py lint             # Lint code" -ForegroundColor Cyan
Write-Host "   uv run python scripts.py celery-worker    # Start Celery worker" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or use direct commands:" -ForegroundColor White
Write-Host "   uv run uvicorn config.asgi:application --reload --host 0.0.0.0 --port 8000" -ForegroundColor Cyan
Write-Host "   uv run python manage.py migrate" -ForegroundColor Cyan
Write-Host "   uv run pytest" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or use Docker to run everything:" -ForegroundColor White
Write-Host "   cd .. && docker-compose up --build" -ForegroundColor Cyan
Write-Host ""
