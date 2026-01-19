# API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

## Endpoints

### Authentication

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "securepassword123",
  "full_name": "Full Name (optional)"
}
```

**Response:**
```json
{
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "username": "username",
    "full_name": "Full Name",
    "role": "analyst",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00"
  },
  "token": {
    "access_token": "jwt_token",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

#### POST /auth/token
Authenticate and get access token.

**Request Body (form-urlencoded):**
```
username=username&password=password
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### GET /auth/me
Get current user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "role": "analyst",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00"
}
```

#### POST /auth/change-password
Change user password.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newsecurepassword123"
}
```

**Response:**
```json
{
  "message": "Password changed successfully"
}
```

### Documents

#### POST /documents/upload
Upload and process a document.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request Body (multipart/form-data):**
```
file: <file attachment>
```

**Supported file types:**
- PDF (.pdf)
- Excel (.xlsx)
- Word (.docx)

**Response:**
```json
{
  "status": "success",
  "id": "document_id",
  "filename": "rent_roll.pdf",
  "extractions": [
    {
      "type": "RentRollExtractor",
      "confidence": 0.95
    }
  ]
}
```

#### GET /documents/{document_id}/status
Get document processing status.

**Response:**
```json
{
  "status": "completed",
  "extractions": [
    {
      "type": "RentRollExtractor",
      "confidence": 0.95
    }
  ]
}
```

#### GET /documents/{document_id}/analysis
Get document financial analysis.

**Response:**
```json
{
  "noi": 851250,
  "capRate": 0.0685,
  "dscr": 1.35,
  "ltv": 72.5,
  "occupancyRate": 94.5
}
```

#### GET /documents/types
Get list of supported document types.

**Response:**
```json
{
  "supported_types": [
    {
      "name": "Rent Roll",
      "extractor": "RentRollExtractor",
      "description": "Tenant and lease information from rent rolls"
    },
    {
      "name": "P&L Statement",
      "extractor": "PLStatementExtractor",
      "description": "Financial data from profit and loss statements"
    },
    {
      "name": "Operating Statement",
      "extractor": "OperatingStatementExtractor",
      "description": "Combined financial and occupancy data from operating statements"
    },
    {
      "name": "Lease",
      "extractor": "LeaseExtractor",
      "description": "Detailed lease terms and conditions"
    }
  ]
}
```

### Health

#### GET /health
Comprehensive health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "checks": {
    "mongodb": {
      "status": "healthy",
      "latency_ms": 5
    },
    "system": {
      "status": "healthy",
      "details": {
        "cpu_percent": 25.5,
        "memory_percent": 45.2,
        "disk_percent": 62.1
      }
    }
  }
}
```

#### GET /health/live
Kubernetes liveness probe.

**Response:**
```json
{
  "status": "alive"
}
```

#### GET /health/ready
Kubernetes readiness probe.

**Response:**
```json
{
  "status": "ready"
}
```

#### GET /health/metrics
System metrics.

**Response:**
```json
{
  "uptime_seconds": 3600,
  "cpu_percent": 25.5,
  "memory_percent": 45.2,
  "disk_percent": 62.1,
  "timestamp": "2024-01-01T00:00:00"
}
```

## Error Responses

All errors follow this format:

```json
{
  "status": "error",
  "error": "Error message",
  "detail": "Detailed error information (development only)"
}
```

### Common Status Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 201  | Created |
| 400  | Bad Request |
| 401  | Unauthorized |
| 403  | Forbidden |
| 404  | Not Found |
| 422  | Validation Error |
| 429  | Rate Limit Exceeded |
| 500  | Internal Server Error |

## Rate Limiting

- 100 requests per minute per IP
- Rate limit headers included in response
