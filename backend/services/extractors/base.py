"""
Base extractor class that defines the interface for all document extractors.
Includes market data integration and enhanced validation capabilities.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class RiskProfile(Enum):
    """Risk profile classification."""
    CORE = "core"
    VALUE_ADD = "valueAdd"
    OPPORTUNISTIC = "opportunistic"

class BaseExtractor(ABC):
    """Base class for document extractors with enhanced validation and market integration."""
    
    def __init__(self):
        """Initialize the extractor with enhanced tracking."""
        self.confidence_scores: Dict[str, float] = {}
        self.extracted_data: Dict[str, Any] = {}
        self.validation_errors: List[str] = []
        self.market_data: Dict[str, Any] = {}
        self.risk_factors: Dict[str, float] = {}
        self.processing_metadata: Dict[str, Any] = {
            "start_time": datetime.now().isoformat(),
            "version": "2.0.0",
            "validation_rules_applied": []
        }
        
    @abstractmethod
    def can_handle(self, content: str, filename: str) -> Tuple[bool, float]:
        """
        Determine if this extractor can handle the given document with confidence score.
        
        Args:
            content: The text content of the document
            filename: The name of the file
            
        Returns:
            Tuple[bool, float]: (Can handle, confidence score)
        """
        pass
    
    @abstractmethod
    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract data from the document content with enhanced validation.
        
        Args:
            content: The text content of the document
            
        Returns:
            Dict[str, Any]: Extracted data with validation metadata
        """
        pass

    def fetch_market_data(self, property_type: str, location: str) -> Dict[str, Any]:
        """
        Fetch relevant market data for validation and enrichment.
        
        Args:
            property_type: Type of property
            location: Property location
            
        Returns:
            Dict[str, Any]: Market data for comparison
        """
        try:
            # TODO: Implement market data fetching from the market-data package
            # This is a placeholder for the actual implementation
            self.market_data = {
                "property_type": property_type,
                "location": location,
                "timestamp": datetime.now().isoformat()
            }
            return self.market_data
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return {}

    def assess_risk_profile(self) -> RiskProfile:
        """
        Assess the risk profile based on extracted data and market conditions.
        
        Returns:
            RiskProfile: Assessed risk profile
        """
        try:
            # Calculate risk factors
            self.risk_factors = {
                "market_risk": self._calculate_market_risk(),
                "property_risk": self._calculate_property_risk(),
                "financial_risk": self._calculate_financial_risk(),
                "tenant_risk": self._calculate_tenant_risk()
            }
            
            # Calculate weighted average risk score
            weights = {"market_risk": 0.3, "property_risk": 0.2, 
                      "financial_risk": 0.3, "tenant_risk": 0.2}
            total_risk = sum(score * weights[factor] 
                           for factor, score in self.risk_factors.items())
            
            # Classify risk profile
            if total_risk < 0.3:
                return RiskProfile.CORE
            elif total_risk < 0.6:
                return RiskProfile.VALUE_ADD
            else:
                return RiskProfile.OPPORTUNISTIC
                
        except Exception as e:
            logger.error(f"Error assessing risk profile: {str(e)}")
            return RiskProfile.VALUE_ADD  # Default to middle risk profile
    
    def validate(self) -> bool:
        """
        Enhanced validation with market data comparison.
        
        Returns:
            bool: True if validation passed
        """
        self.validation_errors = []
        
        try:
            # Basic data validation
            self._validate_required_fields()
            self._validate_data_formats()
            self._validate_data_ranges()
            
            # Market-based validation
            if self.market_data:
                self._validate_against_market_data()
            
            # Record validation metadata
            self.processing_metadata["validation_completed"] = datetime.now().isoformat()
            self.processing_metadata["validation_success"] = len(self.validation_errors) == 0
            
            return len(self.validation_errors) == 0
            
        except Exception as e:
            logger.error(f"Error in validation: {str(e)}")
            self.validation_errors.append(f"Validation error: {str(e)}")
            return False
    
    def get_confidence_scores(self) -> Dict[str, Any]:
        """
        Get enhanced confidence scores with metadata.
        
        Returns:
            Dict[str, Any]: Detailed confidence analysis
        """
        return {
            "field_scores": self.confidence_scores,
            "overall_score": self._calculate_overall_confidence(),
            "market_validation_score": self._calculate_market_validation_score(),
            "risk_factors": self.risk_factors,
            "metadata": {
                "calculation_time": datetime.now().isoformat(),
                "market_data_used": bool(self.market_data)
            }
        }
    
    def calculate_field_confidence(self, field: str, value: Any, expected_range: Optional[Tuple[float, float]] = None) -> float:
        """
        Enhanced confidence calculation with market data comparison.
        
        Args:
            field: The field name
            value: The extracted value
            expected_range: Optional range for numerical values
            
        Returns:
            float: Confidence score between 0 and 1
        """
        try:
            if value is None:
                return 0.0
                
            base_score = self._calculate_base_confidence(field, value)
            format_score = self._calculate_format_confidence(field, value)
            range_score = self._calculate_range_confidence(field, value, expected_range)
            market_score = self._calculate_market_alignment(field, value)
            
            # Weighted average of scores
            weights = {
                "base": 0.3,
                "format": 0.2,
                "range": 0.2,
                "market": 0.3
            }
            
            final_score = (
                base_score * weights["base"] +
                format_score * weights["format"] +
                range_score * weights["range"] +
                market_score * weights["market"]
            )
            
            return round(final_score, 3)
            
        except Exception as e:
            logger.error(f"Error calculating confidence for {field}: {str(e)}")
            return 0.0
    
    def get_result(self) -> Dict[str, Any]:
        """
        Get enhanced extraction result with comprehensive metadata.
        
        Returns:
            Dict[str, Any]: Detailed extraction result
        """
        end_time = datetime.now()
        self.processing_metadata["end_time"] = end_time.isoformat()
        self.processing_metadata["processing_time"] = (
            end_time - datetime.fromisoformat(self.processing_metadata["start_time"])
        ).total_seconds()
        
        return {
            "data": self.extracted_data,
            "confidence_analysis": self.get_confidence_scores(),
            "validation": {
                "errors": self.validation_errors,
                "passed": len(self.validation_errors) == 0,
                "rules_applied": self.processing_metadata["validation_rules_applied"]
            },
            "risk_profile": self.assess_risk_profile().value,
            "risk_factors": self.risk_factors,
            "market_data": self.market_data,
            "metadata": self.processing_metadata,
            "success": len(self.validation_errors) == 0
        }
    
    def extract_number(self, text: str, default: Optional[float] = None) -> Optional[float]:
        """
        Extract a number from text, handling various formats.
        
        Args:
            text: The text to extract from
            default: Default value if extraction fails
            
        Returns:
            Optional[float]: Extracted number or default
        """
        import re
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[^\d.-]', '', text)
            return float(cleaned)
        except (ValueError, TypeError):
            return default
    
    def extract_percentage(self, text: str, default: Optional[float] = None) -> Optional[float]:
        """
        Extract a percentage from text.
        
        Args:
            text: The text to extract from
            default: Default value if extraction fails
            
        Returns:
            Optional[float]: Extracted percentage or default
        """
        import re
        try:
            # Find number followed by % symbol
            match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
            if match:
                return float(match.group(1))
            return default
        except (ValueError, TypeError):
            return default
    
    def extract_date(self, text: str, default: Optional[str] = None) -> Optional[str]:
        """
        Extract a date from text in ISO format.
        
        Args:
            text: The text to extract from
            default: Default value if extraction fails
            
        Returns:
            Optional[str]: Extracted date in ISO format or default
        """
        from dateutil.parser import parse
        try:
            date = parse(text)
            return date.date().isoformat()
        except (ValueError, TypeError):
            return default
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: The text to clean
            
        Returns:
            str: Cleaned text
        """
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Convert to lowercase
        text = text.lower()
        return text

    def _calculate_market_risk(self) -> float:
        """Calculate market risk score based on market data."""
        try:
            if not self.market_data:
                return 0.5  # Default to medium risk if no market data
                
            risk_score = 0.0
            factors = {
                "vacancy_trend": 0.3,
                "rent_growth": 0.3,
                "absorption": 0.2,
                "new_supply": 0.2
            }
            
            # Placeholder logic - implement actual calculations based on market data
            risk_score = 0.5  # Default medium risk
            
            return round(risk_score, 3)
        except Exception as e:
            logger.error(f"Error calculating market risk: {str(e)}")
            return 0.5

    def _calculate_property_risk(self) -> float:
        """Calculate property-specific risk score."""
        try:
            risk_score = 0.0
            factors = {
                "age": 0.25,
                "location": 0.25,
                "condition": 0.25,
                "amenities": 0.25
            }
            
            # Placeholder logic - implement based on extracted data
            risk_score = 0.5  # Default medium risk
            
            return round(risk_score, 3)
        except Exception as e:
            logger.error(f"Error calculating property risk: {str(e)}")
            return 0.5

    def _calculate_financial_risk(self) -> float:
        """Calculate financial risk score."""
        try:
            risk_score = 0.0
            factors = {
                "dscr": 0.3,
                "ltv": 0.3,
                "occupancy": 0.2,
                "tenant_credit": 0.2
            }
            
            # Placeholder logic - implement based on extracted data
            risk_score = 0.5  # Default medium risk
            
            return round(risk_score, 3)
        except Exception as e:
            logger.error(f"Error calculating financial risk: {str(e)}")
            return 0.5

    def _calculate_tenant_risk(self) -> float:
        """Calculate tenant risk score."""
        try:
            risk_score = 0.0
            factors = {
                "credit_quality": 0.3,
                "lease_term": 0.3,
                "industry": 0.2,
                "concentration": 0.2
            }
            
            # Placeholder logic - implement based on extracted data
            risk_score = 0.5  # Default medium risk
            
            return round(risk_score, 3)
        except Exception as e:
            logger.error(f"Error calculating tenant risk: {str(e)}")
            return 0.5

    def _validate_required_fields(self) -> None:
        """Validate presence of required fields."""
        required_fields = self._get_required_fields()
        for field in required_fields:
            if field not in self.extracted_data:
                self.validation_errors.append(f"Missing required field: {field}")

    def _validate_data_formats(self) -> None:
        """Validate data formats for extracted fields."""
        format_rules = self._get_format_rules()
        for field, rule in format_rules.items():
            if field in self.extracted_data:
                if not rule.match(str(self.extracted_data[field])):
                    self.validation_errors.append(f"Invalid format for {field}")

    def _validate_data_ranges(self) -> None:
        """Validate numerical ranges for applicable fields."""
        range_rules = self._get_range_rules()
        for field, (min_val, max_val) in range_rules.items():
            if field in self.extracted_data:
                value = self.extracted_data[field]
                if not min_val <= value <= max_val:
                    self.validation_errors.append(
                        f"Value for {field} ({value}) outside valid range [{min_val}, {max_val}]"
                    )

    def _validate_against_market_data(self) -> None:
        """Validate extracted data against market data."""
        if not self.market_data:
            return
            
        # Example validation rules
        if "noi" in self.extracted_data and "market_noi_range" in self.market_data:
            noi = self.extracted_data["noi"]
            min_noi, max_noi = self.market_data["market_noi_range"]
            if not min_noi <= noi <= max_noi:
                self.validation_errors.append(
                    f"NOI ({noi}) outside market range [{min_noi}, {max_noi}]"
                )

    def _calculate_base_confidence(self, field: str, value: Any) -> float:
        """Calculate base confidence score for a field."""
        if value is None:
            return 0.0
        return 1.0  # Override in specific extractors

    def _calculate_format_confidence(self, field: str, value: Any) -> float:
        """Calculate format-based confidence score."""
        try:
            format_rules = self._get_format_rules()
            if field in format_rules:
                return 1.0 if format_rules[field].match(str(value)) else 0.0
            return 1.0
        except Exception:
            return 0.0

    def _calculate_range_confidence(self, field: str, value: Any, expected_range: Optional[Tuple[float, float]]) -> float:
        """Calculate range-based confidence score."""
        try:
            if expected_range and isinstance(value, (int, float)):
                min_val, max_val = expected_range
                if min_val <= value <= max_val:
                    return 1.0
                # Calculate distance from valid range
                distance = min(abs(value - min_val), abs(value - max_val))
                range_size = max_val - min_val
                return max(0, 1 - (distance / range_size))
            return 1.0
        except Exception:
            return 0.0

    def _calculate_market_alignment(self, field: str, value: Any) -> float:
        """Calculate market alignment confidence score."""
        try:
            if not self.market_data:
                return 1.0
                
            # Example market alignment check
            if field in self.market_data:
                market_value = self.market_data[field]
                if isinstance(value, (int, float)) and isinstance(market_value, (int, float)):
                    diff_percent = abs(value - market_value) / market_value
                    return max(0, 1 - diff_percent)
            return 1.0
        except Exception:
            return 0.0

    def _calculate_overall_confidence(self) -> float:
        """Calculate overall confidence score."""
        if not self.confidence_scores:
            return 0.0
        return round(sum(self.confidence_scores.values()) / len(self.confidence_scores), 3)

    def _calculate_market_validation_score(self) -> float:
        """Calculate market validation confidence score."""
        try:
            if not self.market_data:
                return 1.0
                
            validation_scores = []
            for field in self.extracted_data:
                if field in self.market_data:
                    validation_scores.append(
                        self._calculate_market_alignment(field, self.extracted_data[field])
                    )
            
            if not validation_scores:
                return 1.0
                
            return round(sum(validation_scores) / len(validation_scores), 3)
        except Exception:
            return 1.0

    @abstractmethod
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for this extractor."""
        pass

    @abstractmethod
    def _get_format_rules(self) -> Dict[str, Any]:
        """Get format validation rules for this extractor."""
        pass

    @abstractmethod
    def _get_range_rules(self) -> Dict[str, Tuple[float, float]]:
        """Get numerical range rules for this extractor."""
        pass
