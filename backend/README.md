# Purchase Request & Approval System - Backend

A modern Django REST API backend for a Procure-to-Pay system with AI-powered document processing, built with **uv** for blazing-fast package management.

## 🚀 Features

- **Multi-level Approval Workflow** - Sequential L1 → L2 approval process
- **AI Document Processing** - Automated extraction from proformas and receipts using OpenAI
- **Automatic PO Generation** - PDF purchase orders generated on approval
- **Receipt Validation** - AI-powered comparison against purchase orders
- **Role-Based Access Control** - Staff, Approvers (L1/L2), Finance, Admin roles
- **JWT Authentication** - Secure token-based authentication
- **Celery Background Tasks** - Async document processing
- **PostgreSQL Database** - Production-grade data storage
- **Redis Caching** - Performance optimization
- **Comprehensive API** - RESTful endpoints with Swagger docs

## 📋 Prerequisites

- **Python 3.11+**
- **uv** (package manager)
- **Docker & Docker Compose** (for services)
- **PostgreSQL 15** (via Docker)
- **Redis 7** (via Docker)

## ⚡ Quick Start with uv

### 1. Install uv

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

### 2. Run Setup Script

**Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```powershell
.\setup.ps1
```

### 3. Configure Environment

Update `../.env` with your settings:
```bash
# Database
DB_NAME=procure_db
DB_USER=admin
DB_PASSWORD=your_secure_password

# OpenAI API Key (for document processing)
OPENAI_API_KEY=sk-your-key-here

# Other settings...
```

### 4. Start Services

Start PostgreSQL and Redis:
```bash
cd ..
docker-compose up -d db redis
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Start Development Server

```bash
python manage.py runserver
```

Visit: http://localhost:8000

## 📦 Package Management with uv

### Why uv?

- **10-100x faster** than pip
- **Resolves dependencies in seconds** vs minutes with pip
- **Better caching** and reproducible builds
- **Compatible with pip** - drop-in replacement

### Common Commands

```bash
# Install production dependencies
uv pip install -e .

# Install with development dependencies
uv pip install -e ".[dev]"

# Add a new package
uv pip install package-name

# Update dependencies
uv pip install --upgrade package-name

# Sync from pyproject.toml (recommended)
uv sync --dev
```

### Dependency Management

All dependencies are defined in [pyproject.toml](./pyproject.toml):

- **Production dependencies**: Listed in `[project.dependencies]`
- **Development dependencies**: Listed in `[project.optional-dependencies.dev]`
- **Production extras**: Listed in `[project.optional-dependencies.prod]`

## 🐳 Docker Usage

### Development with Docker

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Production Docker Build

```bash
# Build production image
docker build -f Dockerfile.prod -t procure-backend:prod .

# Run production container
docker run -p 8000:8000 --env-file ../.env procure-backend:prod
```

## 🛠️ Development Workflow

### Using Makefile

```bash
# View all available commands
make help

# Install dependencies
make install-dev

# Run migrations
make migrate

# Create migrations
make makemigrations

# Run development server
make run

# Run tests
make test

# Run tests with coverage
make coverage

# Format code
make format

# Lint code
make lint

# Clean cache files
make clean
```

### Manual Commands

```bash
# Run Django shell
python manage.py shell

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Run Celery worker (in separate terminal)
celery -A config worker -l info

# Run Celery beat (scheduled tasks)
celery -A config beat -l info
```

## 📁 Project Structure

```
backend/
├── apps/
│   ├── accounts/          # User authentication & authorization
│   ├── purchase_requests/ # Purchase request management
│   ├── approvals/         # Multi-level approval workflow
│   └── documents/         # AI document processing
├── config/
│   ├── settings/
│   │   ├── base.py       # Base settings
│   │   ├── development.py # Development settings
│   │   └── production.py  # Production settings
│   ├── urls.py           # Root URL configuration
│   └── wsgi.py           # WSGI application
├── core/
│   ├── exceptions.py     # Custom exceptions
│   ├── mixins.py         # Reusable mixins
│   ├── utils.py          # Utility functions
│   └── permissions.py    # Custom permission classes
├── media/                # Uploaded files
├── static/               # Static files
├── templates/            # Email templates
├── logs/                 # Application logs
├── pyproject.toml        # uv dependencies
├── Dockerfile            # Development Docker image
├── Dockerfile.prod       # Production Docker image
├── Makefile              # Development commands
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

All configuration is done via environment variables (`.env` file):

**Django Settings:**
- `DEBUG` - Debug mode (True/False)
- `SECRET_KEY` - Django secret key
- `ALLOWED_HOSTS` - Comma-separated allowed hosts

**Database:**
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `DB_HOST` - Database host
- `DB_PORT` - Database port

**Redis:**
- `REDIS_URL` - Redis connection URL

**Celery:**
- `CELERY_BROKER_URL` - Celery broker URL
- `CELERY_RESULT_BACKEND` - Celery result backend

**OpenAI:**
- `OPENAI_API_KEY` - OpenAI API key for document processing

**AWS S3 (optional):**
- `USE_S3` - Enable S3 storage (True/False)
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_STORAGE_BUCKET_NAME` - S3 bucket name

### Settings Modules

The project uses environment-specific settings:

- **Development**: `config.settings.development` (default)
- **Production**: `config.settings.production`
- **Staging**: `config.settings.staging`

Set via `DJANGO_SETTINGS_MODULE` or `DJANGO_ENVIRONMENT`:

```bash
# Option 1: Direct module
export DJANGO_SETTINGS_MODULE=config.settings.production

# Option 2: Environment name (recommended)
export DJANGO_ENVIRONMENT=production
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific app tests
pytest apps/accounts/tests/

# Run specific test file
pytest apps/accounts/tests/test_models.py

# Run with verbose output
pytest -v

# Using make
make test
make coverage
```

### Test Structure

```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
├── api/               # API endpoint tests
└── fixtures/          # Test fixtures
```

## 📚 API Documentation

### Swagger UI

Visit http://localhost:8000/api/docs/ for interactive API documentation.

### Key Endpoints

**Authentication:**
- `POST /api/auth/login/` - Login
- `POST /api/auth/refresh/` - Refresh token
- `GET /api/auth/me/` - Get current user

**Purchase Requests:**
- `GET /api/requests/` - List requests
- `POST /api/requests/` - Create request
- `GET /api/requests/{id}/` - Get request details
- `PATCH /api/requests/{id}/approve/` - Approve request
- `PATCH /api/requests/{id}/reject/` - Reject request
- `POST /api/requests/{id}/upload-receipt/` - Upload receipt

**Dashboard:**
- `GET /api/dashboard/stats/` - Get role-specific statistics

See [API_REFERENCE.md](../docs/API_REFERENCE.md) for complete documentation.

## 🔒 Security

### Implemented Security Measures

- **JWT Authentication** - 15-minute access tokens, 7-day refresh tokens
- **Role-Based Permissions** - Granular access control
- **File Upload Validation** - Type, size, and content validation
- **Rate Limiting** - 1000 requests/hour per user
- **SQL Injection Protection** - Django ORM parameterization
- **XSS Prevention** - Template auto-escaping
- **CORS Configuration** - Whitelist-based origins
- **HTTPS Enforcement** - Production SSL redirect
- **Security Headers** - CSP, X-Frame-Options, etc.

### Best Practices

1. **Never commit** `.env` files
2. **Rotate secrets** regularly
3. **Use strong passwords** (min 8 chars with mixed case, numbers)
4. **Enable 2FA** for admin accounts (future feature)
5. **Regular security audits** with `safety check`

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set strong `SECRET_KEY`
- [ ] Configure PostgreSQL (not SQLite)
- [ ] Setup Redis for caching
- [ ] Configure AWS S3 for file storage
- [ ] Setup email backend (SMTP)
- [ ] Enable HTTPS/SSL
- [ ] Configure logging
- [ ] Setup monitoring (Sentry, etc.)
- [ ] Configure Celery workers
- [ ] Setup database backups
- [ ] Configure firewall rules

### Deployment Commands

```bash
# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Start with gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 config.wsgi:application
```

## 🐛 Troubleshooting

### Common Issues

**Issue: uv command not found**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Add to PATH
export PATH="$HOME/.cargo/bin:$PATH"
```

**Issue: Database connection error**
```bash
# Check if PostgreSQL is running
docker-compose ps db
# Start if not running
docker-compose up -d db
```

**Issue: Module not found**
```bash
# Reinstall dependencies
uv pip install -e ".[dev]"
```

**Issue: Celery not processing tasks**
```bash
# Check if Redis is running
docker-compose ps redis
# Start Celery worker
celery -A config worker -l info
```

## 📖 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [uv Documentation](https://github.com/astral-sh/uv)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Implementation Plan](../IMPLEMENTATION_PLAN.md)
- [Feature Guide](../FEATURE_GUIDE.md)

## 🤝 Contributing

1. Follow PEP 8 style guide
2. Write tests for new features
3. Run `make format` before committing
4. Run `make lint` to check code quality
5. Update documentation as needed

## 📝 License

[Add your license here]

## 👥 Authors

[Your Name] - Initial work

---

**Built with ❤️ using Django, uv, and modern Python tools**
