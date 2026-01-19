import re
import logging
from typing import Dict, Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class FinancialAnalysis:
    DEFAULTS = {
        "property_value_multiplier": 2.0,
        "loan_to_value_ratio": 0.7,
        "debt_service_rate": 0.08,
        "min_noi_threshold": 100000,
        "min_value_threshold": 100000,
    }

    @staticmethod
    def extract_numbers(text: str) -> list:
        """Extract all numbers from text."""
        return [float(x) for x in re.findall(r"\$?(\d+(?:,\d{3})*(?:\.\d{2})?)", text)]

    @staticmethod
    def find_noi(text: str) -> Optional[float]:
        """Extract NOI from document text."""
        noi_patterns = [
            r"NOI[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Net Operating Income[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
        ]

        for pattern in noi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(",", ""))
        return None

    @staticmethod
    def find_occupancy(text: str) -> Optional[float]:
        """Extract occupancy rate from document text."""
        occupancy_patterns = [
            r"Occupancy[:|\s]+(\d+(?:\.\d{1,2})?)\s*%",
            r"Occupied[:|\s]+(\d+(?:\.\d{1,2})?)\s*%",
        ]

        for pattern in occupancy_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None

    @staticmethod
    def find_property_value(text: str) -> Optional[float]:
        """Extract property value from document text."""
        value_patterns = [
            r"Property\s*Value[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Appraised\s*Value[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Market\s*Value[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
        ]

        for pattern in value_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(",", ""))
        return None

    @staticmethod
    def find_loan_amount(text: str) -> Optional[float]:
        """Extract loan amount from document text."""
        loan_patterns = [
            r"Loan\s*Amount[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Mortgage\s*Amount[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
        ]

        for pattern in loan_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(",", ""))
        return None

    @staticmethod
    def find_debt_service(text: str) -> Optional[float]:
        """Extract annual debt service from document text."""
        debt_patterns = [
            r"Debt\s*Service[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Annual\s*Debt\s*Service[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
        ]

        for pattern in debt_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(",", ""))
        return None

    @staticmethod
    def calculate_dscr(noi: float, debt_service: float) -> float:
        """Calculate Debt Service Coverage Ratio."""
        if not debt_service or debt_service == 0:
            return 0.0
        return noi / debt_service

    @staticmethod
    def calculate_cap_rate(noi: float, property_value: float) -> float:
        """Calculate Capitalization Rate."""
        if not property_value or property_value == 0:
            return 0.0
        return (noi / property_value) * 100

    @staticmethod
    def calculate_ltv(loan_amount: float, property_value: float) -> float:
        """Calculate Loan-to-Value ratio."""
        if not property_value or property_value == 0:
            return 0.0
        return (loan_amount / property_value) * 100

    @classmethod
    def _estimate_from_numbers(cls, numbers: list) -> Optional[float]:
        """Estimate NOI from extracted numbers using configurable thresholds."""
        if not numbers:
            return None
        max_val = max(numbers)
        threshold = cls.DEFAULTS["min_noi_threshold"]
        if max_val > threshold:
            return max_val / 12
        return None

    @classmethod
    def _estimate_property_value(cls, numbers: list) -> Optional[float]:
        """Estimate property value from extracted numbers using configurable multipliers."""
        if not numbers:
            return None
        max_val = max(numbers)
        threshold = cls.DEFAULTS["min_value_threshold"]
        if max_val > threshold:
            return max_val * cls.DEFAULTS["property_value_multiplier"]
        return None

    @classmethod
    def _estimate_loan_amount(cls, property_value: float) -> Optional[float]:
        """Estimate loan amount using configurable LTV ratio."""
        if not property_value:
            return None
        return property_value * cls.DEFAULTS["loan_to_value_ratio"]

    @classmethod
    def _estimate_debt_service(cls, loan_amount: float) -> Optional[float]:
        """Estimate debt service using configurable rate."""
        if not loan_amount:
            return None
        return loan_amount * cls.DEFAULTS["debt_service_rate"]

    @classmethod
    async def analyze_document(cls, ocr_result: Dict) -> Dict:
        """Analyze OCR results and extract financial metrics."""
        text = ocr_result.get("text", "")

        noi = cls.find_noi(text)
        occupancy = cls.find_occupancy(text)
        property_value = cls.find_property_value(text)
        loan_amount = cls.find_loan_amount(text)
        debt_service = cls.find_debt_service(text)

        if noi is None or noi == 0:
            logger.warning("NOI not found in document, attempting estimation")
            numbers = cls.extract_numbers(text)
            noi = cls._estimate_from_numbers(numbers)

        if property_value is None:
            numbers = cls.extract_numbers(text)
            property_value = cls._estimate_property_value(numbers)

        if loan_amount is None:
            loan_amount = cls._estimate_loan_amount(property_value)

        if debt_service is None:
            debt_service = cls._estimate_debt_service(loan_amount)

        noi = noi or 0
        property_value = property_value or 0
        loan_amount = loan_amount or 0
        debt_service = debt_service or 0
        occupancy = occupancy or 0

        dscr = cls.calculate_dscr(noi, debt_service)
        cap_rate = cls.calculate_cap_rate(noi, property_value)
        ltv = cls.calculate_ltv(loan_amount, property_value)

        return {
            "noi": noi,
            "capRate": cap_rate / 100 if cap_rate else 0,
            "dscr": dscr,
            "ltv": ltv,
            "occupancyRate": occupancy,
        }
