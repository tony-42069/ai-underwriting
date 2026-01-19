# Architecture Overview

## System Architecture

The AI Underwriting Assistant is a full-stack web application designed for processing commercial real estate documents using AI-powered extraction and analysis.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌───────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐  │
│  │ Dashboard │  │   Upload   │  │  Analysis  │  │   Login   │  │
│  └─────┬─────┘  └─────┬──────┘  └─────┬──────┘  └─────┬─────┘  │
│        │              │               │               │         │
│        └──────────────┴───────────────┴───────────────┘         │
│                            │                                     │
│                     ┌──────▼──────┐                             │
│                     │   Axios     │                             │
│                     │   Client    │                             │
│                     └──────┬──────┘                             │
└────────────────────────────┼────────────────────────────────────┘
                             │ HTTP/API
┌────────────────────────────┼────────────────────────────────────┐
│                     ┌──────▼──────┐                             │
│                     │  FastAPI    │                             │
│                     │  Backend    │                             │
│                     └──────┬──────┘                             │
└────────────────────────────┼────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
       ┌──────▼──────┐ ┌──────▼──────┐ ┌───▼──────┐
       │   OCR       │ │  Extractors │ │  Health  │
       │  Service    │ │  Service    │ │  Checks  │
       └──────┬──────┘ └──────┬──────┘ └────┬─────┘
              │               │             │
       ┌──────▼──────┐ ┌──────▼──────┐      │
       │  Tesseract  │ │   MongoDB   │      │
       │   (OCR)     │ │  Database   │      │
       └─────────────┘ └──────┬──────┘      │
                             │              │
                             └──────────────┘
```

## Component Description

### Frontend (React + TypeScript)

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: React Query
- **Routing**: React Router v6
- **Forms**: React Hook Form

### Backend (Python + FastAPI)

- **Framework**: FastAPI
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT with bcrypt password hashing
- **OCR**: Tesseract + pdf2image
- **Document Processing**: Custom extractors for various document types

### Database (MongoDB)

- **Collections**:
  - `documents` - Uploaded documents and processing results
  - `users` - User accounts and authentication
  - `analyses` - Financial analysis results
  - `validations` - Data validation reports
  - `processing_history` - Audit trail

## Data Flow

### Document Upload Flow

```
1. User uploads document via React Upload component
2. Frontend sends multipart/form-data to /api/v1/documents/upload
3. Backend saves file to uploads directory
4. DocumentProcessor extracts text using:
   - pdf2image + Tesseract for PDFs
   - pandas + openpyxl for Excel
   - python-docx for Word documents
5. Text is passed to relevant extractors:
   - RentRollExtractor
   - PLStatementExtractor
   - OperatingStatementExtractor
   - LeaseExtractor
6. FinancialAnalysis calculates metrics:
   - NOI, Cap Rate, DSCR, LTV, Occupancy
7. ValidationService validates extracted data
8. Results stored in MongoDB
9. Response returned to frontend
```

## Document Extractors

### Rent Roll Extractor
Extracts:
- Tenant names
- Unit numbers
- Square footage
- Current rent
- Lease start/end dates
- Security deposits

### P&L Statement Extractor
Extracts:
- Revenue items (rental, parking, other income)
- Expense categories (taxes, insurance, utilities, etc.)
- NOI calculation
- Expense ratio

### Operating Statement Extractor
Extracts:
- Period information
- Budget vs actual comparisons
- Variance analysis
- Combined metrics

### Lease Document Extractor
Extracts:
- Lease terms and conditions
- Base rent and escalations
- Key dates (commencement, expiration)
- Tenant and property information

## Security Architecture

### Authentication Flow

```
1. User POSTs credentials to /auth/token
2. Backend validates against MongoDB users collection
3. Returns JWT token with user info (ID, email, role)
4. Frontend stores token in localStorage
5. Subsequent requests include: Authorization: Bearer <token>
6. Backend middleware validates token and extracts user
7. Authorization middleware checks role permissions
```

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| Admin | Full access (users, documents, analytics, export) |
| Analyst | Upload, view, analytics, export |
| Viewer | View only |

## Infrastructure

### Development Environment

```
docker-compose up -d
├── backend:8000   (FastAPI with hot reload)
├── frontend:3000  (Vite dev server)
├── mongo:27017    (MongoDB)
└── mongo-express:8081 (Database admin UI)
```

### Production Environment

```
├── Backend Docker container
│   ├── Python 3.9
│   ├── Tesseract OCR
│   ├── Poppler
│   └── All Python dependencies
├── Frontend Docker container
│   ├── Node 18 build
│   ├── Nginx serve static files
│   └── API proxy configuration
└── MongoDB replica set
```

## CI/CD Pipeline

### GitHub Actions Workflows

**CI Pipeline** (on push/PR):
1. Linting (Ruff, ESLint)
2. Type checking (MyPy, TypeScript)
3. Backend tests (pytest)
4. Frontend tests (Vitest)
5. Docker image building

**CD Pipeline** (on main branch push):
1. Run full test suite
2. Build frontend production bundle
3. Build Docker images
4. Deploy to production server
5. Run database migrations
6. Health check verification

## Monitoring & Logging

### Health Check Endpoints

- `/health` - Comprehensive system health
- `/health/live` - Kubernetes liveness probe
- `/health/ready` - Kubernetes readiness probe
- `/health/metrics` - System metrics

### Structured Logging

All logs are JSON-formatted with:
- Timestamp
- Log level
- Message
- Module/function/line
- Request ID (for request tracing)
- User ID (for audit)
- Exception details (when applicable)
