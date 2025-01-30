"""
Specialized extractor for lease documents.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from .base import BaseExtractor

logger = logging.getLogger(__name__)

class LeaseExtractor(BaseExtractor):
    """Extracts detailed information from lease documents."""
    
    def __init__(self):
        """Initialize the lease extractor."""
        super().__init__()
        
    def can_handle(self, content: str, filename: str) -> bool:
        """
        Determine if this is a lease document.
        
        Args:
            content: Document content
            filename: Name of the file
            
        Returns:
            bool: True if this is a lease document
        """
        # Check filename
        filename_indicators = [
            'lease', 'tenant', 'agreement', 'contract'
        ]
        if any(term in filename.lower() for term in filename_indicators):
            return True
            
        # Check content for lease indicators
        indicators = [
            r'lease\s*agreement',
            r'tenant\s*lease',
            r'rental\s*agreement',
            r'landlord\s*and\s*tenant',
            r'premises\s*lease',
            r'term\s*of\s*lease'
        ]
        
        content_lower = content.lower()
        return any(re.search(pattern, content_lower) for pattern in indicators)
    
    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract data from lease document content.
        
        Args:
            content: Document content
            
        Returns:
            Dict[str, Any]: Extracted lease data
        """
        try:
            # Extract basic lease information
            basic_info = self._extract_basic_info(content)
            
            # Extract financial terms
            financial_terms = self._extract_financial_terms(content)
            
            # Extract key dates
            key_dates = self._extract_key_dates(content)
            
            # Extract tenant information
            tenant_info = self._extract_tenant_info(content)
            
            # Extract property information
            property_info = self._extract_property_info(content)
            
            # Extract special provisions
            special_provisions = self._extract_special_provisions(content)
            
            # Store extracted data
            self.extracted_data = {
                "basic_info": basic_info,
                "financial_terms": financial_terms,
                "key_dates": key_dates,
                "tenant_info": tenant_info,
                "property_info": property_info,
                "special_provisions": special_provisions
            }
            
            # Calculate confidence scores
            self._calculate_confidence_scores()
            
            # Validate extracted data
            self.validate()
            
            return self.get_result()
            
        except Exception as e:
            logger.error(f"Error extracting lease data: {str(e)}")
            self.validation_errors.append(f"Extraction error: {str(e)}")
            return self.get_result()
    
    def _extract_basic_info(self, content: str) -> Dict[str, Any]:
        """Extract basic lease information."""
        basic_info = {
            "lease_type": None,  # e.g., "Commercial", "Retail", "Office"
            "term_length": None,  # in months
            "lease_status": None,  # "Active", "Expired", "Pending"
            "lease_version": None,
            "execution_date": None
        }
        
        # Detect lease type
        lease_types = {
            "commercial": r'commercial\s*lease',
            "retail": r'retail\s*lease',
            "office": r'office\s*lease',
            "industrial": r'industrial\s*lease',
            "warehouse": r'warehouse\s*lease'
        }
        
        for lease_type, pattern in lease_types.items():
            if re.search(pattern, content, re.IGNORECASE):
                basic_info["lease_type"] = lease_type.capitalize()
                break
        
        # Extract term length
        term_patterns = [
            r'(?:term|period)\s*of\s*(\d+)\s*(?:year|month)s?',
            r'(\d+)[\-\s]year\s*(?:term|lease)',
            r'(\d+)[\-\s]month\s*(?:term|lease)'
        ]
        
        for pattern in term_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                term = int(match.group(1))
                # Convert years to months if necessary
                if 'year' in match.group(0).lower():
                    term *= 12
                basic_info["term_length"] = term
                break
        
        # Extract execution date
        execution_patterns = [
            r'executed\s*(?:on|as\s*of)\s*(\w+\s+\d{1,2},?\s+\d{4})',
            r'dated\s*(?:this)?\s*(\d{1,2}(?:st|nd|rd|th)?\s+\w+,?\s+\d{4})',
            r'effective\s*date[:\s]+(\w+\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in execution_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                basic_info["execution_date"] = self.extract_date(match.group(1))
                break
        
        return basic_info
    
    def _extract_financial_terms(self, content: str) -> Dict[str, Any]:
        """Extract financial terms from the lease."""
        financial_terms = {
            "base_rent": None,
            "rent_escalations": [],
            "security_deposit": None,
            "operating_expenses": {
                "base_year": None,
                "tenant_share": None,
                "caps": None
            },
            "utilities": [],
            "other_charges": []
        }
        
        # Extract base rent
        base_rent_patterns = [
            r'base\s*rent[:\s]+\$?\s*([\d,]+\.?\d*)\s*(?:per\s*(?:month|year|annum))?',
            r'monthly\s*rent[:\s]+\$?\s*([\d,]+\.?\d*)',
            r'annual\s*rent[:\s]+\$?\s*([\d,]+\.?\d*)'
        ]
        
        for pattern in base_rent_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                financial_terms["base_rent"] = self.extract_number(match.group(1))
                break
        
        # Extract rent escalations
        escalation_section = self._extract_section(content,
            start_patterns=[
                r'rent\s*escalation',
                r'rent\s*increase',
                r'rental\s*adjustment'
            ],
            end_patterns=[
                r'security\s*deposit',
                r'operating\s*expenses',
                r'utilities'
            ])
            
        if escalation_section:
            # Look for percentage or fixed increases
            increases = re.finditer(
                r'(\d+(?:\.\d+)?%|\$\s*[\d,]+\.?\d*)\s*(?:increase|adjustment)\s*(?:in|on|at)\s*(?:year|month)\s*(\d+)',
                escalation_section,
                re.IGNORECASE
            )
            
            for match in increases:
                amount = match.group(1)
                year = int(match.group(2))
                
                financial_terms["rent_escalations"].append({
                    "year": year,
                    "amount": amount,
                    "type": "percentage" if "%" in amount else "fixed"
                })
        
        # Extract security deposit
        security_patterns = [
            r'security\s*deposit[:\s]+\$?\s*([\d,]+\.?\d*)',
            r'deposit[:\s]+\$?\s*([\d,]+\.?\d*)\s*(?:as\s*security)?'
        ]
        
        for pattern in security_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                financial_terms["security_deposit"] = self.extract_number(match.group(1))
                break
        
        # Extract operating expenses
        opex_section = self._extract_section(content,
            start_patterns=[r'operating\s*expenses', r'additional\s*rent'],
            end_patterns=[r'utilities', r'maintenance', r'insurance'])
            
        if opex_section:
            # Extract base year
            base_year_match = re.search(
                r'base\s*year[:\s]+(\d{4})',
                opex_section,
                re.IGNORECASE
            )
            if base_year_match:
                financial_terms["operating_expenses"]["base_year"] = int(base_year_match.group(1))
            
            # Extract tenant share
            share_match = re.search(
                r'tenant\'?s?\s*(?:share|portion|percentage)[:\s]+(\d+(?:\.\d+)?)\s*%',
                opex_section,
                re.IGNORECASE
            )
            if share_match:
                financial_terms["operating_expenses"]["tenant_share"] = float(share_match.group(1))
            
            # Extract caps
            cap_match = re.search(
                r'(?:increase|escalation)\s*cap[:\s]+(\d+(?:\.\d+)?)\s*%',
                opex_section,
                re.IGNORECASE
            )
            if cap_match:
                financial_terms["operating_expenses"]["caps"] = float(cap_match.group(1))
        
        return financial_terms
    
    def _extract_key_dates(self, content: str) -> Dict[str, Any]:
        """Extract key dates from the lease."""
        key_dates = {
            "commencement_date": None,
            "expiration_date": None,
            "rent_commencement_date": None,
            "option_notice_date": None,
            "early_termination_date": None
        }
        
        # Extract commencement date
        commencement_patterns = [
            r'commencement\s*date[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
            r'lease\s*(?:shall\s*)?commence[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
            r'beginning\s*(?:on|date)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in commencement_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                key_dates["commencement_date"] = self.extract_date(match.group(1))
                break
        
        # Extract expiration date
        expiration_patterns = [
            r'expiration\s*date[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
            r'lease\s*(?:shall\s*)?(?:terminate|end)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
            r'ending\s*(?:on|date)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in expiration_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                key_dates["expiration_date"] = self.extract_date(match.group(1))
                break
        
        # Extract rent commencement date if different
        rent_patterns = [
            r'rent\s*commencement\s*date[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
            r'rent\s*(?:shall\s*)?commence[:\s]+(\w+\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in rent_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                key_dates["rent_commencement_date"] = self.extract_date(match.group(1))
                break
        
        return key_dates
    
    def _extract_tenant_info(self, content: str) -> Dict[str, Any]:
        """Extract tenant information."""
        tenant_info = {
            "name": None,
            "entity_type": None,  # e.g., "Corporation", "LLC", "Individual"
            "contact_info": {
                "address": None,
                "phone": None,
                "email": None
            },
            "guarantors": []
        }
        
        # Extract tenant name and entity type
        tenant_patterns = [
            r'tenant[:\s]+([^,\n]+)(?:\s*,\s*(?:an?|the)\s+([^,\n]+))?',
            r'lessee[:\s]+([^,\n]+)(?:\s*,\s*(?:an?|the)\s+([^,\n]+))?'
        ]
        
        for pattern in tenant_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                tenant_info["name"] = match.group(1).strip()
                if match.group(2):
                    tenant_info["entity_type"] = match.group(2).strip()
                break
        
        # Extract contact information
        address_section = self._extract_section(content,
            start_patterns=[
                r'tenant\'?s?\s*address',
                r'notice\s*address',
                r'address\s*for\s*notices'
            ],
            end_patterns=[
                r'phone',
                r'email',
                r'contact'
            ])
            
        if address_section:
            # Look for formatted address
            address_match = re.search(
                r'([\d\w\s,.-]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|circle|cir|court|ct|way)[,\s]+(?:suite|ste|unit)?\s*[\d\w-]*[,\s]+[\w\s]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)',
                address_section,
                re.IGNORECASE
            )
            if address_match:
                tenant_info["contact_info"]["address"] = address_match.group(1).strip()
        
        # Extract phone number
        phone_match = re.search(
            r'(?:phone|tel|telephone)[:\s]+(\+?\d{1,2}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
            content,
            re.IGNORECASE
        )
        if phone_match:
            tenant_info["contact_info"]["phone"] = phone_match.group(1)
        
        # Extract email
        email_match = re.search(
            r'(?:email|e-mail)[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            content,
            re.IGNORECASE
        )
        if email_match:
            tenant_info["contact_info"]["email"] = email_match.group(1)
        
        # Extract guarantor information
        guarantor_section = self._extract_section(content,
            start_patterns=[r'guarantor', r'guarantee'],
            end_patterns=[r'term', r'rent', r'security'])
            
        if guarantor_section:
            guarantors = re.finditer(
                r'([^,\n]+)(?:\s*,\s*(?:an?|the)\s+([^,\n]+))?',
                guarantor_section
            )
            
            for match in guarantors:
                guarantor = {
                    "name": match.group(1).strip(),
                    "entity_type": match.group(2).strip() if match.group(2) else None
                }
                tenant_info["guarantors"].append(guarantor)
        
        return tenant_info
    
    def _extract_property_info(self, content: str) -> Dict[str, Any]:
        """Extract property information."""
        property_info = {
            "address": None,
            "square_footage": None,
            "unit_number": None,
            "property_type": None,
            "permitted_use": None
        }
        
        # Extract property address
        address_section = self._extract_section(content,
            start_patterns=[
                r'premises\s*(?:is|are)\s*located',
                r'property\s*address',
                r'leased\s*premises'
            ],
            end_patterns=[
                r'square\s*footage',
                r'permitted\s*use',
                r'tenant'
            ])
            
        if address_section:
            address_match = re.search(
                r'([\d\w\s,.-]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|circle|cir|court|ct|way)[,\s]+(?:suite|ste|unit)?\s*[\d\w-]*[,\s]+[\w\s]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)',
                address_section,
                re.IGNORECASE
            )
            if address_match:
                property_info["address"] = address_match.group(1).strip()
        
        # Extract square footage
        sf_patterns = [
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:square\s*feet|sq\.\s*ft\.|sf)',
            r'premises\s*contains?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:square\s*feet|sq\.\s*ft\.|sf)'
        ]
        
        for pattern in sf_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                property_info["square_footage"] = self.extract_number(match.group(1))
                break
        
        # Extract unit number
        unit_patterns = [
            r'unit\s*(?:number|#)?\s*([A-Z0-9-]+)',
            r'suite\s*(?:number|#)?\s*([A-Z0-9-]+)'
        ]
        
        for pattern in unit_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                property_info["unit_number"] = match.group(1)
                break
        
        # Extract property type
        property_types = [
            'office', 'retail', 'industrial', 'warehouse',
            'manufacturing', 'mixed-use', 'restaurant'
        ]
        
        for prop_type in property_types:
            if re.search(rf'\b{prop_type}\b', content, re.IGNORECASE):
                property_info["property_type"] = prop_type.capitalize()
                break
        
        # Extract permitted use
        use_section = self._extract_section(content,
            start_patterns=[r'permitted\s*use', r'use\s*of\s*premises'],
            end_patterns=[r'maintenance', r'alterations', r'term'])
            
        if use_section:
            # Take the first non-empty line after "permitted use"
            lines = use_section.split('\n')
            for line in lines[1:]:  # Skip the header line
                if line.strip() and not any(header in line.lower() for header in ['permitted', 'use', 'premises']):
                    property_info["permitted_use"] = line.strip()
                    break
        
        return property_info
    
    def _extract_special_provisions(self, content: str) -> List[Dict[str, Any]]:
        """Extract special provisions from the lease."""
        special_provisions = []
        
        # Common special provision sections
        provision_sections = [
            ('option_to_extend', r'option\s*to\s*(?:extend|renew)'),
            ('early_termination', r'early\s*termination'),
            ('right_of_first_refusal', r'right\s*of\s*first\s*refusal'),
            ('tenant_improvements', r'tenant\s*improvements?'),
            ('exclusivity', r'exclusive\s*use'),
            ('sublease_rights', r'sublease|assignment'),
            ('parking', r'parking'),
            ('signage', r'signage|sign')
        ]
        
        for provision_type, pattern in provision_sections:
            section = self._extract_section(content,
                start_patterns=[pattern],
                end_patterns=[r'\d+\.', r'section', r'article'])
                
            if section:
                special_provisions.append({
                    "type": provision_type,
                    "content": section.strip(),
                    "summary": self._summarize_provision(section)
                })
        
        return special_provisions
    
    def _summarize_provision(self, text: str) -> str:
        """Create a brief summary of a provision."""
        # Remove common legal language
        cleaned = re.sub(r'(?:provided|however|notwithstanding|whereas|therefore)\s*,?\s*', '', text.lower())
        
        # Take first sentence or up to 100 characters
        summary = re.split(r'[.!?]', cleaned)[0].strip()
        if len(summary) > 100:
            summary = summary[:97] + "..."
        
        return summary.capitalize()
    
    def _calculate_confidence_scores(self):
        """Calculate confidence scores for extracted data."""
        scores = {}
        
        # Basic info confidence
        basic_info = self.extracted_data.get("basic_info", {})
        scores["basic_info"] = sum(1 for v in basic_info.values() if v is not None) / len(basic_info)
        
        # Financial terms confidence
        financial_terms = self.extracted_data.get("financial_terms", {})
        required_financial = ["base_rent", "security_deposit"]
        scores["financial_terms"] = sum(
            1 for k in required_financial
            if financial_terms.get(k) is not None
        ) / len(required_financial)
        
        # Key dates confidence
        key_dates = self.extracted_data.get("key_dates", {})
        required_dates = ["commencement_date", "expiration_date"]
        scores["key_dates"] = sum(
            1 for k in required_dates
            if key_dates.get(k) is not None
        ) / len(required_dates)
        
        # Tenant info confidence
        tenant_info = self.extracted_data.get("tenant_info", {})
        scores["tenant_info"] = 1.0 if tenant_info.get("name") else 0.0
        
        # Property info confidence
        property_info = self.extracted_data.get("property_info", {})
        required_property = ["address", "square_footage"]
        scores["property_info"] = sum(
            1 for k in required_property
            if property_info.get(k) is not None
        ) / len(required_property)
        
        # Store confidence scores
        self.confidence_scores = scores
        self.confidence_scores["overall"] = sum(scores.values()) / len(scores)
    
    def validate(self) -> bool:
        """
        Validate the extracted lease data.
        
        Returns:
            bool: True if validation passed
        """
        self.validation_errors = []
        
        # Check for minimum required data
        basic_info = self.extracted_data.get("basic_info", {})
        if not basic_info.get("lease_type"):
            self.validation_errors.append("Missing lease type")
        
        # Validate dates
        key_dates = self.extracted_data.get("key_dates", {})
        if not key_dates.get("commencement_date"):
            self.validation_errors.append("Missing commencement date")
        if not key_dates.get("expiration_date"):
            self.validation_errors.append("Missing expiration date")
        
        # Validate financial terms
        financial_terms = self.extracted_data.get("financial_terms", {})
        if not financial_terms.get("base_rent"):
            self.validation_errors.append("Missing base rent")
        
        # Validate tenant information
        tenant_info = self.extracted_data.get("tenant_info", {})
        if not tenant_info.get("name"):
            self.validation_errors.append("Missing tenant name")
        
        # Validate property information
        property_info = self.extracted_data.get("property_info", {})
        if not property_info.get("address"):
            self.validation_errors.append("Missing property address")
        if not property_info.get("square_footage"):
            self.validation_errors.append("Missing square footage")
        
        return len(self.validation_errors) == 0
