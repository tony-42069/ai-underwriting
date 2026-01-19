import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)


class FinancialAnalysis:
    """Comprehensive financial analysis for commercial real estate underwriting."""

    DEFAULTS = {
        "property_value_multiplier": 2.0,
        "loan_to_value_ratio": 0.7,
        "debt_service_rate": 0.08,
        "min_noi_threshold": 100000,
        "min_value_threshold": 100000,
    }

    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """Extract all numbers from text."""
        return [float(x) for x in re.findall(r"\$?(\d+(?:,\d{3})*(?:\.\d{2})?)", text)]

    @staticmethod
    def extract_currency_amount(text: str, pattern: str) -> Optional[float]:
        """Extract currency amount using regex pattern."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))
        return None

    @staticmethod
    def find_noi(text: str) -> Optional[float]:
        """Extract NOI from document text."""
        noi_patterns = [
            r"NOI[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Net Operating Income[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Operating\s*Income[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
        ]
        for pattern in noi_patterns:
            result = FinancialAnalysis.extract_currency_amount(text, pattern)
            if result is not None:
                return result
        return None

    @staticmethod
    def find_occupancy(text: str) -> Optional[float]:
        """Extract occupancy rate from document text."""
        occupancy_patterns = [
            r"Occupancy[:|\s]+(\d+(?:\.\d{1,2})?)\s*%",
            r"Occupied[:|\s]+(\d+(?:\.\d{1,2})?)\s*%",
            r"Leased[:|\s]+(\d+(?:\.\d{1,2})?)\s*%",
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
            r"Purchase\s*Price[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
        ]
        for pattern in value_patterns:
            result = FinancialAnalysis.extract_currency_amount(text, pattern)
            if result is not None:
                return result
        return None

    @staticmethod
    def find_loan_amount(text: str) -> Optional[float]:
        """Extract loan amount from document text."""
        loan_patterns = [
            r"Loan\s*Amount[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Mortgage\s*Amount[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Loan\s*Balance[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
        ]
        for pattern in loan_patterns:
            result = FinancialAnalysis.extract_currency_amount(text, pattern)
            if result is not None:
                return result
        return None

    @staticmethod
    def find_debt_service(text: str) -> Optional[float]:
        """Extract annual debt service from document text."""
        debt_patterns = [
            r"Debt\s*Service[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Annual\s*Debt\s*Service[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Annual\s*Debt\s*Payment[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
        ]
        for pattern in debt_patterns:
            result = FinancialAnalysis.extract_currency_amount(text, pattern)
            if result is not None:
                return result
        return None

    @staticmethod
    def find_gross_income(text: str) -> Optional[float]:
        """Extract gross income from document text."""
        income_patterns = [
            r"Gross\s*Income[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Gross\s*Potential\s*Income[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Effective\s*Gross\s*Income[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
        ]
        for pattern in income_patterns:
            result = FinancialAnalysis.extract_currency_amount(text, pattern)
            if result is not None:
                return result
        return None

    @staticmethod
    def find_total_expenses(text: str) -> Optional[float]:
        """Extract total expenses from document text."""
        expense_patterns = [
            r"Total\s*Expenses[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Operating\s*Expenses[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
            r"Operating\s*Costs[:|\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
        ]
        for pattern in expense_patterns:
            result = FinancialAnalysis.extract_currency_amount(text, pattern)
            if result is not None:
                return result
        return None

    @staticmethod
    def calculate_dscr(noi: float, debt_service: float) -> float:
        """Calculate Debt Service Coverage Ratio."""
        if not debt_service or debt_service == 0:
            return 0.0
        return round(noi / debt_service, 2)

    @staticmethod
    def calculate_cap_rate(noi: float, property_value: float) -> float:
        """Calculate Capitalization Rate."""
        if not property_value or property_value == 0:
            return 0.0
        return round((noi / property_value) * 100, 2)

    @staticmethod
    def calculate_ltv(loan_amount: float, property_value: float) -> float:
        """Calculate Loan-to-Value ratio."""
        if not property_value or property_value == 0:
            return 0.0
        return round((loan_amount / property_value) * 100, 2)

    @staticmethod
    def calculate_expense_ratio(total_expenses: float, gross_income: float) -> float:
        """Calculate expense ratio as percentage of gross income."""
        if not gross_income or gross_income == 0:
            return 0.0
        return round((total_expenses / gross_income) * 100, 2)

    @staticmethod
    def calculate_rent_psf(annual_rent: float, square_footage: float) -> float:
        """Calculate rent per square foot."""
        if not square_footage or square_footage == 0:
            return 0.0
        return round(annual_rent / square_footage, 2)

    @staticmethod
    def calculate_grm(gross_rent: float, property_value: float) -> float:
        """Calculate Gross Rent Multiplier."""
        if not gross_rent or gross_rent == 0:
            return 0.0
        return round(property_value / gross_rent, 2)

    @staticmethod
    def calculate_debt_yield(noi: float, loan_amount: float) -> float:
        """Calculate Debt Yield (NOI / Loan Amount)."""
        if not loan_amount or loan_amount == 0:
            return 0.0
        return round((noi / loan_amount) * 100, 2)

    @classmethod
    def calculate_variance(cls, current: float, previous: float) -> Tuple[float, float]:
        """Calculate variance and variance percentage between two values."""
        if not previous or previous == 0:
            return 0.0, 0.0
        variance = current - previous
        variance_pct = round((variance / previous) * 100, 2)
        return round(variance, 2), variance_pct

    @classmethod
    def calculate_trend(cls, values: List[float]) -> Optional[str]:
        """Calculate trend direction from a list of values."""
        if len(values) < 2:
            return None
        first, last = values[0], values[-1]
        if last > first:
            return "increasing"
        elif last < first:
            return "decreasing"
        return "stable"

    @classmethod
    def _estimate_from_numbers(cls, numbers: List[float]) -> Optional[float]:
        """Estimate NOI from extracted numbers using configurable thresholds."""
        if not numbers:
            return None
        max_val = max(numbers)
        threshold = cls.DEFAULTS["min_noi_threshold"]
        if max_val > threshold:
            return max_val / 12
        return None

    @classmethod
    def _estimate_property_value(cls, numbers: List[float]) -> Optional[float]:
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
        """Analyze OCR results and extract comprehensive financial metrics."""
        text = ocr_result.get("text", "")

        noi = cls.find_noi(text)
        occupancy = cls.find_occupancy(text)
        property_value = cls.find_property_value(text)
        loan_amount = cls.find_loan_amount(text)
        debt_service = cls.find_debt_service(text)
        gross_income = cls.find_gross_income(text)
        total_expenses = cls.find_total_expenses(text)

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
        gross_income = gross_income or noi or 0
        total_expenses = total_expenses or 0
        occupancy = occupancy or 0

        dscr = cls.calculate_dscr(noi, debt_service)
        cap_rate = cls.calculate_cap_rate(noi, property_value)
        ltv = cls.calculate_ltv(loan_amount, property_value)
        expense_ratio = cls.calculate_expense_ratio(total_expenses, gross_income)
        debt_yield = cls.calculate_debt_yield(noi, loan_amount)

        return {
            "noi": noi,
            "capRate": cap_rate / 100 if cap_rate else 0,
            "dscr": dscr,
            "ltv": ltv,
            "occupancyRate": occupancy,
            "grossIncome": gross_income,
            "totalExpenses": total_expenses,
            "expenseRatio": expense_ratio,
            "debtYield": debt_yield,
            "loanAmount": loan_amount,
            "propertyValue": property_value,
            "debtService": debt_service,
        }

    @classmethod
    def analyze_variance(
        cls, current_metrics: Dict, previous_metrics: Dict
    ) -> Dict[str, Dict[str, float]]:
        """Analyze variance between current and previous period metrics."""
        variance_analysis = {}

        key_metrics = ["noi", "occupancyRate", "dscr", "capRate", "ltv"]

        for metric in key_metrics:
            current = current_metrics.get(metric, 0)
            previous = previous_metrics.get(metric, 0)
            variance, variance_pct = cls.calculate_variance(current, previous)

            variance_analysis[metric] = {
                "current": current,
                "previous": previous,
                "variance": variance,
                "variancePercentage": variance_pct,
            }

        return variance_analysis

    @classmethod
    def generate_risk_flags(cls, metrics: Dict) -> List[str]:
        """Generate risk flags based on financial metrics."""
        risk_flags = []

        if metrics.get("dscr", 0) < 1.25:
            risk_flags.append("DSCR below 1.25 - potential cash flow issues")

        if metrics.get("occupancyRate", 0) < 85:
            risk_flags.append("Occupancy below 85% - high vacancy risk")

        if metrics.get("ltv", 0) > 75:
            risk_flags.append("LTV above 75% - high leverage")

        if metrics.get("expenseRatio", 0) > 60:
            risk_flags.append("Expense ratio above 60% - high operating costs")

        if metrics.get("capRate", 0) < 4:
            risk_flags.append("Cap rate below 4% - below market returns")

        return risk_flags
