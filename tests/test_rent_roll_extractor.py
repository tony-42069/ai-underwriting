import pytest
from backend.services.extractors.rent_roll import RentRollExtractor


class TestRentRollExtractor:
    """Tests for RentRollExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create a RentRollExtractor instance."""
        return RentRollExtractor()

    def test_can_handle_by_filename(self, extractor):
        """Test detection by filename."""
        assert extractor.can_handle("Some content", "rent_roll_2024.pdf") is True
        assert extractor.can_handle("Some content", "tenant_schedule.xlsx") is True
        assert extractor.can_handle("Some content", "lease_schedule.docx") is True
        assert extractor.can_handle("Some content", "report.pdf") is False

    def test_can_handle_by_content(self, extractor):
        """Test detection by content."""
        content_with_indicators = """
        Unit    Tenant Name    Square Feet    Monthly Rent
        101     Test Corp      1,500          $3,500
        """
        assert extractor.can_handle(content_with_indicators, "document.pdf") is True

        content_without_indicators = "This is a regular document without any relevant terms."
        assert extractor.can_handle(content_without_indicators, "document.pdf") is False

    def test_extract_basic_rent_roll(self, extractor, sample_pdf_content):
        """Test extracting basic rent roll data."""
        result = extractor.extract(sample_pdf_content)

        assert result["success"] is True
        assert len(extractor.tenant_data) == 4
        assert extractor.extracted_data["summary"]["total_units"] == 4

    def test_extract_tenant_data(self, extractor, sample_pdf_content):
        """Test extracting individual tenant records."""
        result = extractor.extract(sample_pdf_content)

        tenants = extractor.tenant_data
        assert len(tenants) == 4

        first_tenant = tenants[0]
        assert first_tenant.get("unit") == "101"
        assert first_tenant.get("tenant") == "ABC Corporation"
        assert first_tenant.get("square_footage") == 1500
        assert first_tenant.get("current_rent") == 3500

    def test_extract_vacant_unit(self, extractor, sample_pdf_content):
        """Test identifying vacant units."""
        result = extractor.extract(sample_pdf_content)

        tenants = extractor.tenant_data
        vacant_tenant = next(
            (t for t in tenants if "Vacant" in t.get("tenant", "")), None
        )
        assert vacant_tenant is not None
        assert vacant_tenant.get("occupied") is False

    def test_extract_occupied_unit(self, extractor, sample_pdf_content):
        """Test identifying occupied units."""
        result = extractor.extract(sample_pdf_content)

        tenants = extractor.tenant_data
        occupied_tenants = [t for t in tenants if t.get("occupied", True)]
        assert len(occupied_tenants) == 3

    def test_summary_metrics(self, extractor, sample_pdf_content):
        """Test summary metrics calculation."""
        result = extractor.extract(sample_pdf_content)

        summary = extractor.extracted_data["summary"]
        assert summary["total_units"] == 4
        assert summary["occupancy_rate"] > 0
        assert summary["total_monthly_rent"] > 0

    def test_confidence_scores(self, extractor, sample_pdf_content):
        """Test confidence score calculation."""
        result = extractor.extract(sample_pdf_content)

        assert "overall" in extractor.confidence_scores
        assert 0 <= extractor.confidence_scores["overall"] <= 1

    def test_validation_no_errors(self, extractor, sample_pdf_content):
        """Test validation with valid data."""
        result = extractor.extract(sample_pdf_content)

        assert len(extractor.validation_errors) == 0
        assert result["success"] is True

    def test_validation_missing_unit(self, extractor):
        """Test validation fails for missing unit numbers."""
        content = """
        Unit    Tenant    Square Feet    Rent
                Corp      1,500          $3,500
        """
        result = extractor.extract(content)

        unit_errors = [
            e for e in extractor.validation_errors if "unit" in e.lower()
        ]
        assert len(unit_errors) > 0

    def test_validation_invalid_square_footage(self, extractor):
        """Test validation fails for invalid square footage."""
        content = """
        Unit    Tenant    Square Feet    Rent
        101     Corp      0              $3,500
        """
        result = extractor.extract(content)

        sf_errors = [
            e
            for e in extractor.validation_errors
            if "square footage" in e.lower()
        ]
        assert len(sf_errors) > 0

    def test_validation_invalid_rent(self, extractor):
        """Test validation fails for negative rent."""
        content = """
        Unit    Tenant    Square Feet    Rent
        101     Corp      1,500          $-500
        """
        result = extractor.extract(content)

        rent_errors = [e for e in extractor.validation_errors if "rent" in e.lower()]
        assert len(rent_errors) > 0

    def test_get_result_returns_correct_structure(self, extractor, sample_pdf_content):
        """Test get_result returns properly structured response."""
        result = extractor.extract(sample_pdf_content)
        final_result = extractor.get_result()

        assert "data" in final_result
        assert "confidence_scores" in final_result
        assert "validation_errors" in final_result
        assert "success" in final_result
        assert "timestamp" in final_result

    def test_extract_empty_content(self, extractor):
        """Test extraction with empty content."""
        result = extractor.extract("")

        assert result["success"] is False
        assert len(extractor.tenant_data) == 0

    def test_extract_no_matching_data(self, extractor):
        """Test extraction when no rent roll data matches."""
        content = "This is not a rent roll document at all."
        result = extractor.extract(content)

        assert result["success"] is False
        assert len(extractor.tenant_data) == 0

    def test_calculate_field_confidence(self, extractor):
        """Test field-level confidence calculation."""
        confidence = extractor.calculate_field_confidence("unit", "101")
        assert confidence == 1.0

        confidence = extractor.calculate_field_confidence("unit", None)
        assert confidence == 0.0

    def test_extract_date_helper(self, extractor):
        """Test date extraction helper method."""
        date = extractor.extract_date("January 15, 2024")
        assert date == "2024-01-15"

    def test_extract_number_helper(self, extractor):
        """Test number extraction helper method."""
        number = extractor.extract_number("$3,500.00")
        assert number == 3500.0

    def test_column_position_detection(self, extractor):
        """Test column position detection from header."""
        header = "Unit    Tenant Name    Square Feet    Monthly Rent    Lease Start    Lease End"
        positions = extractor._get_column_positions(header)

        assert "unit" in positions
        assert "tenant" in positions
        assert "square_footage" in positions
        assert "rent" in positions

    def test_parse_tenant_line(self, extractor):
        """Test parsing individual tenant line."""
        header = "Unit    Tenant    SF    Rent"
        positions = extractor._get_column_positions(header)

        line = "101     Corp      1500  3500"
        tenant = extractor._parse_tenant_line(line, positions)

        assert tenant is not None
        assert tenant.get("unit") == "101"
        assert tenant.get("tenant") == "Corp"
        assert tenant.get("square_footage") == 1500
        assert tenant.get("current_rent") == 3500

    def test_parse_empty_line(self, extractor):
        """Test parsing empty line returns None."""
        positions = {"unit": (0, 10), "tenant": (10, 30)}
        result = extractor._parse_tenant_line("", positions)
        assert result is None

    def test_parse_whitespace_line(self, extractor):
        """Test parsing whitespace-only line returns None."""
        positions = {"unit": (0, 10)}
        result = extractor._parse_tenant_line("   ", positions)
        assert result is None
