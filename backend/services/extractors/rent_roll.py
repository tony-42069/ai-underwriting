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
        
    def can_handle(self, content: str, filename: str) -> Tuple[bool, float]:
        """
        Determine if this is a rent roll document with confidence score.
        
        Args:
            content: Document content
            filename: Name of the file
            
        Returns:
            Tuple[bool, float]: (Can handle, confidence score)
        """
        confidence = 0.0
        
        # Check filename (30% of confidence)
        filename_indicators = ['rent', 'roll', 'tenant']
        filename_matches = sum(term in filename.lower() for term in filename_indicators)
        filename_confidence = min(filename_matches / len(filename_indicators), 1.0) * 0.3
        
        # Check content for rent roll indicators (70% of confidence)
        indicators = [
            (r'rent\s*roll', 0.2),
            (r'tenant\s*schedule', 0.1),
            (r'lease\s*schedule', 0.1),
            (r'unit\s*number', 0.1),
            (r'tenant\s*name', 0.1),
            (r'monthly\s*rent', 0.1)
        ]
        
        content_lower = content.lower()
        content_confidence = sum(
            weight for pattern, weight in indicators 
            if re.search(pattern, content_lower)
        )
        
        # Calculate total confidence
        confidence = filename_confidence + content_confidence
        
        # Require minimum confidence of 0.3 to handle
        can_handle = confidence >= 0.3
        
        return can_handle, round(confidence, 3)
    
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
        """Calculate enhanced confidence scores with market validation."""
        # Calculate tenant-level confidence
        tenant_confidences = []
        
        # Get market data for validation
        if not self.market_data:
            property_type = self._infer_property_type()
            location = self._infer_location()
            self.fetch_market_data(property_type, location)
        
        for tenant in self.tenant_data:
            field_scores = {}
            
            # Basic field confidence
            for field in self._get_required_fields():
                value = tenant.get(field)
                expected_range = self._get_field_range(field)
                score = self.calculate_field_confidence(field, value, expected_range)
                field_scores[field] = score
                self.confidence_scores[f"tenant.{field}"] = score
            
            # Market-based confidence
            if self.market_data:
                # Validate rent against market rates
                rent_psf = (tenant.get('current_rent', 0) * 12) / tenant.get('square_footage', 1)
                market_rent_range = self.market_data.get('market_rent_range', (0, 1000))
                rent_score = self._calculate_range_confidence(
                    'rent_psf', rent_psf, market_rent_range
                )
                field_scores['market_rent'] = rent_score
                
                # Validate lease terms
                if tenant.get('start_date') and tenant.get('end_date'):
                    lease_term = self._calculate_lease_term(
                        tenant['start_date'], 
                        tenant['end_date']
                    )
                    term_score = self._calculate_lease_term_confidence(lease_term)
                    field_scores['lease_term'] = term_score
            
            # Calculate tenant risk score
            risk_score = self._calculate_tenant_risk_score(tenant)
            field_scores['risk'] = 1 - risk_score  # Convert risk to confidence
            
            # Average all scores for tenant
            tenant_score = sum(field_scores.values()) / len(field_scores)
            tenant_confidences.append(tenant_score)
            
            # Store individual tenant confidence
            self.confidence_scores[f"tenant_{tenant.get('unit', 'unknown')}"] = round(tenant_score, 3)
        
        # Calculate summary metrics confidence
        summary_confidence = self._calculate_summary_confidence()
        self.confidence_scores["summary"] = summary_confidence
        
        # Overall confidence score with weightings
        weights = {
            "tenants": 0.6,
            "summary": 0.2,
            "market_validation": 0.2
        }
        
        tenant_avg = (sum(tenant_confidences) / len(tenant_confidences)) if tenant_confidences else 0
        market_score = self._calculate_market_validation_score()
        
        self.confidence_scores["overall"] = round(
            tenant_avg * weights["tenants"] +
            summary_confidence * weights["summary"] +
            market_score * weights["market_validation"],
            3
        )
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for rent roll."""
        return ['unit', 'square_footage', 'current_rent', 'tenant']

    def _get_format_rules(self) -> Dict[str, Any]:
        """Get format validation rules for rent roll fields."""
        import re
        return {
            'unit': re.compile(r'^[A-Za-z0-9\-\.]+$'),
            'square_footage': re.compile(r'^\d+(\.\d{1,2})?$'),
            'current_rent': re.compile(r'^\d+(\.\d{1,2})?$'),
            'start_date': re.compile(r'^\d{4}-\d{2}-\d{2}$'),
            'end_date': re.compile(r'^\d{4}-\d{2}-\d{2}$')
        }

    def _get_range_rules(self) -> Dict[str, Tuple[float, float]]:
        """Get numerical range rules for rent roll fields."""
        return {
            'square_footage': (100, 1000000),  # 100 to 1M sq ft
            'current_rent': (0, 1000000),      # $0 to $1M monthly
            'occupancy_rate': (0, 100),        # 0% to 100%
            'security_deposit': (0, 1000000)   # $0 to $1M
        }

    def _get_field_range(self, field: str) -> Optional[Tuple[float, float]]:
        """Get expected range for a field based on market data."""
        if not self.market_data:
            return None
            
        ranges = {
            'square_footage': self.market_data.get('unit_size_range'),
            'current_rent': self.market_data.get('monthly_rent_range'),
            'rent_psf': self.market_data.get('market_rent_range')
        }
        return ranges.get(field)

    def _calculate_tenant_risk_score(self, tenant: Dict[str, Any]) -> float:
        """Calculate risk score for an individual tenant."""
        risk_factors = {
            'lease_term': 0.3,
            'credit_quality': 0.3,
            'size': 0.2,
            'industry': 0.2
        }
        
        scores = {
            'lease_term': self._assess_lease_term_risk(tenant),
            'credit_quality': self._assess_credit_risk(tenant),
            'size': self._assess_size_risk(tenant),
            'industry': self._assess_industry_risk(tenant)
        }
        
        return sum(score * risk_factors[factor] for factor, score in scores.items())

    def _calculate_summary_confidence(self) -> float:
        """Calculate confidence score for summary metrics."""
        summary = self.extracted_data.get("summary", {})
        if not summary:
            return 0.0
            
        scores = []
        
        # Validate occupancy rate
        if 0 <= summary.get("occupancy_rate", -1) <= 100:
            scores.append(1.0)
        else:
            scores.append(0.0)
            
        # Validate average rent PSF against market data
        if self.market_data and "average_rent_psf" in summary:
            market_range = self.market_data.get("market_rent_range")
            if market_range:
                min_rent, max_rent = market_range
                rent_psf = summary["average_rent_psf"]
                if min_rent <= rent_psf <= max_rent:
                    scores.append(1.0)
                else:
                    distance = min(abs(rent_psf - min_rent), abs(rent_psf - max_rent))
                    range_size = max_rent - min_rent
                    scores.append(max(0, 1 - (distance / range_size)))
        
        return sum(scores) / len(scores) if scores else 0.0

    def _infer_property_type(self) -> str:
        """Infer property type from rent roll data."""
        # Analyze tenant mix and unit sizes to infer property type
        avg_size = sum(t.get('square_footage', 0) for t in self.tenant_data) / len(self.tenant_data)
        
        if avg_size < 1000:
            return 'multifamily'
        elif avg_size < 5000:
            return 'retail'
        elif any('warehouse' in t.get('tenant', '').lower() for t in self.tenant_data):
            return 'industrial'
        else:
            return 'office'

    def _infer_location(self) -> str:
        """Infer property location from document content."""
        # TODO: Implement location extraction from document header or metadata
        return "unknown"

    def _calculate_lease_term(self, start: str, end: str) -> int:
        """Calculate lease term in months."""
        from datetime import datetime
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end)
        return ((end_date - start_date).days + 30) // 30

    def _calculate_lease_term_confidence(self, term_months: int) -> float:
        """Calculate confidence score for lease term."""
        if term_months <= 0:
            return 0.0
        elif term_months <= 12:
            return 0.7  # Short-term lease
        elif term_months <= 60:
            return 1.0  # Standard lease term
        else:
            return 0.9  # Long-term lease

    def _assess_lease_term_risk(self, tenant: Dict[str, Any]) -> float:
        """Assess risk based on lease term."""
        if not (tenant.get('start_date') and tenant.get('end_date')):
            return 0.8  # High risk if dates missing
            
        term_months = self._calculate_lease_term(
            tenant['start_date'], 
            tenant['end_date']
        )
        
        if term_months <= 12:
            return 0.8  # High risk for short term
        elif term_months <= 36:
            return 0.5  # Medium risk
        else:
            return 0.2  # Low risk for long term

    def _assess_credit_risk(self, tenant: Dict[str, Any]) -> float:
        """Assess tenant credit risk."""
        # TODO: Implement credit check integration
        return 0.5  # Medium risk default

    def _assess_size_risk(self, tenant: Dict[str, Any]) -> float:
        """Assess risk based on tenant size."""
        sf = tenant.get('square_footage', 0)
        total_sf = sum(t.get('square_footage', 0) for t in self.tenant_data)
        
        if total_sf == 0:
            return 0.5
            
        concentration = sf / total_sf
        if concentration > 0.3:
            return 0.8  # High risk for large concentration
        elif concentration > 0.1:
            return 0.5  # Medium risk
        else:
            return 0.3  # Low risk for good diversification

    def _assess_industry_risk(self, tenant: Dict[str, Any]) -> float:
        """Assess risk based on tenant industry."""
        # TODO: Implement industry risk assessment
        return 0.5  # Medium risk default
