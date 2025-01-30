# AI Underwriting Assistant

An advanced document processing system for commercial real estate underwriting, capable of extracting and analyzing information from various document types including rent rolls, P&L statements, operating statements, and lease documents.

## Features

- **Multi-Format Document Support**
  - PDF (with OCR capabilities)
  - Excel spreadsheets
  - Word documents

- **Specialized Document Extractors**
  - Rent Roll Extractor
    - Tenant information
    - Lease terms
    - Occupancy data
    - Rent analysis
  - P&L Statement Extractor
    - Revenue items
    - Expense categories
    - NOI calculations
    - Historical comparisons
  - Operating Statement Extractor
    - Combined financial metrics
    - Budget variance analysis
    - Period comparisons
  - Lease Document Extractor
    - Key lease terms
    - Financial obligations
    - Special provisions
    - Key dates

- **Advanced Analysis**
  - Confidence scoring for extracted data
  - Automated data validation
  - Risk factor identification
  - Financial metrics calculation

- **API Features**
  - Document upload and processing
  - Extraction results retrieval
  - Status monitoring
  - Statistical analysis

## Prerequisites

- Python 3.9+
- MongoDB 4.4+
- Tesseract OCR
- Poppler (for PDF processing)
- Azure OpenAI API access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-underwriting.git
cd ai-underwriting
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Tesseract OCR:
- Windows: Download and install from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- Mac: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

5. Install Poppler:
- Windows: Download from [Poppler Releases](http://blog.alivate.com.au/poppler-windows/)
- Mac: `brew install poppler`
- Linux: `sudo apt-get install poppler-utils`

6. Configure environment variables:
```bash
cp backend/.env.example backend/.env
```
Edit `.env` with your settings.

## Configuration

Key environment variables:

```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=ai_underwriting

# OCR Configuration
POPPLER_PATH=/path/to/poppler
TESSERACT_PATH=/path/to/tesseract

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=your-embedding-deployment
```

## Usage

1. Start the server:
```bash
cd backend
uvicorn main:app --reload
```

2. Access the API documentation:
```
http://localhost:8000/api/v1/docs
```

## API Endpoints

### Document Processing

- `POST /api/v1/documents/upload`
  - Upload and process a document
  - Supports PDF, DOCX, XLSX

- `GET /api/v1/documents/{document_id}/status`
  - Check processing status
  - Get confidence scores

- `GET /api/v1/documents/{document_id}/content`
  - Get extracted content
  - Access all extractions

- `GET /api/v1/documents/{document_id}/extraction/{extractor_type}`
  - Get specific extraction results
  - Filter by extractor type

- `GET /api/v1/documents/types`
  - List supported document types
  - Get extractor descriptions

## Development

### Project Structure

```
backend/
├── api/
│   └── documents.py
├── services/
│   ├── extractors/
│   │   ├── base.py
│   │   ├── rent_roll.py
│   │   ├── pl_statement.py
│   │   ├── operating_statement.py
│   │   └── lease.py
│   └── ocr.py
├── db/
│   └── mongodb.py
├── config/
│   └── settings.py
└── main.py
```

### Adding New Extractors

1. Create a new extractor class in `services/extractors/`
2. Inherit from `BaseExtractor`
3. Implement required methods:
   - `can_handle()`
   - `extract()`
   - `validate()`

Example:
```python
from .base import BaseExtractor

class NewDocumentExtractor(BaseExtractor):
    def can_handle(self, content: str, filename: str) -> bool:
        # Implement document type detection
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        # Implement data extraction
        pass

    def validate(self) -> bool:
        # Implement validation rules
        pass
```

## Testing

Run tests:
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
