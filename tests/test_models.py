"""Test suite for API models and validation."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from backend.models.auth import (
    UserRole,
    UserCreate,
    UserResponse,
    Token,
    TokenData,
    AuthResponse,
    ChangePassword,
)
from backend.models.api import (
    ProcessingStatus,
    DocumentUploadResponse,
    DocumentStatusResponse,
    FinancialMetrics,
    ConfidenceScores,
)


class TestAuthModels:
    """Test authentication models."""

    def test_user_role_enum(self):
        """Test UserRole enum values."""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.ANALYST.value == "analyst"
        assert UserRole.VIEWER.value == "viewer"

    def test_user_create_valid(self):
        """Test valid UserCreate model."""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="securepassword123",
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password == "securepassword123"

    def test_user_create_with_full_name(self):
        """Test UserCreate with full name."""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="securepassword123",
            full_name="Test User",
        )
        assert user.full_name == "Test User"

    def test_user_create_short_password(self):
        """Test UserCreate rejects short password."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="short",
            )

    def test_user_response(self):
        """Test UserResponse model."""
        user = UserResponse(
            id="507f1f77bcf86cd799439011",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.ANALYST,
            is_active=True,
            created_at=datetime.now(),
        )
        assert user.id == "507f1f77bcf86cd799439011"
        assert user.role == UserRole.ANALYST

    def test_token_model(self):
        """Test Token model."""
        token = Token(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            token_type="bearer",
            expires_in=1800,
        )
        assert token.access_token.startswith("eyJ")
        assert token.token_type == "bearer"
        assert token.expires_in == 1800

    def test_auth_response(self):
        """Test AuthResponse model."""
        user = UserResponse(
            id="507f1f77bcf86cd799439011",
            email="test@example.com",
            username="testuser",
            role=UserRole.ANALYST,
            is_active=True,
            created_at=datetime.now(),
        )
        token = Token(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            token_type="bearer",
            expires_in=1800,
        )
        auth = AuthResponse(user=user, token=token)
        assert auth.user.id == "507f1f77bcf86cd799439011"
        assert auth.token.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

    def test_change_password(self):
        """Test ChangePassword model."""
        change = ChangePassword(
            current_password="oldpassword",
            new_password="newsecurepassword123",
        )
        assert change.current_password == "oldpassword"
        assert len(change.new_password) >= 8

    def test_change_password_short(self):
        """Test ChangePassword rejects short new password."""
        with pytest.raises(ValidationError):
            ChangePassword(
                current_password="oldpassword",
                new_password="short",
            )


class TestApiModels:
    """Test API models."""

    def test_processing_status_enum(self):
        """Test ProcessingStatus enum values."""
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.PROCESSING.value == "processing"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.ERROR.value == "error"

    def test_document_upload_response(self):
        """Test DocumentUploadResponse model."""
        response = DocumentUploadResponse(
            status="success",
            id="507f1f77bcf86cd799439011",
            filename="test.pdf",
            extractions=[{"type": "RentRollExtractor", "confidence": 0.95}],
        )
        assert response.status == "success"
        assert response.id == "507f1f77bcf86cd799439011"
        assert len(response.extractions) == 1

    def test_document_status_response(self):
        """Test DocumentStatusResponse model."""
        response = DocumentStatusResponse(
            status=ProcessingStatus.COMPLETED,
            extractions=[{"type": "RentRollExtractor", "confidence": 0.95}],
        )
        assert response.status == ProcessingStatus.COMPLETED
        assert response.extractions[0]["confidence"] == 0.95

    def test_financial_metrics(self):
        """Test FinancialMetrics model."""
        metrics = FinancialMetrics(
            noi=851250,
            capRate=0.0685,
            dscr=1.35,
            ltv=72.5,
            occupancyRate=94.5,
        )
        assert metrics.noi == 851250
        assert metrics.capRate == 0.0685
        assert metrics.dscr == 1.35
        assert metrics.ltv == 72.5
        assert metrics.occupancyRate == 94.5

    def test_financial_metrics_with_optional(self):
        """Test FinancialMetrics with optional fields."""
        metrics = FinancialMetrics(
            noi=851250,
            capRate=0.0685,
            dscr=1.35,
            ltv=72.5,
            occupancyRate=94.5,
            grossIncome=1275000,
            totalExpenses=423750,
            expenseRatio=33.24,
            debtYield=11.35,
        )
        assert metrics.grossIncome == 1275000
        assert metrics.debtYield == 11.35

    def test_confidence_scores(self):
        """Test ConfidenceScores model."""
        scores = ConfidenceScores(
            overall=0.95,
            fields={"noi": 0.98, "occupancy": 0.92},
        )
        assert scores.overall == 0.95
        assert scores.fields["noi"] == 0.98

    def test_confidence_scores_validation(self):
        """Test ConfidenceScores validation."""
        with pytest.raises(ValidationError):
            ConfidenceScores(overall=1.5)  # > 1.0

        with pytest.raises(ValidationError):
            ConfidenceScores(overall=-0.5)  # < 0
