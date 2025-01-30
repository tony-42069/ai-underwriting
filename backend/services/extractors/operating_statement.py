"""
Specialized extractor for operating statements.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from .base import BaseExtractor
from .rent_roll import RentRollExtractor
from .pl_statement import PLStatementExtractor

logger = logging.getLogger(__name__)

class OperatingStatementExtractor(BaseExtractor):
    """
    Extracts data from operating statements, which often combine
    elements of both rent rolls and P&L statements.
    """
    
    def __init__(self):
        """Initialize the operating statement extractor."""
        super().__init__()
        self.rent_roll_extractor = RentRollExtractor()
        self.pl_extractor = PLStatementExtractor()
        
    def can_handle(self, content: str, filename: str) -> bool:
        """
        Determine if this is an operating statement.
        
        Args:
            content: Document content
            filename: Name of the file
            
        Returns:
            bool: True if this is an operating statement
        """
        # Check filename
        filename_indicators = [
            'operating', 'statement', 'performance', 'actual'
        ]
        if any(term in filename.lower() for term in filename_indicators):
            return True
            
        # Check content for operating statement indicators
        indicators = [
            r'operating\s*statement',
            r'property\s*performance',
            r'actual\s*vs\s*budget',
            r'variance\s*report',
            r'year\s*to\s*date'
        ]
        
        content_lower = content.lower()
        return any(re.search(pattern, content_lower) for pattern in indicators)
    
    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract data from operating statement content.
        
        Args:
            content: Document content
            
        Returns:
            Dict[str, Any]: Extracted operating statement data
        """
        try:
            # Extract period information
            period_info = self._extract_period_info(content)
            
            # Try to extract rent roll data if present
            rent_roll_data = None
            if self.rent_roll_extractor.can_handle(content, ""):
                rent_roll_result = self.rent_roll_extractor.extract(content)
                if rent_roll_result["success"]:
                    rent_roll_data = rent_roll_result["data"]
            
            # Extract P&L data
            pl_result = self.pl_extractor.extract(content)
            pl_data = pl_result["data"] if pl_result["success"] else None
            
            # Extract budget and variance data
            budget_data = self._extract_budget_data(content)
            
            # Store extracted data
            self.extracted_data = {
                "period": period_info,
                "financial_data": pl_data,
                "occupancy_data": rent_roll_data["summary"] if rent_roll_data else None,
                "budget_comparison": budget_data,
                "metrics": self._calculate_metrics(pl_data, rent_roll_data, budget_data)
            }
            
            # Calculate confidence scores
            self._calculate_confidence_scores(pl_result, rent_roll_result)
            
            # Validate extracted data
            self.validate()
            
            return self.get_result()
            
        except Exception as e:
            logger.error(f"Error extracting operating statement data: {str(e)}")
            self.validation_errors.append(f"Extraction error: {str(e)}")
            return self.get_result()
    
    def _extract_period_info(self, content: str) -> Dict[str, Any]:
        """Extract reporting period information."""
        period_info = {
            "start_date": None,
            "end_date": None,
            "period_type": None  # monthly, quarterly, annual
        }
        
        # Look for date ranges
        date_range_patterns = [
            r'period(?:\s+from)?\s+(\w+\s+\d{1,2},?\s+\d{4})\s+(?:to|through)\s+(\w+\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{2,4})\s*-\s*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'(?:as\s+of\s+)?(\w+\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in date_range_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    period_info["start_date"] = self.extract_date(match.group(1))
                    period_info["end_date"] = self.extract_date(match.group(2))
                else:
                    period_info["end_date"] = self.extract_date(match.group(1))
                break
        
        # Determine period type
        if period_info["start_date"] and period_info["end_date"]:
            try:
                start = datetime.strptime(period_info["start_date"], "%Y-%m-%d")
                end = datetime.strptime(period_info["end_date"], "%Y-%m-%d")
                days = (end - start).days
                
                if days <= 31:
                    period_info["period_type"] = "monthly"
                elif days <= 92:
                    period_info["period_type"] = "quarterly"
                else:
                    period_info["period_type"] = "annual"
            except ValueError:
                pass
        
        return period_info
    
    def _extract_budget_data(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract budget and variance information."""
        budget_data = {
            "items": [],
            "total_variance": 0.0,
            "variance_percentage": 0.0
        }
        
        # Look for budget comparison section
        budget_section = self._extract_section(content,
            start_patterns=[
                r'budget\s*comparison',
                r'variance\s*analysis',
                r'actual\s*vs\s*budget'
            ],
            end_patterns=[
                r'notes',
                r'summary',
                r'end\s*of\s*report'
            ])
            
        if budget_section:
            # Process each line
            lines = budget_section.split('\n')
            for line in lines:
                # Look for lines with actual and budget amounts
                matches = re.findall(
                    r'([\w\s]+?)\s*\$?([\d,]+\.?\d*)\s*\$?([\d,]+\.?\d*)\s*\$?([-\d,]+\.?\d*)',
                    line
                )
                
                for match in matches:
                    description = match[0].strip()
                    actual = self.extract_number(match[1], 0)
                    budget = self.extract_number(match[2], 0)
                    variance = self.extract_number(match[3], 0)
                    
                    budget_data["items"].append({
                        "description": description,
                        "actual": actual,
                        "budget": budget,
                        "variance": variance,
                        "variance_percentage": (variance / budget * 100) if budget else 0
                    })
            
            # Calculate totals
            if budget_data["items"]:
                total_actual = sum(item["actual"] for item in budget_data["items"])
                total_budget = sum(item["budget"] for item in budget_data["items"])
                budget_data["total_variance"] = total_actual - total_budget
                budget_data["variance_percentage"] = (
                    (total_actual - total_budget) / total_budget * 100
                    if total_budget else 0
                )
        
        return budget_data if budget_data["items"] else None
    
    def _calculate_metrics(self, pl_data: Optional[Dict[str, Any]], 
                         rent_roll_data: Optional[Dict[str, Any]],
                         budget_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate key performance metrics."""
        metrics = {}
        
        if pl_data:
            summary = pl_data.get("summary", {})
            metrics.update({
                "noi": summary.get("noi", 0),
                "expense_ratio": summary.get("expense_ratio", 0)
            })
        
        if rent_roll_data:
            metrics.update({
                "occupancy_rate": rent_roll_data.get("occupancy_rate", 0),
                "avg_rent_psf": rent_roll_data.get("average_rent_psf", 0)
            })
        
        if budget_data:
            metrics.update({
                "budget_variance": budget_data.get("total_variance", 0),
                "budget_variance_percentage": budget_data.get("variance_percentage", 0)
            })
        
        return metrics
    
    def _calculate_confidence_scores(self, pl_result: Dict[str, Any], 
                                  rent_roll_result: Optional[Dict[str, Any]]):
        """Calculate confidence scores for extracted data."""
        scores = []
        
        # P&L confidence
        if pl_result["success"]:
            scores.append(pl_result["confidence_scores"]["overall"])
        
        # Rent roll confidence
        if rent_roll_result and rent_roll_result["success"]:
            scores.append(rent_roll_result["confidence_scores"]["overall"])
        
        # Budget data confidence
        if self.extracted_data.get("budget_comparison"):
            budget_confidence = 1.0 if len(self.extracted_data["budget_comparison"]["items"]) > 0 else 0.0
            scores.append(budget_confidence)
        
        # Period info confidence
        period_info = self.extracted_data.get("period", {})
        period_confidence = 1.0 if period_info.get("end_date") else 0.0
        scores.append(period_confidence)
        
        # Store confidence scores
        self.confidence_scores = {
            "pl_data": pl_result["confidence_scores"]["overall"] if pl_result["success"] else 0.0,
            "rent_roll_data": rent_roll_result["confidence_scores"]["overall"] if rent_roll_result and rent_roll_result["success"] else 0.0,
            "budget_data": budget_confidence if "budget_confidence" in locals() else 0.0,
            "period_info": period_confidence,
            "overall": sum(scores) / len(scores) if scores else 0.0
        }
    
    def _extract_section(self, content: str, start_patterns: List[str], end_patterns: List[str]) -> Optional[str]:
        """Extract a section of the document between start and end patterns."""
        content_lower = content.lower()
        
        # Find start of section
        start_pos = -1
        for pattern in start_patterns:
            match = re.search(pattern, content_lower)
            if match:
                start_pos = match.start()
                break
        
        if start_pos == -1:
            return None
        
        # Find end of section
        end_pos = len(content)
        for pattern in end_patterns:
            match = re.search(pattern, content_lower[start_pos:])
            if match:
                end_pos = start_pos + match.start()
                break
        
        return content[start_pos:end_pos]
    
    def validate(self) -> bool:
        """
        Validate the extracted operating statement data.
        
        Returns:
            bool: True if validation passed
        """
        self.validation_errors = []
        
        # Check for minimum required data
        if not self.extracted_data.get("financial_data"):
            self.validation_errors.append("No financial data extracted")
        
        # Validate period information
        period = self.extracted_data.get("period", {})
        if not period.get("end_date"):
            self.validation_errors.append("Missing reporting period end date")
        
        # Validate metrics
        metrics = self.extracted_data.get("metrics", {})
        if metrics.get("expense_ratio", 0) > 100:
            self.validation_errors.append("Invalid expense ratio > 100%")
        
        if metrics.get("occupancy_rate", 0) > 100:
            self.validation_errors.append("Invalid occupancy rate > 100%")
        
        # Validate budget comparisons
        budget_data = self.extracted_data.get("budget_comparison")
        if budget_data:
            for item in budget_data["items"]:
                if abs(item["variance"]) > max(item["actual"], item["budget"]):
                    self.validation_errors.append(
                        f"Suspicious variance for {item['description']}: {item['variance']}"
                    )
        
        return len(self.validation_errors) == 0
