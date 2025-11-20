# Purchase Request & Approval System - Feature Implementation Guide

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Core Features Explained](#core-features-explained)
3. [Technical Implementation Details](#technical-implementation-details)
4. [User Workflows](#user-workflows)
5. [API Reference](#api-reference)
6. [Frontend Architecture](#frontend-architecture)
7. [Database Design](#database-design)
8. [Security Features](#security-features)
9. [Performance Optimizations](#performance-optimizations)
10. [Troubleshooting Guide](#troubleshooting-guide)

---

## 1. System Overview

### What is This System?

This is a **Procure-to-Pay (P2P) system** that automates the purchase request and approval process. It handles the entire workflow from when an employee requests to buy something, through multiple levels of management approval, to finance processing and receipt validation.

### Key Capabilities

1. **Purchase Request Management** - Staff can create, submit, and track purchase requests
2. **Multi-Level Approval Workflow** - Requests go through Level 1 and Level 2 approvers
3. **AI-Powered Document Processing** - Automatically extracts data from invoices and receipts
4. **Automatic PO Generation** - Creates purchase orders when requests are approved
5. **Receipt Validation** - Compares receipts against purchase orders to detect discrepancies
6. **Role-Based Access** - Different users see different features based on their role

### User Roles

| Role | Description | Capabilities |
|------|-------------|--------------|
| **Staff** | Regular employees | Create requests, upload documents, view own requests |
| **Approver L1** | First-level managers | Approve/reject requests at level 1 |
| **Approver L2** | Senior managers | Approve/reject requests at level 2 (final approval) |
| **Finance** | Finance team | View all approved requests, access POs, review receipts |
| **Admin** | System administrators | Full access, user management |

---

## 2. Core Features Explained

### Feature 1: Purchase Request Creation

**What it does:**
Allows staff to create a purchase request by entering details and uploading a proforma invoice (quotation).

**How it works:**
```
User fills form → Uploads proforma → AI extracts data → Request saved as DRAFT
```

**Key Components:**
- **Form fields**: Title, description, items, quantities, prices
- **File upload**: Proforma invoice (PDF/Image)
- **AI extraction**: Automatically reads vendor, items, prices from proforma
- **Validation**: Ensures all required fields are present

**Example Use Case:**
```
Sarah (Staff) needs to buy 10 office chairs.

1. She creates a new purchase request
2. Fills in: "Office Chairs Purchase"
3. Uploads the quotation PDF from the supplier
4. AI extracts:
   - Vendor: "Office Supplies Ltd"
   - Items: "Ergonomic Chair x10"
   - Total: $5,000
5. She reviews and submits the request
6. Request status → PENDING
```

**Technical Details:**
- **Endpoint**: `POST /api/requests/`
- **Files stored**: S3 or local filesystem
- **Processing**: Celery task extracts data asynchronously
- **Status**: Starts as DRAFT, becomes PENDING on submit

---

### Feature 2: Multi-Level Approval Workflow

**What it does:**
Ensures purchase requests are reviewed and approved by multiple levels of management before processing.

**How it works:**
```
DRAFT → Staff submits → PENDING (L1) → L1 approves → PENDING (L2) → L2 approves → APPROVED
                                ↓                                ↓
                            REJECTED                         REJECTED
```

**Approval Rules:**
1. **Sequential approval required** - L1 must approve before L2 can see the request
2. **Any rejection is final** - If L1 or L2 rejects, status becomes REJECTED (immutable)
3. **All approvals needed** - Both L1 and L2 must approve for final APPROVED status
4. **No changes after approval** - Once APPROVED or REJECTED, status cannot change

**Concurrency Protection:**
- Database locks prevent two approvers from acting simultaneously
- Version checking ensures no race conditions
- Audit trail logs every approval action

**Example Use Case:**
```
Sarah's $5,000 chair request:

Day 1, 10:00 AM:
  - Sarah submits request
  - Status: PENDING (awaiting L1)
  - Email sent to L1 approvers

Day 1, 2:00 PM:
  - John (L1 Manager) reviews request
  - John approves
  - Status: PENDING (awaiting L2)
  - Email sent to L2 approvers

Day 2, 9:00 AM:
  - Mary (L2 Director) reviews request
  - Mary approves
  - Status: APPROVED
  - Purchase Order auto-generated
  - Email sent to Sarah and Finance
```

**Technical Details:**
- **State machine**: Enforces valid state transitions
- **Locking**: `SELECT FOR UPDATE` prevents concurrent modifications
- **Audit log**: Every action recorded with timestamp and user
- **Endpoints**: `PATCH /api/requests/{id}/approve/` and `PATCH /api/requests/{id}/reject/`

---

### Feature 3: AI-Powered Document Processing

**What it does:**
Automatically reads and extracts structured data from documents (invoices, receipts) using AI.

**Technology Stack:**
- **Primary**: OpenAI GPT-4 Vision API
- **Fallback**: pytesseract OCR
- **PDF handling**: pdfplumber, PyPDF2
- **Image processing**: Pillow

**How it works:**

#### A. Proforma Invoice Extraction
```
1. User uploads PDF/image
2. System converts PDF to images
3. GPT-4 Vision analyzes the document
4. AI extracts structured data:
   - Vendor details
   - Item descriptions
   - Quantities
   - Prices
   - Totals
   - Payment terms
5. Data stored as JSON in database
```

**Example Extraction:**
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
      "description": "Ergonomic office chair with lumbar support",
      "quantity": 10,
      "unit_price": 500.00,
      "total": 5000.00
    }
  ],
  "subtotal": 5000.00,
  "tax": 900.00,
  "total": 5900.00,
  "currency": "RWF",
  "payment_terms": "Net 30"
}
```

#### B. Automatic PO Generation
```
1. Request gets final approval (L2)
2. Celery task triggered automatically
3. System extracts data from proforma
4. Generates PO number: PO-YYYY-######
5. Creates PDF purchase order
6. Stores PO file and data
7. Sends notifications
```

**PO Contents:**
- Company details (buyer)
- Vendor details (from proforma)
- PO number and date
- Itemized list with quantities and prices
- Totals and tax
- Payment terms
- Delivery terms
- Approval signatures

#### C. Receipt Validation
```
1. Staff uploads receipt after purchase
2. AI extracts data from receipt
3. System compares with original PO:
   - Vendor name match
   - Item names match
   - Quantities match
   - Prices match (within tolerance)
   - Total amount match
4. Flags discrepancies if found
5. Returns validation report
```

**Discrepancy Detection:**
```json
{
  "valid": false,
  "discrepancies": [
    {
      "field": "price",
      "item": "Office Chair",
      "expected": 500.00,
      "actual": 550.00,
      "variance": 50.00,
      "severity": "MEDIUM"
    },
    {
      "field": "total",
      "expected": 5900.00,
      "actual": 6400.00,
      "variance": 500.00,
      "severity": "HIGH"
    }
  ],
  "confidence_score": 0.85
}
```

**Technical Details:**
- **Async processing**: Celery handles time-consuming extraction
- **Retry logic**: Auto-retry on API failures
- **Fallback**: If OpenAI fails, uses OCR
- **Caching**: Extracted data cached for 1 hour
- **File validation**: Size limits, type checking, malware scanning

---

### Feature 4: Role-Based Dashboards

**What it does:**
Each user sees a customized dashboard based on their role with relevant information and actions.

#### Staff Dashboard
**Widgets:**
- My Requests (all statuses)
- Pending Requests (awaiting approval)
- Approved Requests (ready to purchase)
- Rejected Requests (with reasons)
- Quick Create Request button

**Actions:**
- Create new request
- View request details
- Edit pending requests
- Upload receipts
- Track approval progress

#### Approver Dashboard (L1/L2)
**Widgets:**
- Pending Approvals (requires action)
- Approved by Me (history)
- Rejected by Me (history)
- Statistics (total approved, rejected, pending)

**Actions:**
- Review request details
- View proforma documents
- Approve requests
- Reject with comments
- View approval history

#### Finance Dashboard
**Widgets:**
- All Approved Requests
- Pending POs
- Completed Purchases (with receipts)
- Budget tracking
- Vendor spending analytics

**Actions:**
- View all purchase orders
- Download PO PDFs
- Review receipts
- Validate receipts
- Export reports

**Technical Details:**
- **API**: `GET /api/dashboard/stats/` returns role-specific data
- **Filtering**: Requests filtered by role automatically
- **Real-time updates**: WebSocket or polling for live updates
- **Caching**: Dashboard stats cached for 5 minutes

---

### Feature 5: File Management System

**What it does:**
Securely handles file uploads, storage, and retrieval for documents.

**File Types:**
- Proforma invoices (PDF, PNG, JPG)
- Purchase orders (PDF, generated)
- Receipts (PDF, PNG, JPG)

**Security Measures:**
1. **File validation**:
   - Extension checking
   - MIME type verification
   - File size limits (10MB max)
   - Content scanning

2. **Storage security**:
   - Unique UUID filenames (prevents overwrites)
   - Stored outside web root
   - Access control (owner/authorized only)
   - S3 with signed URLs in production

3. **Download protection**:
   - Authentication required
   - Authorization checks (can this user access this file?)
   - Temporary signed URLs (expire after 1 hour)
   - Audit logging

**Example Flow:**
```
1. User selects file in frontend
2. Frontend validates size/type
3. POST to /api/requests/{id}/upload-proforma/
4. Backend validates file
5. Generate UUID filename: abc123-proforma.pdf
6. Store in S3 bucket or /media/proforma/
7. Save file reference in database
8. Return success with file URL
9. Trigger async extraction task
```

**Technical Details:**
- **Storage**: Local filesystem (dev), AWS S3 (production)
- **Chunked uploads**: For large files (>5MB)
- **Direct S3 uploads**: Frontend uploads directly to S3 with presigned URL
- **CDN**: CloudFront for fast delivery

---

### Feature 6: Notification System

**What it does:**
Automatically sends email notifications for important events.

**Notification Triggers:**

| Event | Recipients | Content |
|-------|-----------|---------|
| Request submitted | L1 approvers | "New request awaiting your approval" |
| L1 approved | L2 approvers, Staff (creator) | "Request approved by L1, awaiting L2" |
| L2 approved (final) | Staff, Finance | "Request approved, PO generated" |
| Request rejected | Staff (creator) | "Request rejected" with reason |
| Receipt uploaded | Finance | "Receipt submitted for validation" |
| Receipt discrepancy | Staff, Finance | "Receipt validation failed" |

**Email Template Example:**
```
Subject: Purchase Request #123 Approved

Hi Sarah,

Your purchase request "Office Chairs Purchase" has been approved!

PO Number: PO-2024-000123
Total Amount: $5,900
Approved By: Mary Johnson (Level 2)

You can now proceed with the purchase. Please upload the receipt after completion.

View Request: https://app.example.com/requests/123

---
IST Africa Procurement System
```

**Technical Details:**
- **Celery tasks**: Async email sending
- **Templates**: Django email templates
- **Provider**: SMTP (Gmail, SendGrid, AWS SES)
- **Retry**: Auto-retry on failure (3 attempts)
- **Logging**: All emails logged for audit

---

## 3. Technical Implementation Details

### Backend Architecture

**Django Project Structure:**
```
backend/
├── config/                   # Project configuration
│   ├── settings/
│   │   ├── base.py          # Common settings
│   │   ├── development.py   # Dev settings
│   │   └── production.py    # Prod settings
│   ├── urls.py              # Root URL config
│   ├── wsgi.py              # WSGI application
│   └── asgi.py              # ASGI application
├── apps/
│   ├── accounts/            # User authentication
│   │   ├── models.py        # Custom User model
│   │   ├── serializers.py   # Auth serializers
│   │   ├── views.py         # Auth endpoints
│   │   ├── permissions.py   # Custom permissions
│   │   └── tests/
│   ├── requests/            # Purchase requests
│   │   ├── models.py        # PurchaseRequest, RequestItem
│   │   ├── serializers.py   # Request serializers
│   │   ├── views.py         # Request endpoints
│   │   ├── permissions.py   # Request permissions
│   │   ├── services.py      # Business logic
│   │   ├── tasks.py         # Celery tasks
│   │   └── tests/
│   ├── approvals/           # Approval workflow
│   │   ├── models.py        # ApprovalLog
│   │   ├── services.py      # Approval logic
│   │   ├── views.py         # Approval endpoints
│   │   └── tests/
│   └── documents/           # Document processing
│       ├── services/
│       │   ├── extractor.py # Proforma extraction
│       │   ├── po_generator.py # PO generation
│       │   └── validator.py # Receipt validation
│       ├── tasks.py         # Document processing tasks
│       └── tests/
├── core/                    # Shared utilities
│   ├── exceptions.py        # Custom exceptions
│   ├── mixins.py            # Reusable mixins
│   └── utils.py             # Helper functions
├── media/                   # Uploaded files (dev)
├── static/                  # Static files
├── templates/               # Email templates
├── manage.py
└── requirements.txt
```

**Key Django Settings:**
```python
# settings/base.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_yasg',  # Swagger
    'django_filters',

    # Local apps
    'apps.accounts',
    'apps.requests',
    'apps.approvals',
    'apps.documents',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Kigali'
```

---

### Frontend Architecture

**React Project Structure:**
```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── assets/              # Images, fonts, etc.
│   ├── components/          # Reusable components
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── FileUpload.tsx
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   └── requests/
│   │       ├── RequestList.tsx
│   │       ├── RequestCard.tsx
│   │       └── RequestForm.tsx
│   ├── pages/               # Page components
│   │   ├── auth/
│   │   │   ├── Login.tsx
│   │   │   └── Register.tsx
│   │   ├── dashboard/
│   │   │   ├── StaffDashboard.tsx
│   │   │   ├── ApproverDashboard.tsx
│   │   │   └── FinanceDashboard.tsx
│   │   └── requests/
│   │       ├── CreateRequest.tsx
│   │       ├── RequestDetail.tsx
│   │       └── RequestsList.tsx
│   ├── services/            # API client
│   │   ├── api.ts           # Axios instance
│   │   ├── auth.ts          # Auth API calls
│   │   ├── requests.ts      # Request API calls
│   │   └── documents.ts     # Document API calls
│   ├── hooks/               # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useRequests.ts
│   │   └── useFileUpload.ts
│   ├── context/             # React Context
│   │   └── AuthContext.tsx
│   ├── types/               # TypeScript types
│   │   ├── user.ts
│   │   ├── request.ts
│   │   └── document.ts
│   ├── utils/               # Helper functions
│   │   ├── formatters.ts
│   │   └── validators.ts
│   ├── App.tsx              # Root component
│   ├── main.tsx             # Entry point
│   └── router.tsx           # React Router config
├── package.json
├── tsconfig.json
└── vite.config.ts
```

**Key Frontend Technologies:**
- **React 18**: UI library
- **TypeScript**: Type safety
- **Vite**: Build tool (fast!)
- **React Router v6**: Routing
- **TanStack Query**: Data fetching & caching
- **Axios**: HTTP client
- **Tailwind CSS**: Styling
- **shadcn/ui**: UI components
- **React Hook Form**: Form handling
- **Zod**: Validation

**Example Component:**
```typescript
// components/requests/RequestCard.tsx

import { Request } from '@/types/request';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface RequestCardProps {
  request: Request;
  onView: (id: string) => void;
}

export function RequestCard({ request, onView }: RequestCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED': return 'bg-green-500';
      case 'REJECTED': return 'bg-red-500';
      case 'PENDING': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="border rounded-lg p-4 hover:shadow-md transition">
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-lg">{request.title}</h3>
        <Badge className={getStatusColor(request.status)}>
          {request.status}
        </Badge>
      </div>

      <p className="text-gray-600 text-sm mb-4">
        {request.description.substring(0, 100)}...
      </p>

      <div className="flex justify-between items-center">
        <span className="font-bold text-lg">
          ${request.total_amount.toLocaleString()}
        </span>
        <Button onClick={() => onView(request.id)}>
          View Details
        </Button>
      </div>
    </div>
  );
}
```

---

## 4. User Workflows

### Workflow 1: Creating a Purchase Request (Staff)

**Step-by-step:**

1. **Navigate to Dashboard**
   - Login with staff credentials
   - See "My Requests" dashboard

2. **Click "Create New Request"**
   - Form appears with fields:
     - Title (required)
     - Description (required)
     - Proforma file (required)

3. **Fill in Details**
   ```
   Title: "10 Ergonomic Office Chairs"
   Description: "For the new marketing team workspace on 3rd floor"
   ```

4. **Upload Proforma**
   - Click "Upload Proforma"
   - Select PDF file from computer
   - Wait for upload (progress bar shows)
   - See "Processing..." indicator

5. **AI Extracts Data**
   - System shows extracted data:
     ```
     Vendor: ABC Supplies Ltd
     Items:
       - Ergonomic Chair x10 @ $500 = $5,000
     Tax: $900
     Total: $5,900
     ```

6. **Review and Edit**
   - Verify extracted data is correct
   - Manually edit if needed
   - Add additional items if necessary

7. **Save as Draft** (optional)
   - Click "Save Draft" to continue later
   - Or proceed to submit

8. **Submit for Approval**
   - Click "Submit for Approval"
   - Confirmation dialog appears
   - Click "Confirm"
   - Request status → PENDING
   - Success message: "Request submitted successfully"
   - Email sent to L1 approvers

9. **Track Progress**
   - Return to dashboard
   - See request in "Pending Approval" section
   - Click to view approval progress

---

### Workflow 2: Approving a Request (Approver L1)

**Step-by-step:**

1. **Receive Notification**
   - Email: "New purchase request awaiting your approval"
   - Click link or login to dashboard

2. **View Pending Approvals**
   - Dashboard shows: "3 requests awaiting your approval"
   - List of pending requests displayed

3. **Click on Request**
   - Opens request detail page
   - Shows:
     - Request title and description
     - Requester name
     - Total amount
     - Items list
     - Proforma document (downloadable)

4. **Review Proforma**
   - Click "View Proforma"
   - Document opens in new tab
   - Review vendor, items, prices

5. **Check Extracted Data**
   - Compare AI-extracted data with proforma
   - Verify accuracy

6. **Make Decision**

   **Option A: Approve**
   - Click "Approve" button
   - Modal appears: "Add comment (optional)"
   - Enter comment: "Approved - necessary for team expansion"
   - Click "Confirm Approval"
   - Success message: "Request approved"
   - Request moves to Level 2
   - Email sent to L2 approvers

   **Option B: Reject**
   - Click "Reject" button
   - Modal appears: "Reason for rejection (required)"
   - Enter reason: "Budget not available this quarter"
   - Click "Confirm Rejection"
   - Request status → REJECTED
   - Email sent to requester

7. **View Approval History**
   - "Approval Log" section shows:
     ```
     Jan 15, 2024 10:30 AM - Submitted by Sarah Johnson
     Jan 15, 2024 2:00 PM - Approved by John Smith (L1)
     ```

---

### Workflow 3: Final Approval & PO Generation (Approver L2)

**Step-by-step:**

1. **Receive Notification**
   - Email: "Request approved by L1, awaiting your approval"

2. **Review Request**
   - See all previous details
   - View L1 approver's comments
   - Review proforma

3. **Final Approval**
   - Click "Approve" (final)
   - Enter comment (optional)
   - Click "Confirm"
   - Request status → APPROVED

4. **Automatic PO Generation**
   - System immediately generates PO
   - Progress indicator: "Generating Purchase Order..."
   - PO created in 5-10 seconds

5. **PO Available**
   - "Purchase Order" section appears
   - Shows PO number: PO-2024-000123
   - Download PO button available
   - Email sent to requester and finance with PO attached

---

### Workflow 4: Uploading Receipt (Staff)

**Step-by-step:**

1. **Complete Purchase**
   - Staff member buys the items
   - Receives receipt from vendor

2. **Navigate to Request**
   - Go to "My Requests"
   - Find the approved request
   - Click "View Details"

3. **Upload Receipt**
   - Click "Upload Receipt" button
   - Select receipt file (PDF/image)
   - Upload (progress bar)
   - See "Processing receipt..." indicator

4. **AI Validation**
   - System extracts data from receipt
   - Compares with original PO
   - Shows validation results:

   **If valid:**
   ```
   ✓ Receipt validated successfully
   ✓ Vendor matches: ABC Supplies Ltd
   ✓ Items match: 10 x Ergonomic Chair
   ✓ Total matches: $5,900
   ```

   **If discrepancies found:**
   ```
   ⚠ Discrepancies detected:

   Price mismatch:
     Expected: $500/chair
     Actual: $550/chair
     Difference: +$50/chair

   Total variance: +$500
   ```

5. **Finance Review**
   - If discrepancies found, finance is notified
   - Finance can approve override or request action

---

## 5. API Reference

### Authentication Endpoints

#### POST /api/auth/login/
**Description**: Login and get JWT tokens

**Request:**
```json
{
  "username": "sarah.johnson",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "123",
      "username": "sarah.johnson",
      "email": "sarah@example.com",
      "role": "STAFF",
      "first_name": "Sarah",
      "last_name": "Johnson"
    }
  }
}
```

---

#### POST /api/auth/refresh/
**Description**: Refresh access token

**Request:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

### Purchase Request Endpoints

#### POST /api/requests/
**Description**: Create new purchase request

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request (multipart):**
```
title: "Office Chairs Purchase"
description: "For marketing team"
proforma_file: <file>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "abc-123-def",
    "title": "Office Chairs Purchase",
    "description": "For marketing team",
    "status": "DRAFT",
    "total_amount": null,
    "created_by": {
      "id": "123",
      "name": "Sarah Johnson"
    },
    "proforma_file": "/media/proforma/abc-123.pdf",
    "proforma_extracted_data": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

#### GET /api/requests/
**Description**: List purchase requests (filtered by role)

**Query Parameters:**
- `status` - Filter by status (DRAFT, PENDING, APPROVED, REJECTED)
- `search` - Search in title/description
- `ordering` - Sort field (-created_at for descending)
- `page` - Page number
- `page_size` - Items per page

**Example:** `GET /api/requests/?status=PENDING&page=1&page_size=20`

**Response:**
```json
{
  "status": "success",
  "data": {
    "count": 45,
    "next": "/api/requests/?page=2",
    "previous": null,
    "results": [
      {
        "id": "abc-123-def",
        "title": "Office Chairs Purchase",
        "status": "PENDING",
        "total_amount": "5900.00",
        "current_approval_level": 1,
        "created_by": {
          "id": "123",
          "name": "Sarah Johnson"
        },
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

---

#### GET /api/requests/{id}/
**Description**: Get request details

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "abc-123-def",
    "title": "Office Chairs Purchase",
    "description": "For the new marketing team workspace",
    "status": "PENDING",
    "total_amount": "5900.00",
    "current_approval_level": 1,
    "created_by": {
      "id": "123",
      "name": "Sarah Johnson",
      "email": "sarah@example.com"
    },
    "proforma_file": "/media/proforma/abc-123.pdf",
    "proforma_extracted_data": {
      "vendor": {
        "name": "ABC Supplies Ltd",
        "contact": "+250788123456"
      },
      "items": [
        {
          "name": "Ergonomic Chair",
          "quantity": 10,
          "unit_price": 500.00,
          "total": 5000.00
        }
      ],
      "subtotal": 5000.00,
      "tax": 900.00,
      "total": 5900.00
    },
    "purchase_order_file": null,
    "receipt_file": null,
    "approval_logs": [
      {
        "id": "log-1",
        "approver": {
          "name": "John Smith",
          "role": "APPROVER_L1"
        },
        "action": "SUBMITTED",
        "comments": "",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

#### PATCH /api/requests/{id}/approve/
**Description**: Approve request (Approver only)

**Request:**
```json
{
  "comments": "Approved - necessary for team expansion"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "abc-123-def",
    "status": "PENDING",
    "current_approval_level": 2,
    "message": "Request approved at Level 1"
  }
}
```

---

#### PATCH /api/requests/{id}/reject/
**Description**: Reject request (Approver only)

**Request:**
```json
{
  "comments": "Budget not available this quarter"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "abc-123-def",
    "status": "REJECTED",
    "message": "Request rejected"
  }
}
```

---

#### POST /api/requests/{id}/upload-receipt/
**Description**: Upload receipt (Staff only)

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request:**
```
receipt_file: <file>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "abc-123-def",
    "receipt_file": "/media/receipts/receipt-abc-123.pdf",
    "receipt_validation": {
      "valid": false,
      "discrepancies": [
        {
          "field": "price",
          "item": "Ergonomic Chair",
          "expected": 500.00,
          "actual": 550.00,
          "variance": 50.00,
          "severity": "MEDIUM"
        }
      ],
      "confidence_score": 0.92
    },
    "message": "Receipt uploaded and validated"
  }
}
```

---

### Dashboard Endpoints

#### GET /api/dashboard/stats/
**Description**: Get role-specific statistics

**Response (Staff):**
```json
{
  "status": "success",
  "data": {
    "total_requests": 12,
    "pending_requests": 3,
    "approved_requests": 7,
    "rejected_requests": 2,
    "total_amount_approved": "45000.00",
    "recent_requests": [...]
  }
}
```

**Response (Approver):**
```json
{
  "status": "success",
  "data": {
    "pending_approvals": 5,
    "approved_by_me": 23,
    "rejected_by_me": 4,
    "total_amount_pending": "28000.00",
    "pending_requests": [...]
  }
}
```

---

## 6. Database Design

### User Model
```python
class User(AbstractUser):
    ROLE_CHOICES = [
        ('STAFF', 'Staff'),
        ('APPROVER_L1', 'Approver Level 1'),
        ('APPROVER_L2', 'Approver Level 2'),
        ('FINANCE', 'Finance'),
        ('ADMIN', 'Administrator'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    approval_level = models.IntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
```

---

### PurchaseRequest Model
```python
class PurchaseRequest(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    current_approval_level = models.IntegerField(default=0)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')

    proforma_file = models.FileField(upload_to='proforma/', null=True)
    proforma_extracted_data = models.JSONField(null=True, blank=True)

    purchase_order_file = models.FileField(upload_to='purchase_orders/', null=True)
    purchase_order_data = models.JSONField(null=True, blank=True)

    receipt_file = models.FileField(upload_to='receipts/', null=True)
    receipt_data = models.JSONField(null=True, blank=True)
    receipt_validation = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['created_by', 'status']),
        ]
```

---

### RequestItem Model
```python
class RequestItem(models.Model):
    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
```

---

### ApprovalLog Model
```python
class ApprovalLog(models.Model):
    ACTION_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('UPDATED', 'Updated'),
    ]

    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='approval_logs')
    approver = models.ForeignKey(User, on_delete=models.CASCADE)
    approval_level = models.IntegerField()
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comments = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
```

---

## 7. Security Features

### 1. Authentication Security

**JWT Token Strategy:**
- Access token: 15 minutes expiry
- Refresh token: 7 days expiry
- Token rotation on refresh
- Blacklisting on logout
- Secure HTTP-only cookies (optional)

**Password Requirements:**
- Minimum 8 characters
- Must include: uppercase, lowercase, number
- Django's built-in password validators
- Bcrypt hashing (Django default)

---

### 2. Authorization & Permissions

**Role-Based Access Control:**
```python
# Custom permission classes

class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'STAFF'

class IsApproverL1(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'APPROVER_L1'

class CanApproveRequest(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if user's approval level matches request's current level
        return (
            request.user.approval_level == obj.current_approval_level and
            obj.status == 'PENDING'
        )
```

**Object-Level Permissions:**
- Staff can only view/edit their own requests
- Approvers see requests at their level
- Finance sees all approved requests
- Admin sees everything

---

### 3. Input Validation

**Serializer Validation:**
```python
class PurchaseRequestSerializer(serializers.ModelSerializer):
    def validate_total_amount(self, value):
        if value <= 0:
            raise ValidationError("Amount must be positive")
        if value > 1000000:
            raise ValidationError("Amount exceeds maximum limit")
        return value

    def validate_proforma_file(self, value):
        # Check file size
        if value.size > 10 * 1024 * 1024:  # 10MB
            raise ValidationError("File size exceeds 10MB")

        # Check file type
        ext = value.name.split('.')[-1].lower()
        if ext not in ['pdf', 'png', 'jpg', 'jpeg']:
            raise ValidationError("Invalid file type")

        return value
```

---

### 4. File Upload Security

**Validation Steps:**
1. Extension check (.pdf, .png, .jpg only)
2. MIME type verification
3. File size limit (10MB max)
4. Unique filename (UUID)
5. Store outside web root
6. Virus scanning (optional: ClamAV)

**Storage Security:**
- Production: AWS S3 with signed URLs
- Private buckets (not public)
- 1-hour expiring URLs
- Access logging enabled

---

### 5. SQL Injection Prevention

**Django ORM:**
- Automatically parameterizes queries
- Never concatenate user input into SQL
- Use `.filter()`, `.get()`, etc.

**If raw SQL needed:**
```python
# ✅ Correct (parameterized)
User.objects.raw('SELECT * FROM users WHERE id = %s', [user_id])

# ❌ NEVER do this
User.objects.raw(f'SELECT * FROM users WHERE id = {user_id}')
```

---

### 6. XSS Prevention

**Backend:**
- Django templates auto-escape HTML
- DRF serializes to JSON (safe)
- CSP headers configured

**Frontend:**
- React auto-escapes by default
- Use `dangerouslySetInnerHTML` carefully
- Sanitize user input with DOMPurify

---

### 7. CSRF Protection

- REST API uses JWT (stateless) - CSRF not applicable
- Django admin has CSRF protection enabled
- CORS properly configured for known origins

---

### 8. Rate Limiting

**DRF Throttling:**
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'upload': '10/hour',  # Custom for file uploads
    }
}
```

---

### 9. Secrets Management

**Environment Variables:**
```bash
# Never commit these!
SECRET_KEY=...
DATABASE_URL=...
OPENAI_API_KEY=...
AWS_ACCESS_KEY_ID=...
```

**Production:**
- Use AWS Secrets Manager
- Or environment variables in deployment platform
- Rotate secrets regularly

---

### 10. Security Headers

**Django Middleware:**
```python
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True  # Production only
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 8. Performance Optimizations

### 1. Database Query Optimization

**N+1 Query Problem:**
```python
# ❌ Bad (N+1 queries)
requests = PurchaseRequest.objects.all()
for req in requests:
    print(req.created_by.name)  # Query for each!

# ✅ Good (2 queries total)
requests = PurchaseRequest.objects.select_related('created_by').all()
for req in requests:
    print(req.created_by.name)  # No additional query
```

**Prefetch Related:**
```python
# ✅ Optimized
requests = PurchaseRequest.objects.prefetch_related(
    'items',
    'approval_logs__approver'
).select_related('created_by')
```

**Field Selection:**
```python
# Only fetch needed fields
PurchaseRequest.objects.only('id', 'title', 'status', 'total_amount')
```

---

### 2. Caching Strategy

**Redis Caching:**
```python
from django.core.cache import cache

def get_dashboard_stats(user_id):
    cache_key = f'dashboard_stats_{user_id}'
    stats = cache.get(cache_key)

    if not stats:
        stats = calculate_stats(user_id)
        cache.set(cache_key, stats, 300)  # 5 minutes

    return stats
```

**View-Level Caching:**
```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # 5 minutes
def dashboard_stats(request):
    # ...
```

---

### 3. Pagination

**Always paginate lists:**
```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

---

### 4. Async Processing

**Celery for Heavy Tasks:**
```python
# Don't block the request-response cycle
@shared_task
def process_proforma(file_path):
    # This runs in background
    extract_data(file_path)
```

---

### 5. File Upload Optimization

**Chunked Uploads:**
- Frontend splits large files into chunks
- Upload chunks in parallel
- Resume on failure

**Direct S3 Upload:**
- Get presigned URL from backend
- Frontend uploads directly to S3
- Backend receives S3 URL
- No file goes through backend server

---

### 6. Frontend Optimization

**Code Splitting:**
```typescript
// Lazy load routes
const StaffDashboard = lazy(() => import('./pages/StaffDashboard'));
```

**Image Optimization:**
- Use WebP format
- Lazy loading
- Responsive images

**Memoization:**
```typescript
const MemoizedComponent = React.memo(ExpensiveComponent);

const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);
```

---

## 9. Troubleshooting Guide

### Issue: "Token has expired"

**Cause:** Access token lifetime exceeded (15 minutes)

**Solution:**
```typescript
// Automatically refresh token
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response.status === 401) {
      // Refresh token
      const newToken = await refreshAccessToken();
      // Retry original request
      return axios(error.config);
    }
    return Promise.reject(error);
  }
);
```

---

### Issue: "Permission denied"

**Cause:** User role doesn't have permission for this action

**Solution:**
- Check user role: `GET /api/auth/me/`
- Verify role requirements for endpoint
- Contact admin if role is incorrect

---

### Issue: "Concurrent modification detected"

**Cause:** Two users tried to modify the same request simultaneously

**Solution:**
- Refresh the page to get latest data
- Try action again
- System prevents duplicate approvals

---

### Issue: Document processing stuck

**Cause:** Celery task failed or OpenAI API error

**Solution:**
1. Check Celery logs: `docker logs celery`
2. Verify OpenAI API key is valid
3. Retry processing: Re-upload document
4. Check file format (PDF or image)

---

### Issue: File upload fails

**Cause:** File too large, wrong format, or network issue

**Solution:**
- Max size: 10MB
- Allowed formats: PDF, PNG, JPG
- Compress large files
- Check internet connection

---

### Issue: Receipt validation shows false discrepancies

**Cause:** OCR/AI extraction inaccuracy

**Solution:**
- Re-upload clearer image/scan
- Use PDF instead of image if possible
- Finance can manually review and override
- Contact support if persistent

---

## 10. Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] SECRET_KEY generated (strong)
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS set correctly
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] OpenAI API key tested
- [ ] AWS credentials configured
- [ ] Email settings tested

### Deployment

- [ ] Docker images built
- [ ] Database created (PostgreSQL)
- [ ] Redis instance running
- [ ] Backend deployed
- [ ] Celery worker running
- [ ] Frontend built and deployed
- [ ] Nginx configured
- [ ] SSL certificate installed
- [ ] Domain DNS configured

### Post-Deployment

- [ ] Health check endpoint working
- [ ] Login functionality tested
- [ ] File upload tested
- [ ] Document processing tested
- [ ] Approval workflow tested
- [ ] Email notifications working
- [ ] Monitoring configured
- [ ] Backup system tested

---

## Conclusion

This guide covers all major features and implementation details of the Purchase Request & Approval System. For specific code examples and further details, refer to:

- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Detailed technical plan
- API Documentation (Swagger) - Available at `/api/docs/`
- Source code comments
- Test files for examples

**Need Help?**
- Check logs: `docker logs <container>`
- Review error messages carefully
- Test in development environment first
- Contact development team

---

**Document Version:** 1.0
**Last Updated:** 2024-01-20
**Maintained By:** Development Team
