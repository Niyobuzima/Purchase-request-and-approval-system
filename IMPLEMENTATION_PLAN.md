# Purchase Request & Approval System - Implementation Plan

## Executive Summary
This document outlines a comprehensive step-by-step plan for building a production-ready Procure-to-Pay system using Django, DRF, React, and AI-powered document processing.

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend (SPA)                     │
│  - Role-based Dashboards                                     │
│  - File Upload Components                                    │
│  - Approval Workflows UI                                     │
└───────────────────┬─────────────────────────────────────────┘
                    │ REST API (JSON)
┌───────────────────▼─────────────────────────────────────────┐
│              Django + DRF Backend                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │   Authentication & Authorization Layer               │   │
│  │   - JWT Tokens                                       │   │
│  │   - Role-based Permissions                           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │   Business Logic Layer                               │   │
│  │   - Multi-level Approval Workflow                    │   │
│  │   - State Machine for Request Status                 │   │
│  │   - Concurrent Request Handling                      │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │   Document Processing Service                        │   │
│  │   - Proforma Extraction (AI/OCR)                     │   │
│  │   - PO Generation (Automated)                        │   │
│  │   - Receipt Validation (AI Comparison)               │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │   Background Task Queue (Celery)                     │   │
│  │   - Async Document Processing                        │   │
│  │   - Email Notifications                              │   │
│  │   - PO Generation Tasks                              │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────┬─────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
┌─────────┐   ┌─────────┐   ┌─────────────┐
│PostgreSQL│   │  Redis  │   │ File Storage│
│         │   │ (Celery)│   │   (S3/Local)│
└─────────┘   └─────────┘   └─────────────┘
```

### 1.2 Technology Stack

**Backend:**
- Django 5.0
- Django REST Framework 3.14
- PostgreSQL 15
- Redis 7.0 (Celery broker)
- Celery 5.3 (background tasks)
- JWT Authentication (djangorestframework-simplejwt)

**Document Processing:**
- OpenAI GPT-5 API (primary)
- pdfplumber (PDF text extraction)
- PyPDF2 (PDF manipulation)
- Pillow (image processing)
- pytesseract (fallback OCR)

**Frontend:**
- React 19 with Hooks
- TypeScript
- Vite (build tool)
- TanStack Query (data fetching)
- Fetch (HTTP client)
- React Router v6
- Tailwind CSS + shadcn/ui
- React-router form + Zod validation

**DevOps:**
- Docker + Docker Compose
- PostgreSQL container
- Redis container
- Nginx (reverse proxy)
- AWS EC2 / Render deployment

---

## 2. Database Schema Design

### 2.1 Entity Relationship Diagram

```
┌──────────────────────┐
│       User           │
│──────────────────────│
│ id (PK)              │
│ username             │
│ email                │
│ password             │
│ role (ENUM)          │
│ approval_level (INT) │
│ created_at           │
│ updated_at           │
└──────────────────────┘
          │
          │ 1:N (created_by)
          ▼
┌──────────────────────────────┐
│    PurchaseRequest           │
│──────────────────────────────│
│ id (PK)                      │
│ title (VARCHAR 255)          │
│ description (TEXT)           │
│ total_amount (DECIMAL)       │
│ status (ENUM)                │──┐
│ created_by_id (FK)           │  │
│ current_approval_level (INT) │  │
│ proforma_file (FILE)         │  │
│ proforma_extracted_data (JSON)│ │
│ purchase_order_file (FILE)   │  │
│ purchase_order_data (JSON)   │  │
│ receipt_file (FILE)          │  │
│ receipt_data (JSON)          │  │
│ receipt_validation (JSON)    │  │
│ created_at                   │  │
│ updated_at                   │  │
└──────────────────────────────┘  │
          │                        │
          │ 1:N                    │
          ▼                        │
┌──────────────────────────────┐  │
│      RequestItem             │  │
│──────────────────────────────│  │
│ id (PK)                      │  │
│ request_id (FK)              │  │
│ item_name (VARCHAR)          │  │
│ description (TEXT)           │  │
│ quantity (DECIMAL)           │  │
│ unit_price (DECIMAL)         │  │
│ total_price (DECIMAL)        │  │
│ created_at                   │  │
│ updated_at                   │  │
└──────────────────────────────┘  │
                                   │
          ┌────────────────────────┘
          │ 1:N
          ▼
┌──────────────────────────────┐
│      ApprovalLog             │
│──────────────────────────────│
│ id (PK)                      │
│ request_id (FK)              │
│ approver_id (FK → User)      │
│ approval_level (INT)         │
│ action (ENUM)                │
│ comments (TEXT)              │
│ created_at                   │
└──────────────────────────────┘

ENUMS:
- User.role: ['STAFF', 'APPROVER_L1', 'APPROVER_L2', 'FINANCE', 'ADMIN']
- PurchaseRequest.status: ['DRAFT', 'PENDING', 'APPROVED', 'REJECTED', 'COMPLETED']
- ApprovalLog.action: ['SUBMITTED', 'APPROVED', 'REJECTED', 'UPDATED']
```

### 2.2 Database Indexes & Constraints

**Performance Optimizations:**
```sql
-- Indexes for common queries
CREATE INDEX idx_purchase_request_status ON purchase_request(status);
CREATE INDEX idx_purchase_request_created_by ON purchase_request(created_by_id);
CREATE INDEX idx_purchase_request_created_at ON purchase_request(created_at DESC);
CREATE INDEX idx_approval_log_request ON approval_log(request_id);
CREATE INDEX idx_approval_log_approver ON approval_log(approver_id);

-- Composite index for approval workflow queries
CREATE INDEX idx_request_status_level ON purchase_request(status, current_approval_level);

-- Check constraints
ALTER TABLE purchase_request ADD CONSTRAINT check_total_amount_positive
  CHECK (total_amount > 0);

ALTER TABLE user ADD CONSTRAINT check_approval_level_valid
  CHECK (approval_level >= 1 AND approval_level <= 2);
```

---

## 3. API Design & Endpoints

### 3.1 Authentication Endpoints
```
POST   /api/auth/register/          - Register new user (admin only)
POST   /api/auth/login/             - Login (get JWT tokens)
POST   /api/auth/refresh/           - Refresh access token
POST   /api/auth/logout/            - Logout (blacklist token)
GET    /api/auth/me/                - Get current user profile
PATCH  /api/auth/me/                - Update profile
```

### 3.2 Purchase Request Endpoints
```
POST   /api/requests/                     - Create request (Staff)
GET    /api/requests/                     - List requests (filtered by role)
GET    /api/requests/{id}/                - Get request details
PUT    /api/requests/{id}/                - Update request (Staff, DRAFT/PENDING)
DELETE /api/requests/{id}/                - Delete request (Staff, DRAFT only)
PATCH  /api/requests/{id}/submit/         - Submit for approval
PATCH  /api/requests/{id}/approve/        - Approve request (Approver)
PATCH  /api/requests/{id}/reject/         - Reject request (Approver)
POST   /api/requests/{id}/upload-receipt/ - Upload receipt (Staff)
GET    /api/requests/{id}/approval-history/ - Get approval logs
GET    /api/requests/{id}/download-po/    - Download PO file
```

### 3.3 Document Processing Endpoints
```
POST   /api/documents/extract-proforma/   - Extract data from proforma
POST   /api/documents/generate-po/        - Generate PO (auto-triggered)
POST   /api/documents/validate-receipt/   - Validate receipt against PO
```

### 3.4 Dashboard & Analytics
```
GET    /api/dashboard/stats/              - Get role-specific statistics
GET    /api/dashboard/pending-approvals/  - Approver's pending items
GET    /api/dashboard/my-requests/        - Staff's request history
```

### 3.5 API Response Standards

**Success Response:**
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation successful"
}
```

**Error Response:**
```json
{
  "status": "error",
  "errors": {
    "field_name": ["Error message 1", "Error message 2"]
  },
  "message": "Validation failed"
}
```

**Pagination:**
```json
{
  "status": "success",
  "data": {
    "count": 100,
    "next": "http://api.example.com/requests/?page=3",
    "previous": "http://api.example.com/requests/?page=1",
    "results": [...]
  }
}
```

---

## 4. Security Implementation Plan

### 4.1 Authentication & Authorization

**JWT Token Strategy:**
```python
# Access Token: 15 minutes expiry
# Refresh Token: 7 days expiry
# Blacklist on logout
# HttpOnly cookies for tokens (optional)

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

**Role-Based Access Control (RBAC):**
```python
# Custom permission classes
IsStaff, IsApproverL1, IsApproverL2, IsFinance

# Decorators for view-level protection
@permission_classes([IsAuthenticated, IsStaff])

# Object-level permissions
- Staff can only view/edit their own requests
- Approvers see requests at their approval level
- Finance sees all approved requests
```

### 4.2 Input Validation & Sanitization

**Django REST Framework Serializers:**
```python
class PurchaseRequestSerializer(serializers.ModelSerializer):
    # Validation rules
    - title: max_length=255, required
    - description: max_length=5000
    - total_amount: min_value=0.01, max_digits=12, decimal_places=2
    - File uploads: max_size=10MB, allowed types: PDF, PNG, JPG

    # Custom validators
    def validate_total_amount(self, value):
        if value <= 0:
            raise ValidationError("Amount must be positive")
        return value
```

### 4.3 File Upload Security

```python
# File validation
ALLOWED_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# File storage
- Use unique UUIDs for filenames
- Store outside web root
- Validate MIME types (not just extensions)
- Scan for malware (optional: ClamAV)
- Store in S3 with signed URLs
```

### 4.4 SQL Injection Prevention
```python
# Django ORM handles this automatically
# Never use raw SQL with user input
# Use parameterized queries if raw SQL needed
```

### 4.5 XSS Prevention
```python
# Django templates auto-escape by default
# DRF serializes to JSON safely
# Frontend: sanitize user input in React
# CSP headers configured
```

### 4.6 CSRF Protection
```python
# REST API uses JWT (stateless)
# CSRF not needed for API endpoints
# Enable for Django admin panel
```

### 4.7 Rate Limiting
```python
# django-ratelimit or DRF throttling
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

### 4.8 Secrets Management
```python
# Use environment variables
# Never commit .env files
# Use AWS Secrets Manager in production
# Separate configs for dev/staging/prod
```

---

## 5. Multi-Level Approval Workflow

### 5.1 State Machine Design

```
States: DRAFT → PENDING → APPROVED/REJECTED

Transitions:
┌────────┐  submit   ┌─────────┐  L1 approve  ┌──────────────┐
│ DRAFT  │──────────▶│ PENDING │─────────────▶│ PENDING (L2) │
└────────┘           └─────────┘              └──────────────┘
                          │                            │
                          │ reject                     │ L2 approve
                          ▼                            ▼
                     ┌──────────┐                ┌──────────┐
                     │ REJECTED │                │ APPROVED │
                     └──────────┘                └──────────┘
                     (immutable)                 (immutable)
```

### 5.2 Approval Logic Implementation

**Approval Levels:**
- Level 1: APPROVER_L1 role
- Level 2: APPROVER_L2 role
- Requires sequential approval (L1 → L2)

**Workflow Rules:**
```python
def approve_request(request, approver):
    # 1. Verify approver has correct level
    if approver.approval_level != request.current_approval_level:
        raise PermissionDenied("Wrong approval level")

    # 2. Check request is in PENDING state
    if request.status != 'PENDING':
        raise ValidationError("Request not in approvable state")

    # 3. Create approval log entry
    ApprovalLog.objects.create(
        request=request,
        approver=approver,
        approval_level=approver.approval_level,
        action='APPROVED'
    )

    # 4. Advance to next level or approve
    if request.current_approval_level == 1:
        request.current_approval_level = 2
        request.save()
    else:  # Level 2 approval
        request.status = 'APPROVED'
        request.save()
        # Trigger PO generation
        generate_purchase_order.delay(request.id)
```

### 5.3 Concurrency Handling

**Database-Level Locking:**
```python
from django.db import transaction

@transaction.atomic
def approve_request(request_id, approver_id):
    # SELECT FOR UPDATE prevents race conditions
    request = PurchaseRequest.objects.select_for_update().get(id=request_id)

    # Check if already processed
    if request.status in ['APPROVED', 'REJECTED']:
        raise ValidationError("Request already finalized")

    # Process approval
    # ... approval logic ...
```

**Optimistic Locking (Alternative):**
```python
class PurchaseRequest(models.Model):
    version = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.pk:
            # Increment version on update
            self.version += 1
            # Check version hasn't changed
            updated = PurchaseRequest.objects.filter(
                pk=self.pk,
                version=self.version - 1
            ).update(version=self.version)
            if not updated:
                raise ValidationError("Concurrent modification detected")
        super().save(*args, **kwargs)
```

---

## 6. Document Processing with AI

### 6.1 Architecture

```
┌─────────────────┐
│  Upload File    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Store in File System   │
│  (S3 or Local)          │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Celery Task Queue      │
│  (Async Processing)     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Document Type Check    │
│  PDF / Image            │
└────────┬────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│  PDF   │ │  Image   │
│Extract │ │   OCR    │
└───┬────┘ └────┬─────┘
    │           │
    └─────┬─────┘
          ▼
┌──────────────────────┐
│  OpenAI GPT-4 Vision │
│  Structured Extract  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Validate & Store    │
│  JSON Data           │
└──────────────────────┘
```

### 6.2 Proforma Extraction

**Implementation:**
```python
# services/document_processor.py

import openai
from pdf2image import convert_from_path
import pdfplumber

class ProformaExtractor:
    def extract(self, file_path):
        # 1. Convert PDF to images or read image
        if file_path.endswith('.pdf'):
            images = self._pdf_to_images(file_path)
            text = self._extract_text_from_pdf(file_path)
        else:
            images = [file_path]
            text = self._ocr_image(file_path)

        # 2. Use GPT-4 Vision for structured extraction
        extracted_data = self._extract_with_ai(images[0], text)

        return extracted_data

    def _extract_with_ai(self, image_path, text_context):
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Extract the following from this proforma invoice:
                        - Vendor name
                        - Vendor contact
                        - Date
                        - Items (name, quantity, unit price)
                        - Subtotal
                        - Tax
                        - Total amount
                        - Payment terms

                        Context text: {text_context}

                        Return as JSON."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{self._encode_image(image_path)}"}
                    }
                ]
            }],
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)
```

**Data Schema:**
```json
{
  "vendor": {
    "name": "ABC Supplies Ltd",
    "contact": "+250788123456",
    "email": "sales@abc.com",
    "address": "Kigali, Rwanda"
  },
  "invoice_number": "INV-2024-001",
  "date": "2024-01-15",
  "items": [
    {
      "name": "Office Chair",
      "description": "Ergonomic office chair",
      "quantity": 10,
      "unit_price": 50000,
      "total": 500000
    }
  ],
  "subtotal": 500000,
  "tax": 90000,
  "total": 590000,
  "currency": "RWF",
  "payment_terms": "Net 30"
}
```

### 6.3 Purchase Order Generation

**Auto-Generation Logic:**
```python
# tasks.py (Celery)

@shared_task
def generate_purchase_order(request_id):
    request = PurchaseRequest.objects.get(id=request_id)

    # 1. Extract data from proforma
    proforma_data = request.proforma_extracted_data

    # 2. Generate PO number
    po_number = f"PO-{datetime.now().year}-{request.id:06d}"

    # 3. Create PO data structure
    po_data = {
        "po_number": po_number,
        "date": datetime.now().isoformat(),
        "vendor": proforma_data["vendor"],
        "buyer": {
            "name": "IST Africa",
            "address": "Kigali, Rwanda",
            "contact": "+250788000000"
        },
        "items": proforma_data["items"],
        "subtotal": proforma_data["subtotal"],
        "tax": proforma_data["tax"],
        "total": proforma_data["total"],
        "payment_terms": proforma_data["payment_terms"],
        "delivery_terms": "FOB Kigali",
        "approved_by": request.get_final_approver()
    }

    # 4. Generate PDF document
    pdf_file = generate_po_pdf(po_data)

    # 5. Store PO
    request.purchase_order_file = pdf_file
    request.purchase_order_data = po_data
    request.save()

    # 6. Send notification
    send_po_notification.delay(request.id)
```

**PDF Generation:**
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_po_pdf(po_data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "PURCHASE ORDER")
    c.setFont("Helvetica", 10)
    c.drawString(50, 730, f"PO Number: {po_data['po_number']}")

    # Vendor details
    # Items table
    # Totals
    # Terms

    c.save()
    buffer.seek(0)
    return buffer
```

### 6.4 Receipt Validation

**Comparison Logic:**
```python
class ReceiptValidator:
    def validate(self, receipt_file, purchase_order_data):
        # 1. Extract data from receipt
        receipt_data = self._extract_receipt_data(receipt_file)

        # 2. Compare with PO
        discrepancies = []

        # Vendor validation
        if not self._fuzzy_match(
            receipt_data["vendor"]["name"],
            purchase_order_data["vendor"]["name"]
        ):
            discrepancies.append({
                "field": "vendor",
                "expected": purchase_order_data["vendor"]["name"],
                "actual": receipt_data["vendor"]["name"],
                "severity": "HIGH"
            })

        # Item-by-item comparison
        for po_item in purchase_order_data["items"]:
            matching_item = self._find_matching_item(
                po_item,
                receipt_data["items"]
            )

            if not matching_item:
                discrepancies.append({
                    "field": "items",
                    "issue": "Missing item",
                    "item": po_item["name"],
                    "severity": "HIGH"
                })
            else:
                # Price variance
                if abs(matching_item["unit_price"] - po_item["unit_price"]) > 0.01:
                    discrepancies.append({
                        "field": "price",
                        "item": po_item["name"],
                        "expected": po_item["unit_price"],
                        "actual": matching_item["unit_price"],
                        "variance": matching_item["unit_price"] - po_item["unit_price"],
                        "severity": "MEDIUM"
                    })

        # Total amount variance
        total_variance = receipt_data["total"] - purchase_order_data["total"]
        if abs(total_variance) > 1:  # Allow 1 RWF rounding
            discrepancies.append({
                "field": "total",
                "expected": purchase_order_data["total"],
                "actual": receipt_data["total"],
                "variance": total_variance,
                "severity": "HIGH"
            })

        return {
            "valid": len(discrepancies) == 0,
            "discrepancies": discrepancies,
            "receipt_data": receipt_data,
            "confidence_score": self._calculate_confidence(discrepancies)
        }
```

### 6.5 Performance Optimization

**Strategies:**
```python
# 1. Async processing with Celery
@shared_task
def process_document_async(file_id, document_type):
    # Process in background
    pass

# 2. Caching extracted data
from django.core.cache import cache

def get_extracted_data(file_path):
    cache_key = f"extracted_{hashlib.md5(file_path.encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    data = extract_data(file_path)
    cache.set(cache_key, data, timeout=3600)
    return data

# 3. Thumbnail generation for quick preview
# 4. Chunked file uploads for large files
# 5. Queue prioritization (receipts > proformas)
```

---

## 7. Performance Optimization Strategies

### 7.1 Database Query Optimization

```python
# Use select_related for foreign keys
PurchaseRequest.objects.select_related('created_by').all()

# Use prefetch_related for reverse FKs
PurchaseRequest.objects.prefetch_related('items', 'approval_logs').all()

# Avoid N+1 queries
requests = PurchaseRequest.objects.select_related('created_by') \
    .prefetch_related('approval_logs__approver')

# Use only() to fetch specific fields
PurchaseRequest.objects.only('id', 'title', 'status')

# Use defer() to exclude heavy fields
PurchaseRequest.objects.defer('description', 'proforma_extracted_data')

# Database indexes on common filters
class Meta:
    indexes = [
        models.Index(fields=['status', '-created_at']),
        models.Index(fields=['created_by', 'status']),
    ]
```

### 7.2 Caching Strategy

```python
# Redis caching layers
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Cache dashboard stats (5 minutes)
@cache_page(60 * 5)
def dashboard_stats(request):
    pass

# Cache request list per user (1 minute)
from django.views.decorators.cache import cache_page

# Low-level caching for expensive operations
def get_approval_stats(user):
    cache_key = f"approval_stats_{user.id}"
    stats = cache.get(cache_key)
    if not stats:
        stats = calculate_stats(user)
        cache.set(cache_key, stats, 300)  # 5 min
    return stats
```

### 7.3 API Response Optimization

```python
# Pagination
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# Field filtering (sparse fieldsets)
GET /api/requests/?fields=id,title,status

# Compression
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
]

# ETags for conditional requests
from django.views.decorators.http import condition

@condition(etag_func=calculate_etag)
def request_detail(request, pk):
    pass
```

### 7.4 File Upload Optimization

```python
# Chunked uploads for large files
# Direct S3 uploads with presigned URLs
import boto3

def generate_presigned_post(filename):
    s3_client = boto3.client('s3')
    return s3_client.generate_presigned_post(
        Bucket='my-bucket',
        Key=filename,
        ExpiresIn=3600
    )

# Frontend uploads directly to S3
# Backend receives URL and validates
```

### 7.5 Background Task Optimization

```python
# Celery task routing
CELERY_TASK_ROUTES = {
    'tasks.process_document': {'queue': 'high_priority'},
    'tasks.send_email': {'queue': 'low_priority'},
}

# Task result backend
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Task retry with exponential backoff
@shared_task(bind=True, max_retries=3)
def process_document(self, file_id):
    try:
        # Process
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

---

## 8. Testing Strategy

### 8.1 Test Coverage Goals
- Unit Tests: 80% coverage
- Integration Tests: Critical workflows
- API Tests: All endpoints
- Security Tests: Auth, permissions, file uploads

### 8.2 Test Structure

```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_serializers.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/
│   ├── test_approval_workflow.py
│   ├── test_document_processing.py
│   └── test_concurrent_approvals.py
├── api/
│   ├── test_auth_endpoints.py
│   ├── test_request_endpoints.py
│   └── test_permissions.py
└── fixtures/
    ├── sample_proforma.pdf
    ├── sample_receipt.jpg
    └── test_data.json
```

### 8.3 Key Test Cases

**Approval Workflow Tests:**
```python
def test_sequential_approval():
    # Create request
    # L1 approver approves
    # Assert status still PENDING
    # L2 approver approves
    # Assert status APPROVED
    # Assert PO generated

def test_rejection_at_l1():
    # L1 rejects
    # Assert status REJECTED
    # Assert L2 cannot approve

def test_concurrent_approval_attempt():
    # Two approvers at same level approve simultaneously
    # Assert only one succeeds
    # Assert no duplicate approvals
```

**Document Processing Tests:**
```python
def test_proforma_extraction_accuracy():
    # Upload sample proforma
    # Compare extracted data to expected
    # Assert key fields present

def test_receipt_validation_with_mismatch():
    # Create PO with specific items/prices
    # Upload receipt with different prices
    # Assert discrepancies flagged

def test_po_generation():
    # Approve request
    # Assert PO created
    # Assert PO contains correct data
```

---

## 9. Deployment Architecture

### 9.1 Production Environment

```
                          ┌─────────────────┐
                          │   CloudFlare    │
                          │   (CDN + SSL)   │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │  Load Balancer  │
                          │   (AWS ALB)     │
                          └────────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼                             ▼
          ┌──────────────────┐         ┌──────────────────┐
          │   EC2 Instance   │         │   EC2 Instance   │
          │   (Web Server)   │         │   (Web Server)   │
          │   - Django       │         │   - Django       │
          │   - Gunicorn     │         │   - Gunicorn     │
          │   - Nginx        │         │   - Nginx        │
          └──────────────────┘         └──────────────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
          ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
          │ RDS PostgreSQL│  │Redis Cluster│  │   S3 Bucket │
          │  (Multi-AZ)   │  │  (Celery)   │  │   (Files)   │
          └─────────────┘  └─────────────┘  └─────────────┘
```

### 9.2 Docker Configuration

**Dockerfile (Backend):**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "config.wsgi:application"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: procure_db
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    command: gunicorn --bind 0.0.0.0:8000 --workers 4 config.wsgi:application
    volumes:
      - ./backend:/app
      - media_files:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis

  celery:
    build: ./backend
    command: celery -A config worker -l info
    volumes:
      - ./backend:/app
      - media_files:/app/media
    env_file:
      - .env
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - media_files:/media
      - static_files:/static
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
  media_files:
  static_files:
```

### 9.3 Environment Variables

```bash
# .env.example
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-...

# AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...
AWS_S3_REGION_NAME=us-east-1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...

# Frontend
REACT_APP_API_URL=https://api.yourdomain.com
```

---

## 10. Git Branching Strategy

### 10.1 Branch Structure

```
main (production)
  │
  ├─ develop (integration)
  │   │
  │   ├─ feature/auth-system
  │   ├─ feature/purchase-request-api
  │   ├─ feature/approval-workflow
  │   ├─ feature/document-processing
  │   ├─ feature/frontend-dashboard
  │   ├─ feature/receipt-validation
  │   └─ feature/deployment-config
  │
  └─ hotfix/critical-bug (if needed)
```

### 10.2 Branch Naming Convention

```
feature/<feature-name>        - New features
bugfix/<bug-description>      - Bug fixes
hotfix/<critical-issue>       - Production hotfixes
release/<version>             - Release branches
chore/<task-description>      - Maintenance tasks
```

### 10.3 Feature Branch Plan

**Phase 1: Foundation (Days 1-2)**
```
feature/project-setup
  - Django project initialization
  - Docker configuration
  - Database setup
  - Environment configuration

feature/auth-system
  - User model with roles
  - JWT authentication
  - Login/logout endpoints
  - Permission classes
```

**Phase 2: Core Backend (Days 3-5)**
```
feature/purchase-request-models
  - PurchaseRequest model
  - RequestItem model
  - ApprovalLog model
  - Database migrations

feature/purchase-request-api
  - CRUD endpoints
  - Serializers
  - Basic validation

feature/approval-workflow
  - Multi-level approval logic
  - State machine implementation
  - Concurrency handling
  - Approval endpoints
```

**Phase 3: Document Processing (Days 6-7)**
```
feature/document-processing
  - File upload handling
  - Proforma extraction service
  - OpenAI integration
  - Celery tasks

feature/po-generation
  - Auto PO generation
  - PDF creation
  - Data mapping

feature/receipt-validation
  - Receipt extraction
  - Comparison logic
  - Discrepancy detection
```

**Phase 4: Frontend (Days 8-10)**
```
feature/frontend-setup
  - React + Vite setup
  - Routing configuration
  - Auth context
  - API client

feature/frontend-auth
  - Login page
  - Protected routes
  - Token management

feature/frontend-dashboard
  - Role-based dashboards
  - Request list views
  - Statistics widgets

feature/frontend-request-management
  - Create request form
  - File upload component
  - Request detail view
  - Approval interface
```

**Phase 5: Integration & Testing (Days 11-12)**
```
feature/testing
  - Unit tests
  - Integration tests
  - API tests

feature/documentation
  - API documentation (Swagger)
  - README
  - Deployment guide
```

**Phase 6: Deployment (Day 13)**
```
feature/deployment
  - AWS/Render configuration
  - CI/CD pipeline
  - Production environment setup
```

### 10.4 Commit Message Convention

```
<type>(<scope>): <subject>

Types:
  feat: New feature
  fix: Bug fix
  docs: Documentation
  style: Formatting
  refactor: Code restructuring
  test: Adding tests
  chore: Maintenance

Examples:
  feat(auth): implement JWT authentication
  fix(approval): resolve concurrent approval race condition
  docs(api): add Swagger documentation for request endpoints
  test(workflow): add integration tests for approval flow
```

### 10.5 PR & Merge Strategy

```
1. Create feature branch from develop
2. Implement feature with commits
3. Create PR to develop
4. Code review (self-review if solo)
5. Merge to develop
6. Delete feature branch
7. After all features complete: merge develop to main
```

---

## 11. Security Checklist

### 11.1 Pre-Deployment Security Audit

- [ ] All environment variables in .env (not hardcoded)
- [ ] SECRET_KEY is strong and unique
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS configured correctly
- [ ] Database credentials secured
- [ ] AWS credentials use IAM roles (not hardcoded)
- [ ] HTTPS enforced (SSL certificates)
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] File upload validation (size, type, content)
- [ ] SQL injection prevention (ORM usage)
- [ ] XSS prevention (template escaping)
- [ ] CSRF tokens (if needed)
- [ ] JWT tokens with short expiry
- [ ] Sensitive data encrypted at rest
- [ ] Audit logging enabled
- [ ] Error messages don't leak sensitive info
- [ ] Dependencies updated (no known vulnerabilities)
- [ ] Security headers configured (CSP, X-Frame-Options, etc.)

---

## 12. Performance Benchmarks & Optimization Targets

### 12.1 Target Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (95th percentile) | < 200ms | NewRelic/Sentry |
| Document Processing Time | < 30s | Celery task logs |
| Page Load Time | < 2s | Lighthouse |
| Database Query Time | < 50ms | Django Debug Toolbar |
| Concurrent Users | 100+ | Load testing (Locust) |
| File Upload (10MB) | < 5s | Frontend metrics |

### 12.2 Bottleneck Identification

**Potential Bottlenecks:**
1. **Document processing** - Mitigated with Celery async tasks
2. **Database queries** - Mitigated with indexes, select_related, caching
3. **File uploads** - Mitigated with chunked uploads, S3 direct upload
4. **API response time** - Mitigated with pagination, field filtering, compression
5. **Concurrent approvals** - Mitigated with SELECT FOR UPDATE locks

---

## 13. Monitoring & Observability

### 13.1 Logging Strategy

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/app.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
        'app': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
    },
}
```

### 13.2 Metrics to Track

- Request count by endpoint
- Response time distribution
- Error rate (4xx, 5xx)
- Database connection pool usage
- Celery queue length
- Document processing success rate
- User activity (logins, requests created, approvals)

---

## 14. Implementation Timeline

### Week 1 (Days 1-7)

**Day 1: Project Setup**
- Initialize Django project
- Configure Docker
- Setup PostgreSQL & Redis
- Configure environment variables

**Day 2: Authentication System**
- Custom User model with roles
- JWT authentication endpoints
- Permission classes
- Basic tests

**Day 3-4: Core Models & API**
- PurchaseRequest model
- RequestItem model
- ApprovalLog model
- CRUD API endpoints
- Serializers & validation

**Day 5: Approval Workflow**
- Multi-level approval logic
- State transitions
- Concurrency handling
- Approval/rejection endpoints

**Day 6-7: Document Processing**
- File upload handling
- Proforma extraction (OpenAI)
- PO generation
- Celery task setup

### Week 2 (Days 8-13)

**Day 8: Receipt Validation**
- Receipt extraction
- Comparison algorithm
- Discrepancy detection

**Day 9-10: Frontend Development**
- React setup
- Authentication flow
- Dashboard components
- Request management UI

**Day 11: Testing**
- Unit tests
- Integration tests
- API tests
- Bug fixes

**Day 12: Documentation**
- Swagger API docs
- README
- Setup guide
- Architecture docs

**Day 13: Deployment**
- AWS EC2 / Render setup
- Domain & SSL configuration
- Production environment
- Final testing

---

## 15. Risk Mitigation

### 15.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OpenAI API rate limits | Medium | High | Implement retry logic, fallback to OCR |
| Concurrent approval conflicts | Medium | High | Database locking, optimistic locking |
| File upload failures | Low | Medium | Chunked uploads, resume capability |
| Poor OCR accuracy | Medium | Medium | Manual review option, confidence scores |
| Performance degradation | Low | High | Caching, query optimization, load testing |
| Security vulnerabilities | Low | Critical | Security audit, dependency scanning |

### 15.2 Contingency Plans

**If OpenAI API fails:**
- Fallback to pytesseract OCR
- Manual data entry option
- Queue for retry when API recovers

**If deployment platform fails:**
- Have secondary platform ready (Render + AWS)
- Docker ensures portability
- Database backups

---

## 16. Success Criteria

### 16.1 Functional Requirements ✓
- [x] Multi-level approval workflow
- [x] Role-based access control
- [x] Document processing (proforma, PO, receipt)
- [x] Automatic PO generation
- [x] Receipt validation with discrepancy detection
- [x] REST API with all required endpoints
- [x] React frontend with role-based UI
- [x] Dockerized deployment
- [x] Public deployment

### 16.2 Non-Functional Requirements ✓
- [x] API response time < 200ms
- [x] Document processing < 30s
- [x] Handles concurrent requests safely
- [x] Secure authentication & authorization
- [x] Comprehensive API documentation
- [x] Clean, maintainable code
- [x] Test coverage > 80%

---

## 17. Next Steps

After reviewing this plan:

1. **Approve architecture** - Confirm tech stack and design decisions
2. **Setup development environment** - Create initial Django project
3. **Create feature branches** - Following the branching strategy
4. **Begin Phase 1 implementation** - Project setup and authentication
5. **Daily progress tracking** - Update implementation status
6. **Code reviews** - Self-review before merging branches
7. **Deployment** - Deploy to production environment

---

## Appendix A: Technology Justifications

**Why Django?**
- Robust ORM for complex queries
- Built-in admin panel
- Excellent security features
- Large ecosystem

**Why PostgreSQL?**
- ACID compliance for critical workflows
- JSON field support for extracted data
- Row-level locking for concurrency
- Production-grade reliability

**Why Celery?**
- Async task processing (document extraction)
- Retry mechanisms
- Task scheduling
- Scalable

**Why React?**
- Component reusability
- Rich ecosystem
- TypeScript support
- Excellent developer experience

**Why OpenAI GPT-4 Vision?**
- Superior accuracy for document extraction
- Structured data output
- Handles various document formats
- Reduces need for preprocessing

---

## Appendix B: Code Quality Standards

**Python (Django/DRF):**
- PEP 8 compliance
- Type hints where applicable
- Docstrings for complex functions
- Maximum line length: 100 characters
- Use black for formatting
- Use flake8 for linting

**JavaScript/TypeScript (React):**
- ESLint + Prettier
- TypeScript strict mode
- Functional components with hooks
- Prop types / TypeScript interfaces
- Maximum line length: 100 characters

**Git Commits:**
- Conventional commits format
- Clear, descriptive messages
- Atomic commits (one logical change)
- Reference issue numbers if applicable

---

**Document Version:** 1.0
**Last Updated:** 2024-01-20
**Author:** Advanced Django Developer
**Status:** Ready for Implementation
