# Development Setup Guide

## Prerequisites

### Required Software

- **Python 3.9+**
- **Node.js 18+**
- **MongoDB 7+**
- **Git**
- **Docker & Docker Compose** (optional, for containerized development)

### Optional Software

- **Tesseract OCR** - For PDF text extraction
- **Poppler** - For PDF to image conversion

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/tony-42069/ai-underwriting.git
cd ai-underwriting
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

#### Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Install System Dependencies

**Windows:**
1. Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Download Poppler from: http://blog.alivate.com.au/poppler-windows/
3. Add both to your PATH

**Mac:**
```bash
brew install tesseract poppler
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr poppler-utils
```

#### Configure Environment

```bash
# Copy example environment file
cp backend/.env.example backend/.env

# Edit with your settings
nano backend/.env
```

Required environment variables:
- `MONGODB_URL` - MongoDB connection string
- `POPPLER_PATH` - Path to Poppler bin directory
- `TESSERACT_PATH` - Path to Tesseract executable

#### Start MongoDB

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:7

# Or use local MongoDB installation
mongod --dbpath /path/to/data
```

#### Run the Backend

```bash
cd backend
uvicorn main:app --reload
```

Backend will be available at: http://localhost:8000

API documentation at: http://localhost:8000/docs

### 3. Frontend Setup

#### Install Node Dependencies

```bash
cd frontend
npm install
```

#### Start Development Server

```bash
npm run dev
```

Frontend will be available at: http://localhost:3000

### 4. Using Docker Compose (Alternative)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- MongoDB: localhost:27017
- Mongo Express: http://localhost:8081

## Project Structure

```
ai-underwriting/
├── backend/
│   ├── api/           # API routes
│   │   ├── auth.py    # Authentication endpoints
│   │   ├── documents.py # Document endpoints
│   │   └── health.py  # Health check endpoints
│   ├── config/        # Configuration
│   │   └── settings.py
│   ├── db/           # Database
│   │   └── mongodb.py
│   ├── middleware/   # Auth & authorization
│   ├── models/       # Pydantic models
│   ├── services/     # Business logic
│   │   ├── ocr.py
│   │   ├── extractors/
│   │   ├── financial_analysis.py
│   │   ├── validation.py
│   │   ├── cleanup.py
│   │   └── logging.py
│   └── main.py       # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── api/      # API client
│   │   ├── components/ # React components
│   │   ├── contexts/ # React contexts
│   │   ├── hooks/    # Custom hooks
│   │   ├── pages/    # Page components
│   │   └── types/    # TypeScript types
│   └── ...
├── docs/             # Documentation
├── tests/            # Tests
└── docker-compose.yml
```

## Development Workflow

### Running Tests

**Backend:**
```bash
pytest tests/ -v
```

**Frontend:**
```bash
cd frontend
npm run test
```

### Running Linters

**Backend:**
```bash
ruff check backend/
mypy backend/
```

**Frontend:**
```bash
cd frontend
npm run lint
```

### Adding New Extractors

1. Create a new file in `backend/services/extractors/`
2. Inherit from `BaseExtractor`
3. Implement `can_handle()` and `extract()` methods
4. Register the extractor in `backend/services/ocr.py`

Example:
```python
from .base import BaseExtractor

class NewDocumentExtractor(BaseExtractor):
    def can_handle(self, content: str, filename: str) -> bool:
        # Check if this extractor should handle the document
        return "keyword" in content.lower()

    def extract(self, content: str) -> dict:
        # Extract data from document
        return self.get_result()
```

### Code Style

- Python: Follow PEP 8, use Ruff for linting
- TypeScript: Follow ESLint rules, use Prettier for formatting
- Commit messages: Conventional Commits format

## Troubleshooting

### MongoDB Connection Failed

```bash
# Check if MongoDB is running
docker ps | grep mongo

# Restart MongoDB
docker-compose restart mongo
```

### Tesseract Not Found

```bash
# Verify installation
tesseract --version

# Check PATH
echo $PATH
```

### Frontend Not Loading

```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill the process
kill <PID>
```

## Additional Resources

- [API Documentation](../api/endpoints.md)
- [Architecture Overview](../architecture/overview.md)
- [Database Schema](../architecture/database.md)
