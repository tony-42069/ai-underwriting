import pytest
from datetime import datetime
from backend.services.extractors.base import BaseExtractor


class ConcreteExtractor(BaseExtractor):
    """Concrete implementation of BaseExtractor for testing."""

    def can_handle(self, content: str, filename: str) -> bool:
        return "test" in content.lower()

    def extract(self, content: str) -> dict:
        self.extracted_data = {"content": content}
        return self.get_result()


class TestBaseExtractor:
    """Tests for BaseExtractor class."""

    def test_init(self):
        """Test extractor initialization."""
        extractor = ConcreteExtractor()
        assert extractor.confidence_scores == {}
        assert extractor.extracted_data == {}
        assert extractor.validation_errors == []

    def test_can_handle_not_implemented(self):
        """Test that can_handle must be implemented."""
        base = BaseExtractor()
        with pytest.raises(TypeError):
            base.can_handle("test", "test.txt")

    def test_extract_not_implemented(self):
        """Test that extract must be implemented."""
        base = BaseExtractor()
        with pytest.raises(TypeError):
            base.extract("test content")

    def test_validate_empty_errors(self):
        """Test validation with no errors."""
        extractor = ConcreteExtractor()
        extractor.validation_errors = []
        assert extractor.validate() is True

    def test_validate_with_errors(self):
        """Test validation with errors."""
        extractor = ConcreteExtractor()
        extractor.validation_errors = ["Error 1", "Error 2"]
        assert extractor.validate() is False
        assert len(extractor.validation_errors) == 2

    def test_get_confidence_scores(self):
        """Test getting confidence scores."""
        extractor = ConcreteExtractor()
        extractor.confidence_scores = {"field1": 0.9, "field2": 0.8}
        scores = extractor.get_confidence_scores()
        assert scores == {"field1": 0.9, "field2": 0.8}

    def test_calculate_field_confidence_with_value(self):
        """Test confidence calculation with a value present."""
        extractor = ConcreteExtractor()
        confidence = extractor.calculate_field_confidence("test_field", "value")
        assert confidence == 1.0

    def test_calculate_field_confidence_with_none(self):
        """Test confidence calculation with None value."""
        extractor = ConcreteExtractor()
        confidence = extractor.calculate_field_confidence("test_field", None)
        assert confidence == 0.0

    def test_get_result_success(self):
        """Test getting result when validation passes."""
        extractor = ConcreteExtractor()
        extractor.validation_errors = []
        extractor.extracted_data = {"key": "value"}
        extractor.confidence_scores = {"overall": 1.0}

        result = extractor.get_result()

        assert result["success"] is True
        assert result["data"] == {"key": "value"}
        assert result["confidence_scores"] == {"overall": 1.0}
        assert result["validation_errors"] == []
        assert "timestamp" in result

    def test_get_result_failure(self):
        """Test getting result when validation fails."""
        extractor = ConcreteExtractor()
        extractor.validation_errors = ["Error 1"]
        extractor.extracted_data = {}
        extractor.confidence_scores = {}

        result = extractor.get_result()

        assert result["success"] is False
        assert result["validation_errors"] == ["Error 1"]

    def test_extract_number_standard(self):
        """Test extracting standard number."""
        extractor = ConcreteExtractor()
        result = extractor.extract_number("1234.56")
        assert result == 1234.56

    def test_extract_number_with_currency(self):
        """Test extracting number with currency symbol."""
        extractor = ConcreteExtractor()
        result = extractor.extract_number("$1,234.56")
        assert result == 1234.56

    def test_extract_number_with_default(self):
        """Test extracting number with default value."""
        extractor = ConcreteExtractor()
        result = extractor.extract_number("invalid", default=42.0)
        assert result == 42.0

    def test_extract_number_invalid(self):
        """Test extracting number from invalid text."""
        extractor = ConcreteExtractor()
        result = extractor.extract_number("no numbers here")
        assert result is None

    def test_extract_percentage_standard(self):
        """Test extracting percentage."""
        extractor = ConcreteExtractor()
        result = extractor.extract_percentage("75.5%")
        assert result == 75.5

    def test_extract_percentage_with_space(self):
        """Test extracting percentage with space."""
        extractor = ConcreteExtractor()
        result = extractor.extract_percentage("50 %")
        assert result == 50.0

    def test_extract_percentage_no_percentage(self):
        """Test extracting percentage when no percentage exists."""
        extractor = ConcreteExtractor()
        result = extractor.extract_percentage("50", default=0.0)
        assert result == 0.0

    def test_extract_date_iso_format(self):
        """Test extracting date in ISO format."""
        extractor = ConcreteExtractor()
        result = extractor.extract_date("2024-01-15")
        assert result == "2024-01-15"

    def test_extract_date_us_format(self):
        """Test extracting date in US format."""
        extractor = ConcreteExtractor()
        result = extractor.extract_date("January 15, 2024")
        assert result == "2024-01-15"

    def test_extract_date_invalid(self):
        """Test extracting date from invalid text."""
        extractor = ConcreteExtractor()
        result = extractor.extract_date("not a date", default="2000-01-01")
        assert result == "2000-01-01"

    def test_clean_text(self):
        """Test cleaning and normalizing text."""
        extractor = ConcreteExtractor()
        result = extractor.clean_text("  Some   Text  \n  With  Whitespace  ")
        assert result == "some text with whitespace"

    def test_clean_text_empty(self):
        """Test cleaning empty text."""
        extractor = ConcreteExtractor()
        result = extractor.clean_text("")
        assert result == ""

    def test_concrete_extractor_can_handle(self):
        """Test concrete extractor can_handle method."""
        extractor = ConcreteExtractor()
        assert extractor.can_handle("This is a TEST", "file.txt") is True
        assert extractor.can_handle("No match here", "file.txt") is False

    def test_concrete_extractor_extract(self):
        """Test concrete extractor extract method."""
        extractor = ConcreteExtractor()
        result = extractor.extract("Test content")

        assert result["success"] is True
        assert result["data"]["content"] == "Test content"
        assert "timestamp" in result
