"""
Base extractor class that defines the interface for all document extractors.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseExtractor(ABC):
    """Base class for document extractors."""
    
    def __init__(self):
        """Initialize the extractor."""
        self.confidence_scores: Dict[str, float] = {}
        self.extracted_data: Dict[str, Any] = {}
        self.validation_errors: List[str] = []
        
    @abstractmethod
    def can_handle(self, content: str, filename: str) -> bool:
        """
        Determine if this extractor can handle the given document.
        
        Args:
            content: The text content of the document
            filename: The name of the file
            
        Returns:
            bool: True if this extractor can handle the document
        """
        pass
    
    @abstractmethod
    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract data from the document content.
        
        Args:
            content: The text content of the document
            
        Returns:
            Dict[str, Any]: Extracted data
        """
        pass
    
    def validate(self) -> bool:
        """
        Validate the extracted data.
        
        Returns:
            bool: True if validation passed
        """
        self.validation_errors = []
        return len(self.validation_errors) == 0
    
    def get_confidence_scores(self) -> Dict[str, float]:
        """
        Get confidence scores for extracted fields.
        
        Returns:
            Dict[str, float]: Field-level confidence scores
        """
        return self.confidence_scores
    
    def calculate_field_confidence(self, field: str, value: Any) -> float:
        """
        Calculate confidence score for a specific field.
        
        Args:
            field: The field name
            value: The extracted value
            
        Returns:
            float: Confidence score between 0 and 1
        """
        # Base implementation - override for specific confidence calculations
        if value is None:
            return 0.0
        return 1.0
    
    def get_result(self) -> Dict[str, Any]:
        """
        Get the final extraction result with metadata.
        
        Returns:
            Dict[str, Any]: Extraction result with metadata
        """
        return {
            "data": self.extracted_data,
            "confidence_scores": self.confidence_scores,
            "validation_errors": self.validation_errors,
            "timestamp": datetime.now().isoformat(),
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
