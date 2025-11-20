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
Write-Host "   uv run python manage.py migrate" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Create superuser:" -ForegroundColor White
Write-Host "   uv run python manage.py createsuperuser" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Start development server:" -ForegroundColor White
Write-Host "   uv run python dev.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "Available uv run commands:" -ForegroundColor White
Write-Host "   uv run python dev.py                # Start dev server with hot reload" -ForegroundColor Cyan
Write-Host "   uv run python manage.py migrate    # Run migrations" -ForegroundColor Cyan
Write-Host "   uv run python manage.py makemigrations" -ForegroundColor Cyan
Write-Host "   uv run python manage.py shell" -ForegroundColor Cyan
Write-Host "   uv run python manage.py createsuperuser" -ForegroundColor Cyan
Write-Host "   uv run pytest" -ForegroundColor Cyan
Write-Host "   uv run pytest --cov=apps --cov-report=html" -ForegroundColor Cyan
Write-Host "   uv run black apps/ config/ core/" -ForegroundColor Cyan
Write-Host "   uv run flake8 apps/ config/ core/" -ForegroundColor Cyan
Write-Host "   uv run celery -A config worker -l info" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or use Docker to run everything:" -ForegroundColor White
Write-Host "   cd .. && docker-compose up --build" -ForegroundColor Cyan
Write-Host ""
