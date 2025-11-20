#!/usr/bin/env python
"""
Verification script to check if the backend setup is correct
"""
import os
import sys
from pathlib import Path

def check_uv_installed():
    """Check if uv is installed"""
    import subprocess
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uv is installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    print("❌ uv is NOT installed")
    print("   Install: curl -LsSf https://astral.sh/uv/install.sh | sh")
    return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version >= (3, 11):
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor}.{version.micro} is too old")
        print("   Required: Python 3.11+")
        return False

def check_files_exist():
    """Check if required files exist"""
    required_files = [
        'pyproject.toml',
        'manage.py',
        'config/settings/base.py',
        'config/settings/development.py',
        'config/settings/production.py',
        'core/permissions.py',
        'core/exceptions.py',
        'core/utils.py',
        'Dockerfile',
        'Dockerfile.prod',
        'Makefile',
        'setup.sh',
        'setup.ps1',
        '../docker-compose.yml',
        '../.env.example',
    ]

    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} NOT FOUND")
            all_exist = False

    return all_exist

def check_directories_exist():
    """Check if required directories exist"""
    required_dirs = [
        'apps/accounts',
        'apps/purchase_requests',
        'apps/approvals',
        'apps/documents',
        'config/settings',
        'core',
        'media',
        'static',
        'templates',
        'logs',
    ]

    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ NOT FOUND")
            all_exist = False

    return all_exist

def check_env_file():
    """Check if .env file exists"""
    env_path = Path('../.env')
    if env_path.exists():
        print("✅ .env file exists")
        return True
    else:
        print("⚠️  .env file NOT FOUND")
        print("   Copy from .env.example and configure")
        return False

def check_dependencies():
    """Check if key dependencies can be imported"""
    dependencies = [
        ('django', 'Django'),
        ('rest_framework', 'Django REST Framework'),
        ('rest_framework_simplejwt', 'Simple JWT'),
        ('celery', 'Celery'),
        ('redis', 'Redis'),
    ]

    all_imported = True
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} NOT INSTALLED")
            all_imported = False

    return all_imported

def main():
    """Run all checks"""
    print("=" * 60)
    print("🔍 Purchase Request & Approval System - Setup Verification")
    print("=" * 60)
    print()

    checks = [
        ("Python Version", check_python_version),
        ("uv Installation", check_uv_installed),
        ("Required Files", check_files_exist),
        ("Required Directories", check_directories_exist),
        ("Environment Configuration", check_env_file),
        ("Python Dependencies", check_dependencies),
    ]

    results = []
    for check_name, check_func in checks:
        print(f"\n📋 Checking {check_name}...")
        print("-" * 60)
        result = check_func()
        results.append((check_name, result))

    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check_name}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 All checks passed! Your setup is ready.")
        print("\nNext steps:")
        print("  1. docker-compose up -d db redis")
        print("  2. python manage.py migrate")
        print("  3. python manage.py createsuperuser")
        print("  4. python manage.py runserver")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nRun the setup script:")
        print("  Linux/macOS: ./setup.sh")
        print("  Windows: .\\setup.ps1")
        return 1

if __name__ == '__main__':
    sys.exit(main())
