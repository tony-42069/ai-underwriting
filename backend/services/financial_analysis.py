import re
from typing import Dict, Optional
import numpy as np

class FinancialAnalysis:
    @staticmethod
    def extract_numbers(text: str) -> list:
        """Extract all numbers from text."""
        return [float(x) for x in re.findall(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', text)]

    @staticmethod
    def find_noi(text: str) -> Optional[float]:
        """Extract NOI from document text."""
        noi_patterns = [
            r'NOI[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Net Operating Income[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        for pattern in noi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', ''))
        return None

    @staticmethod
    def find_occupancy(text: str) -> Optional[float]:
        """Extract occupancy rate from document text."""
        occupancy_patterns = [
            r'Occupancy[:|\s]+(\d+(?:\.\d{1,2})?)\s*%',
            r'Occupied[:|\s]+(\d+(?:\.\d{1,2})?)\s*%',
        ]
        
        for pattern in occupancy_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None

    @staticmethod
    def calculate_dscr(noi: float, debt_service: float) -> float:
        """Calculate Debt Service Coverage Ratio."""
        return noi / debt_service if debt_service else 0.0

    @staticmethod
    def calculate_cap_rate(noi: float, property_value: float) -> float:
        """Calculate Capitalization Rate."""
        return (noi / property_value * 100) if property_value else 0.0

    @staticmethod
    def calculate_ltv(loan_amount: float, property_value: float) -> float:
        """Calculate Loan-to-Value ratio."""
        return (loan_amount / property_value * 100) if property_value else 0.0

    @classmethod
    async def analyze_document(cls, ocr_result: Dict) -> Dict:
        """Analyze OCR results and extract financial metrics."""
        text = ocr_result.get('text', '')
        
        # Extract basic metrics
        noi = cls.find_noi(text) or 250000  # Example fallback
        occupancy = cls.find_occupancy(text) or 95  # Example fallback
        
        # For demo purposes, using some assumptions
        property_value = 5000000  # Example value
        loan_amount = 3750000     # Example value
        debt_service = 200000     # Example value
        
        # Calculate key metrics
        dscr = cls.calculate_dscr(noi, debt_service)
        cap_rate = cls.calculate_cap_rate(noi, property_value)
        ltv = cls.calculate_ltv(loan_amount, property_value)
        
        return {
            "noi": noi,
            "capRate": cap_rate / 100,  # Convert to decimal
            "dscr": dscr,
            "ltv": ltv,
            "occupancyRate": occupancy
        }
