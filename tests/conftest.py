import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from backend.main import app
from backend.db.mongodb import MongoDB


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def mock_mongodb() -> AsyncGenerator[MagicMock, None]:
    mock_db = MagicMock(spec=AsyncIOMotorDatabase)
    mock_client = MagicMock(spec=AsyncIOMotorClient)
    mock_client.__getitem__ = MagicMock(return_value=mock_db)
    mock_db.__getitem__ = MagicMock(return_value=MagicMock())

    with patch.object(MongoDB, 'client', mock_client):
        with patch.object(MongoDB, 'db', mock_db):
            yield mock_db


@pytest.fixture
def sample_pdf_content() -> str:
    return """
    RENT ROLL
    Property: Test Property
    Date: January 1, 2024

    Unit    Tenant Name       Square Feet    Monthly Rent    Lease Start    Lease End
    101     ABC Corporation   1,500          $3,500.00       01/01/2023     12/31/2025
    102     XYZ LLC           1,200          $2,800.00       03/15/2023     03/14/2024
    103     Vacant            1,000          $0.00           N/A            N/A
    201     DEF Industries    2,000          $5,000.00       06/01/2023     05/31/2026
    """


@pytest.fixture
def sample_pl_content() -> str:
    return """
    INCOME STATEMENT
    For the Year Ended December 31, 2023

    REVENUE
    Rental Income                    $1,200,000
    Parking Income                      $50,000
    Other Income                        $25,000
    Total Revenue                   $1,275,000

    EXPENSES
    Property Taxes                     $150,000
    Insurance                           $35,000
    Utilities                           $75,000
    Repairs & Maintenance              $100,000
    Management Fees                     $63,750
    Total Expenses                     $423,750

    Net Operating Income               $851,250
    """


@pytest.fixture
def sample_lease_content() -> str:
    return """
    COMMERCIAL LEASE AGREEMENT

    This Lease Agreement is entered into as of January 1, 2024.

    LANDLORD: ABC Properties LLC
    TENANT: XYZ Corporation, a Delaware Corporation

    PREMISES: Suite 100, 123 Main Street, Anytown, NY 10001
    Square Footage: 5,000 SF

    TERM: 5 years commencing January 1, 2024 and ending December 31, 2028

    BASE RENT: $15,000 per month ($36.00/SF/year)
    SECURITY DEPOSIT: $45,000

    PERMITTED USE: General office purposes

    COMMENCEMENT DATE: January 1, 2024
    EXPIRATION DATE: December 31, 2028
    """


@pytest.fixture
def sample_operating_statement_content() -> str:
    return """
    OPERATING STATEMENT
    Property: Test Property
    Period: January 1, 2024 - December 31, 2024

    OPERATING RESULTS
    Gross Potential Rent              $1,200,000
    Vacancy & Collection Loss          ($60,000)
    Effective Gross Income            $1,140,000

    Operating Expenses:
    Real Estate Taxes                 $150,000
    Insurance                          $35,000
    Utilities                          $75,000
    Repairs & Maintenance             $100,000
    Management Fee                     $57,000
    Total Operating Expenses          $417,000

    Net Operating Income              $723,000

    OCCUPANCY DATA
    Total Square Footage:             25,000
    Occupied Square Footage:          23,750
    Occupancy Rate:                   95%
    """


@pytest.fixture
def mock_ocr_result() -> dict:
    return {
        "status": "success",
        "text": "Sample document text",
        "extractions": [
            {
                "extractor": "RentRollExtractor",
                "data": {
                    "tenants": [
                        {
                            "unit": "101",
                            "tenant": "ABC Corp",
                            "square_footage": 1500,
                            "current_rent": 3500,
                        }
                    ],
                    "summary": {
                        "total_units": 1,
                        "total_square_footage": 1500,
                        "total_monthly_rent": 3500,
                    },
                },
                "confidence": {"overall": 0.95},
            }
        ],
        "processed_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def mock_financial_analysis() -> dict:
    return {
        "noi": 250000,
        "capRate": 0.05,
        "dscr": 1.25,
        "ltv": 75.0,
        "occupancyRate": 95.0,
    }


def create_mock_file(
    content: bytes = b"test content",
    filename: str = "test.pdf"
) -> tuple[bytes, str]:
    return content, filename


@pytest_asyncio.fixture
async def mock_mongodb_connection():
    MongoDB.client = None
    MongoDB.db = None
    yield
    if MongoDB.client:
        MongoDB.client.close()
    MongoDB.client = None
    MongoDB.db = None


@pytest.fixture
def sample_extraction_result() -> dict:
    return {
        "success": True,
        "data": {
            "tenants": [
                {
                    "unit": "101",
                    "tenant": "Test Tenant",
                    "square_footage": 1000,
                    "current_rent": 2500,
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "security_deposit": 5000,
                    "occupied": True,
                }
            ],
            "summary": {
                "total_units": 1,
                "total_square_footage": 1000,
                "occupied_square_footage": 1000,
                "occupancy_rate": 100.0,
                "total_monthly_rent": 2500,
                "average_rent_psf": 30.0,
            },
        },
        "confidence_scores": {
            "tenant.unit": 1.0,
            "tenant.square_footage": 1.0,
            "tenant.current_rent": 1.0,
            "overall": 1.0,
        },
        "validation_errors": [],
        "timestamp": "2024-01-01T00:00:00",
    }
