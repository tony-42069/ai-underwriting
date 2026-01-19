# Database Schema

## Collections

### users Collection

Stores user account information.

```json
{
  "_id": ObjectId("..."),
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "hashed_password": "$2b$12$...",
  "role": "analyst",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "last_login": "2024-01-01T00:00:00"
}
```

**Indexes:**
- `email` (unique)
- `username` (unique)
- `created_at` (descending)

### documents Collection

Stores uploaded documents and processing results.

```json
{
  "_id": ObjectId("..."),
  "filename": "rent_roll.pdf",
  "path": "/app/backend/uploads/rent_roll.pdf",
  "user_id": ObjectId("..."),
  "is_public": false,
  "status": "completed",
  "processing_result": {
    "status": "success",
    "text": "Extracted text content...",
    "extractions": [
      {
        "extractor": "RentRollExtractor",
        "data": {
          "tenants": [...],
          "summary": {...}
        },
        "confidence": {
          "overall": 0.95,
          "tenant.unit": 1.0,
          "tenant.square_footage": 0.9
        }
      }
    ],
    "processed_at": "2024-01-01T00:00:00"
  },
  "analysis_result": {
    "noi": 851250,
    "capRate": 0.0685,
    "dscr": 1.35,
    "ltv": 72.5,
    "occupancyRate": 94.5
  },
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

**Indexes:**
- `filename`
- `status`
- `created_at` (descending, with TTL - 30 days)
- `user_id`
- `processing_result.extractions.extractor`
- `processing_result.processed_at` (with TTL)

### analyses Collection

Stores financial analysis results.

```json
{
  "_id": ObjectId("..."),
  "document_id": ObjectId("..."),
  "user_id": ObjectId("..."),
  "metrics": {
    "noi": 851250,
    "capRate": 0.0685,
    "dscr": 1.35,
    "ltv": 72.5,
    "occupancyRate": 94.5,
    "grossIncome": 1275000,
    "totalExpenses": 423750,
    "expenseRatio": 33.24,
    "debtYield": 11.35
  },
  "risk_flags": [
    "DSCR below 1.25 - potential cash flow issues"
  ],
  "validation_report": {
    "overall_valid": true,
    "confidence_score": 0.92
  },
  "created_at": "2024-01-01T00:00:00"
}
```

**Indexes:**
- `document_id` (unique)
- `user_id`
- `created_at` (descending)

### validations Collection

Stores data validation results.

```json
{
  "_id": ObjectId("..."),
  "document_id": ObjectId("..."),
  "validation_type": "rent_roll",
  "report": {
    "overall_valid": true,
    "confidence_score": 0.95,
    "issues": [
      {
        "severity": "warning",
        "field": "tenant.square_footage",
        "message": "Low confidence for unit 101",
        "current_value": 1500
      }
    ]
  },
  "risk_flags": [],
  "created_at": "2024-01-01T00:00:00"
}
```

**Indexes:**
- `document_id`
- `overall_valid`
- `created_at` (descending)

### processing_history Collection

Stores audit trail for document processing.

```json
{
  "_id": ObjectId("..."),
  "document_id": ObjectId("..."),
  "steps": [
    {
      "step": "upload",
      "status": "completed",
      "started_at": "2024-01-01T00:00:00",
      "completed_at": "2024-01-01T00:00:01",
      "duration_ms": 1000
    },
    {
      "step": "ocr",
      "status": "completed",
      "started_at": "2024-01-01T00:00:01",
      "completed_at": "2024-01-01T00:00:15",
      "duration_ms": 14000
    },
    {
      "step": "extraction",
      "status": "completed",
      "started_at": "2024-01-01T00:00:15",
      "completed_at": "2024-01-01T00:00:18",
      "duration_ms": 3000
    }
  ],
  "started_at": "2024-01-01T00:00:00",
  "completed_at": "2024-01-01T00:00:18",
  "total_duration_ms": 18000
}
```

**Indexes:**
- `document_id`
- `step`
- `started_at` (descending)

### migrations Collection

Stores migration records.

```json
{
  "_id": ObjectId("..."),
  "version": "001",
  "description": "Initial schema setup",
  "applied_at": "2024-01-01T00:00:00"
}
```

## Relationships

```
users (1) ────< (N) documents
users (1) ────< (N) analyses
documents (1) ────< (N) validations
documents (1) ────< (N) processing_history
documents (1) ────< (N) analyses
```

## TTL Indexes

- `documents.processing_result.processed_at`: 30 days (auto-delete old completed documents)
- `documents.status=error`: 24 hours (auto-delete failed documents)
