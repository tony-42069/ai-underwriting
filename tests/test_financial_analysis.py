import pytest
from backend.services.financial_analysis import FinancialAnalysis


class TestFinancialAnalysis:
    """Tests for FinancialAnalysis class."""

    def test_extract_numbers(self):
        """Test extracting numbers from text."""
        text = "Revenue: $1,234,567.89 and expenses: $500,000.00"
        numbers = FinancialAnalysis.extract_numbers(text)

        assert 1234567.89 in numbers
        assert 500000.00 in numbers

    def test_extract_numbers_with_various_formats(self):
        """Test extracting numbers with various formats."""
        text = "Numbers: 100, 1,000, 1000.50, $.75"
        numbers = FinancialAnalysis.extract_numbers(text)

        assert 100 in numbers
        assert 1000 in numbers
        assert 1000.50 in numbers

    def test_extract_numbers_empty(self):
        """Test extracting numbers from empty text."""
        numbers = FinancialAnalysis.extract_numbers("")
        assert numbers == []

    def test_find_noi_explicit(self):
        """Test extracting NOI with explicit label."""
        text = "NOI: $500,000"
        noi = FinancialAnalysis.find_noi(text)
        assert noi == 500000

    def test_find_noi_full_label(self):
        """Test extracting NOI with full label."""
        text = "Net Operating Income: $750,000.00"
        noi = FinancialAnalysis.find_noi(text)
        assert noi == 750000

    def test_find_noi_not_found(self):
        """Test when NOI is not found."""
        text = "This document has no NOI information"
        noi = FinancialAnalysis.find_noi(text)
        assert noi is None

    def test_find_occupancy_percentage(self):
        """Test extracting occupancy rate."""
        text = "Current Occupancy: 95.5%"
        occupancy = FinancialAnalysis.find_occupancy(text)
        assert occupancy == 95.5

    def test_find_occupancy_alternative_label(self):
        """Test extracting occupancy with alternative label."""
        text = "Units Occupied: 92%"
        occupancy = FinancialAnalysis.find_occupancy(text)
        assert occupancy == 92

    def test_find_occupancy_not_found(self):
        """Test when occupancy is not found."""
        text = "No occupancy data in this document"
        occupancy = FinancialAnalysis.find_occupancy(text)
        assert occupancy is None

    def test_calculate_dscr_normal(self):
        """Test DSCR calculation with normal values."""
        dscr = FinancialAnalysis.calculate_dscr(noi=500000, debt_service=400000)
        assert dscr == 1.25

    def test_calculate_dscr_zero_debt_service(self):
        """Test DSCR calculation with zero debt service."""
        dscr = FinancialAnalysis.calculate_dscr(noi=500000, debt_service=0)
        assert dscr == 0.0

    def test_calculate_dscr_no_debt_service(self):
        """Test DSCR calculation with None debt service."""
        dscr = FinancialAnalysis.calculate_dscr(noi=500000, debt_service=None)
        assert dscr == 0.0

    def test_calculate_cap_rate_normal(self):
        """Test cap rate calculation."""
        cap_rate = FinancialAnalysis.calculate_cap_rate(noi=500000, property_value=10000000)
        assert cap_rate == 5.0

    def test_calculate_cap_rate_zero_property_value(self):
        """Test cap rate calculation with zero property value."""
        cap_rate = FinancialAnalysis.calculate_cap_rate(noi=500000, property_value=0)
        assert cap_rate == 0.0

    def test_calculate_cap_rate_none_property_value(self):
        """Test cap rate calculation with None property value."""
        cap_rate = FinancialAnalysis.calculate_cap_rate(noi=500000, property_value=None)
        assert cap_rate == 0.0

    def test_calculate_ltv_normal(self):
        """Test LTV calculation."""
        ltv = FinancialAnalysis.calculate_ltv(loan_amount=7500000, property_value=10000000)
        assert ltv == 75.0

    def test_calculate_ltv_zero_property_value(self):
        """Test LTV calculation with zero property value."""
        ltv = FinancialAnalysis.calculate_ltv(loan_amount=7500000, property_value=0)
        assert ltv == 0.0

    def test_calculate_ltv_none_property_value(self):
        """Test LTV calculation with None property value."""
        ltv = FinancialAnalysis.calculate_ltv(loan_amount=7500000, property_value=None)
        assert ltv == 0.0

    @pytest.mark.asyncio
    async def test_analyze_document_basic(self):
        """Test basic document analysis."""
        ocr_result = {
            "text": """
            Net Operating Income: $500,000
            Occupancy: 95%
            Property Value: $10,000,000
            Loan Amount: $7,500,000
            Annual Debt Service: $400,000
            """,
            "status": "success"
        }

        result = await FinancialAnalysis.analyze_document(ocr_result)

        assert "noi" in result
        assert "capRate" in result
        assert "dscr" in result
        assert "ltv" in result
        assert "occupancyRate" in result

    @pytest.mark.asyncio
    async def test_analyze_document_missing_data(self):
        """Test analysis with missing OCR data."""
        ocr_result = {
            "text": "This document has minimal data",
            "status": "success"
        }

        result = await FinancialAnalysis.analyze_document(ocr_result)

        assert "noi" in result
        assert result["noi"] is not None
        assert "capRate" in result
        assert "dscr" in result
        assert "ltv" in result
        assert "occupancyRate" in result

    @pytest.mark.asyncio
    async def test_analyze_document_empty_text(self):
        """Test analysis with empty text."""
        ocr_result = {
            "text": "",
            "status": "success"
        }

        result = await FinancialAnalysis.analyze_document(ocr_result)

        assert "noi" in result
        assert "capRate" in result
        assert "dscr" in result
        assert "ltv" in result
        assert "occupancyRate" in result

    @pytest.mark.asyncio
    async def test_analyze_document_no_text_key(self):
        """Test analysis when text key is missing."""
        ocr_result = {
            "status": "success"
        }

        result = await FinancialAnalysis.analyze_document(ocr_result)

        assert "noi" in result
        assert "capRate" in result

    def test_metric_calculations_comprehensive(self):
        """Test comprehensive metric calculations."""
        noi = 850000
        property_value = 10000000
        loan_amount = 7000000
        debt_service = 350000

        dscr = FinancialAnalysis.calculate_dscr(noi, debt_service)
        cap_rate = FinancialAnalysis.calculate_cap_rate(noi, property_value)
        ltv = FinancialAnalysis.calculate_ltv(loan_amount, property_value)

        assert dscr == pytest.approx(2.4286, rel=0.01)
        assert cap_rate == pytest.approx(8.5, rel=0.01)
        assert ltv == 70.0

    def test_extract_numbers_with_parentheses(self):
        """Test extracting numbers in parentheses (negative values)."""
        text = "Loss: ($50,000) Profit: $100,000"
        numbers = FinancialAnalysis.extract_numbers(text)

        assert 50000 in numbers or -50000 in numbers
        assert 100000 in numbers

    def test_find_noi_multiple_occurrences(self):
        """Test extracting NOI when it appears multiple times."""
        text = "Projected NOI: $500,000 Actual NOI: $450,000"
        noi = FinancialAnalysis.find_noi(text)
        assert noi == 500000

    def test_find_occupancy_decimal(self):
        """Test extracting decimal occupancy rate."""
        text = "Occupancy Rate: 94.25%"
        occupancy = FinancialAnalysis.find_occupancy(text)
        assert occupancy == 94.25
