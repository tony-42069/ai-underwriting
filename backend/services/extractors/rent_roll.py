"""
Specialized extractor for rent roll documents.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from .base import BaseExtractor

logger = logging.getLogger(__name__)

class RentRollExtractor(BaseExtractor):
    """Extracts tenant and lease information from rent roll documents."""
    
    def __init__(self):
        """Initialize the rent roll extractor."""
        super().__init__()
        self.tenant_data: List[Dict[str, Any]] = []
        
    def can_handle(self, content: str, filename: str) -> bool:
        """
        Determine if this is a rent roll document.
        
        Args:
            content: Document content
            filename: Name of the file
            
        Returns:
            bool: True if this is a rent roll
        """
        # Check filename
        if any(term in filename.lower() for term in ['rent', 'roll', 'tenant']):
            return True
            
        # Check content for rent roll indicators
        indicators = [
            r'rent\s*roll',
            r'tenant\s*schedule',
            r'lease\s*schedule',
            r'unit\s*number',
            r'tenant\s*name',
            r'monthly\s*rent'
        ]
        
        content_lower = content.lower()
        return any(re.search(pattern, content_lower) for pattern in indicators)
    
    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract data from rent roll content.
        
        Args:
            content: Document content
            
        Returns:
            Dict[str, Any]: Extracted rent roll data
        """
        try:
            # Extract tenants
            self.tenant_data = self._extract_tenants(content)
            
            # Calculate summary metrics
            total_sf = sum(t.get('square_footage', 0) for t in self.tenant_data)
            total_rent = sum(t.get('current_rent', 0) for t in self.tenant_data)
            occupied_sf = sum(t.get('square_footage', 0) for t in self.tenant_data if t.get('occupied', True))
            
            # Store extracted data
            self.extracted_data = {
                "tenants": self.tenant_data,
                "summary": {
                    "total_units": len(self.tenant_data),
                    "total_square_footage": total_sf,
                    "occupied_square_footage": occupied_sf,
                    "occupancy_rate": (occupied_sf / total_sf * 100) if total_sf > 0 else 0,
                    "total_monthly_rent": total_rent,
                    "average_rent_psf": (total_rent * 12 / total_sf) if total_sf > 0 else 0
                }
            }
            
            # Calculate confidence scores
            self._calculate_confidence_scores()
            
            # Validate extracted data
            self.validate()
            
            return self.get_result()
            
        except Exception as e:
            logger.error(f"Error extracting rent roll data: {str(e)}")
            self.validation_errors.append(f"Extraction error: {str(e)}")
            return self.get_result()
    
    def _extract_tenants(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract individual tenant records from the content.
        
        Args:
            content: Document content
            
        Returns:
            List[Dict[str, Any]]: List of tenant records
        """
        tenants = []
        
        # Split content into lines
        lines = content.split('\n')
        
        # Find header line to determine column positions
        header_line = self._find_header_line(lines)
        if not header_line:
            logger.warning("Could not find header line in rent roll")
            return tenants
            
        # Get column positions
        columns = self._get_column_positions(header_line)
        
        # Process each line after the header
        processing = False
        for line in lines:
            if line.strip() == header_line.strip():
                processing = True
                continue
                
            if processing and line.strip():
                tenant = self._parse_tenant_line(line, columns)
                if tenant:
                    tenants.append(tenant)
        
        return tenants
    
    def _find_header_line(self, lines: List[str]) -> Optional[str]:
        """Find the header line in the document."""
        header_indicators = [
            'unit', 'tenant', 'square feet', 'sf', 'rent', 'lease'
        ]
        
        for line in lines:
            line_lower = line.lower()
            if sum(1 for ind in header_indicators if ind in line_lower) >= 3:
                return line
        return None
    
    def _get_column_positions(self, header: str) -> Dict[str, Tuple[int, int]]:
        """
        Get the start and end positions of each column.
        
        Args:
            header: Header line from the document
            
        Returns:
            Dict[str, Tuple[int, int]]: Column positions
        """
        # Common column headers and their variations
        columns = {
            'unit': ['unit', 'suite', 'space'],
            'tenant': ['tenant', 'occupant', 'customer'],
            'square_footage': ['sf', 'sqft', 'square feet', 'size'],
            'rent': ['rent', 'rate', 'amount'],
            'start_date': ['start', 'commence', 'begin'],
            'end_date': ['end', 'expir', 'term'],
            'security_deposit': ['deposit', 'security']
        }
        
        positions = {}
        header_lower = header.lower()
        
        # Find positions for each column
        for col_name, variations in columns.items():
            for var in variations:
                pos = header_lower.find(var)
                if pos != -1:
                    # Estimate column width based on typical field sizes
                    width = {
                        'unit': 10,
                        'tenant': 30,
                        'square_footage': 15,
                        'rent': 15,
                        'start_date': 12,
                        'end_date': 12,
                        'security_deposit': 15
                    }.get(col_name, 20)
                    
                    positions[col_name] = (pos, pos + width)
                    break
        
        return positions
    
    def _parse_tenant_line(self, line: str, columns: Dict[str, Tuple[int, int]]) -> Optional[Dict[str, Any]]:
        """
        Parse a line of tenant data using column positions.
        
        Args:
            line: Line of text to parse
            columns: Column positions
            
        Returns:
            Optional[Dict[str, Any]]: Parsed tenant data
        """
        if not line.strip():
            return None
            
        tenant = {}
        
        try:
            for col_name, (start, end) in columns.items():
                if start < len(line):
                    value = line[start:min(end, len(line))].strip()
                    
                    if col_name in ['square_footage', 'rent', 'security_deposit']:
                        tenant[col_name] = self.extract_number(value, 0)
                    elif col_name in ['start_date', 'end_date']:
                        tenant[col_name] = self.extract_date(value)
                    else:
                        tenant[col_name] = value
            
            # Mark as vacant if tenant name indicates vacancy
            tenant['occupied'] = not any(term in tenant.get('tenant', '').lower() 
                                       for term in ['vacant', 'empty', 'available'])
            
            return tenant
            
        except Exception as e:
            logger.error(f"Error parsing tenant line: {str(e)}")
            return None
    
    def _calculate_confidence_scores(self):
        """Calculate confidence scores for extracted data."""
        # Calculate tenant-level confidence
        tenant_confidences = []
        required_fields = ['unit', 'square_footage', 'current_rent']
        
        for tenant in self.tenant_data:
            field_scores = []
            for field in required_fields:
                score = self.calculate_field_confidence(field, tenant.get(field))
                field_scores.append(score)
                self.confidence_scores[f"tenant.{field}"] = score
            
            tenant_confidences.append(sum(field_scores) / len(field_scores))
        
        # Overall confidence score
        self.confidence_scores["overall"] = (
            sum(tenant_confidences) / len(tenant_confidences)
            if tenant_confidences else 0.0
        )
    
    def validate(self) -> bool:
        """
        Validate the extracted rent roll data.
        
        Returns:
            bool: True if validation passed
        """
        self.validation_errors = []
        
        # Check for minimum required data
        if not self.tenant_data:
            self.validation_errors.append("No tenant data extracted")
            return False
        
        # Validate summary calculations
        summary = self.extracted_data.get("summary", {})
        if summary.get("occupancy_rate", 0) > 100:
            self.validation_errors.append("Invalid occupancy rate > 100%")
        
        # Validate individual tenant records
        for i, tenant in enumerate(self.tenant_data):
            # Required fields
            if not tenant.get("unit"):
                self.validation_errors.append(f"Missing unit number for tenant {i+1}")
            
            # Numeric validations
            if tenant.get("square_footage", 0) <= 0:
                self.validation_errors.append(f"Invalid square footage for unit {tenant.get('unit', i+1)}")
            
            if tenant.get("current_rent", 0) < 0:
                self.validation_errors.append(f"Invalid rent amount for unit {tenant.get('unit', i+1)}")
        
        return len(self.validation_errors) == 0
