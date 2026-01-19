from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class DocumentType(str, Enum):
    RENT_ROLL = "rent_roll"
    PL_STATEMENT = "pl_statement"
    OPERATING_STATEMENT = "operating_statement"
    LEASE = "lease"
    UNKNOWN = "unknown"


class ConfidenceScores(BaseModel):
    overall: float = Field(..., ge=0, le=1, description="Overall extraction confidence score")
    fields: Optional[Dict[str, float]] = Field(default=None, description="Field-level confidence scores")


class ExtractionResult(BaseModel):
    extractor: str = Field(..., description="Name of the extractor used")
    data: Dict[str, Any] = Field(..., description="Extracted data")
    confidence: ConfidenceScores = Field(..., description="Confidence scores for extraction")


class ProcessingResult(BaseModel):
    status: ProcessingStatus = Field(..., description="Processing status")
    text: Optional[str] = Field(default=None, description="Extracted text content")
    extractions: List[ExtractionResult] = Field(default_factory=list, description="List of extraction results")
    processed_at: datetime = Field(default_factory=datetime.now, description="Processing timestamp")
    error: Optional[str] = Field(default=None, description="Error message if status is error")


class DocumentUploadResponse(BaseModel):
    status: str = Field(..., description="Upload status")
    id: str = Field(..., description="Document ID in database")
    filename: str = Field(..., description="Original filename")
    extractions: Optional[List[Dict[str, Any]]] = Field(default=None, description="Extraction summaries")


class DocumentStatusResponse(BaseModel):
    status: ProcessingStatus = Field(..., description="Document processing status")
    extractions: Optional[List[Dict[str, Any]]] = Field(default=None, description="Extraction summaries")
    error: Optional[str] = Field(default=None, description="Error message if applicable")


class DocumentContentResponse(BaseModel):
    text: str = Field(..., description="Extracted text content")
    extractions: List[ExtractionResult] = Field(..., description="Extraction results")


class SpecificExtractionResponse(BaseModel):
    extractor: str = Field(..., description="Extractor name")
    data: Dict[str, Any] = Field(..., description="Extracted data")
    confidence: ConfidenceScores = Field(..., description="Confidence scores")
    validation_errors: Optional[List[str]] = Field(default=None, description="Validation errors")


class ExtractorInfo(BaseModel):
    name: str = Field(..., description="Human-readable extractor name")
    extractor: str = Field(..., description="Extractor class name")
    description: str = Field(..., description="Extractor description")


class SupportedTypesResponse(BaseModel):
    supported_types: List[ExtractorInfo] = Field(..., description="List of supported document types")


class ErrorResponse(BaseModel):
    status: str = Field(default="error", description="Error status")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class FinancialMetrics(BaseModel):
    noi: float = Field(..., description="Net Operating Income")
    capRate: float = Field(..., description="Capitalization Rate (decimal)")
    dscr: float = Field(..., description="Debt Service Coverage Ratio")
    ltv: float = Field(..., description="Loan-to-Value ratio (percentage)")
    occupancyRate: float = Field(..., description="Occupancy rate (percentage)")


class TenantInfo(BaseModel):
    unit: str = Field(..., description="Unit number")
    tenant: str = Field(..., description="Tenant name")
    square_footage: float = Field(..., description="Square footage")
    current_rent: float = Field(..., description="Current monthly rent")
    start_date: Optional[str] = Field(default=None, description="Lease start date")
    end_date: Optional[str] = Field(default=None, description="Lease end date")
    security_deposit: Optional[float] = Field(default=None, description="Security deposit amount")
    occupied: bool = Field(default=True, description="Whether unit is occupied")


class RentRollSummary(BaseModel):
    total_units: int = Field(..., description="Total number of units")
    total_square_footage: float = Field(..., description="Total square footage")
    occupied_square_footage: float = Field(..., description="Occupied square footage")
    occupancy_rate: float = Field(..., description="Occupancy rate (percentage)")
    total_monthly_rent: float = Field(..., description="Total monthly rent")
    average_rent_psf: float = Field(..., description="Average rent per square foot (annualized)")


class RentRollData(BaseModel):
    tenants: List[TenantInfo] = Field(..., description="List of tenant records")
    summary: RentRollSummary = Field(..., description="Summary statistics")
