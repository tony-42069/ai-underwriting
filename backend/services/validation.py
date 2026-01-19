import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue found in extracted data."""

    severity: str
    field: str
    message: str
    current_value: Any
    suggested_value: Optional[Any] = None
    rule: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of data validation."""

    is_valid: bool
    issues: List[ValidationIssue]
    confidence_score: float
    validated_at: datetime = datetime.now()

    def add_issue(self, issue: ValidationIssue):
        """Add a validation issue."""
        self.issues.append(issue)
        self._recalculate_validity()

    def _recalculate_validity(self):
        """Recalculate validity based on issues."""
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        self.is_valid = len(critical_issues) == 0

    def get_summary(self) -> Dict:
        """Get validation summary."""
        by_severity = {"critical": [], "warning": [], "info": []}
        for issue in self.issues:
            by_severity[issue.severity].append(
                {"field": issue.field, "message": issue.message}
            )

        return {
            "is_valid": self.is_valid,
            "total_issues": len(self.issues),
            "by_severity": by_severity,
            "confidence_score": self.confidence_score,
        }


class DocumentValidator:
    """Validates extracted document data for quality and consistency."""

    RULES = {
        "occupancy_rate": {"min": 0, "max": 100, "critical": True},
        "dscr": {"min": 0, "max": 10, "critical": False},
        "cap_rate": {"min": 0, "max": 20, "critical": False},
        "ltv": {"min": 0, "max": 100, "critical": False},
        "expense_ratio": {"min": 0, "max": 100, "critical": False},
        "noi": {"min": 0, "max": None, "critical": True},
        "total_revenue": {"min": 0, "max": None, "critical": True},
        "total_expenses": {"min": 0, "max": None, "critical": True},
        "tenant_count": {"min": 0, "max": None, "critical": False},
        "occupancy_rate_change": {"min": -50, "max": 50, "critical": False},
    }

    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize validator with configurable confidence threshold."""
        self.confidence_threshold = confidence_threshold

    def validate_rent_roll(self, data: Dict) -> ValidationResult:
        """Validate rent roll extracted data."""
        result = ValidationResult(is_valid=True, issues=[], confidence_score=1.0)

        if not data.get("tenants"):
            result.add_issue(
                ValidationIssue(
                    severity="critical",
                    field="tenants",
                    message="No tenant data found",
                    current_value=None,
                    suggested_value="Expected tenant records",
                )
            )
            return result

        summary = data.get("summary", {})
        tenant_count = len(data["tenants"])

        self._validate_numeric_field(
            result, "total_units", summary.get("total_units", 0), (0, None)
        )
        self._validate_numeric_field(
            result, "occupancy_rate", summary.get("occupancy_rate", 0), (0, 100)
        )
        self._validate_numeric_field(
            result, "total_monthly_rent", summary.get("total_monthly_rent", 0), (0, None)
        )

        for i, tenant in enumerate(data["tenants"]):
            self._validate_tenant_record(result, tenant, i)

        result.confidence_score = self._calculate_confidence(result.issues, tenant_count)
        return result

    def validate_pl_statement(self, data: Dict) -> ValidationResult:
        """Validate P&L statement extracted data."""
        result = ValidationResult(is_valid=True, issues=[], confidence_score=1.0)

        summary = data.get("summary", {})
        revenue = summary.get("gross_income", 0)
        expenses = summary.get("total_expenses", 0)
        noi = summary.get("noi", 0)

        self._validate_numeric_field(result, "gross_income", revenue, (0, None))
        self._validate_numeric_field(result, "total_expenses", expenses, (0, None))
        self._validate_numeric_field(result, "noi", noi, (0, None))

        if expenses > revenue:
            result.add_issue(
                ValidationIssue(
                    severity="critical",
                    field="noi",
                    message="Expenses exceed revenue - NOI should be positive",
                    current_value=noi,
                    suggested_value="Expected: revenue - expenses",
                    rule="noi = revenue - expenses",
                )
            )

        expense_ratio = summary.get("expense_ratio", 0)
        self._validate_numeric_field(
            result, "expense_ratio", expense_ratio, (0, 100)
        )

        if expense_ratio > 80:
            result.add_issue(
                ValidationIssue(
                    severity="warning",
                    field="expense_ratio",
                    message=f"High expense ratio: {expense_ratio}%",
                    current_value=expense_ratio,
                    suggested_value="Expected < 80%",
                )
            )

        result.confidence_score = self._calculate_confidence(
            result.issues, len(data.get("revenue", {}).get("items", []))
        )
        return result

    def validate_financial_metrics(self, metrics: Dict) -> ValidationResult:
        """Validate financial analysis metrics."""
        result = ValidationResult(is_valid=True, issues=[], confidence_score=1.0)

        self._validate_numeric_field(result, "noi", metrics.get("noi", 0), (0, None))
        self._validate_numeric_field(result, "dscr", metrics.get("dscr", 0), (0, 10))
        self._validate_numeric_field(result, "capRate", metrics.get("capRate", 0), (0, 20))
        self._validate_numeric_field(result, "ltv", metrics.get("ltv", 0), (0, 100))
        self._validate_numeric_field(
            result, "occupancyRate", metrics.get("occupancyRate", 0), (0, 100)
        )

        dscr = metrics.get("dscr", 0)
        if dscr < 1.0:
            result.add_issue(
                ValidationIssue(
                    severity="critical",
                    field="dscr",
                    message=f"DSCR below 1.0 - negative cash flow: {dscr}",
                    current_value=dscr,
                    suggested_value="Expected > 1.0",
                    rule="DSCR >= 1.0",
                )
            )
        elif dscr < 1.25:
            result.add_issue(
                ValidationIssue(
                    severity="warning",
                    field="dscr",
                    message=f"DSCR below 1.25 - tight coverage: {dscr}",
                    current_value=dscr,
                    suggested_value="Expected > 1.25",
                )
            )

        ltv = metrics.get("ltv", 0)
        if ltv > 80:
            result.add_issue(
                ValidationIssue(
                    severity="critical",
                    field="ltv",
                    message=f"LTV above 80% - excessive leverage: {ltv}%",
                    current_value=ltv,
                    suggested_value="Expected < 80%",
                )
            )
        elif ltv > 75:
            result.add_issue(
                ValidationIssue(
                    severity="warning",
                    field="ltv",
                    message=f"LTV above 75% - high leverage: {ltv}%",
                    current_value=ltv,
                )
            )

        occupancy = metrics.get("occupancyRate", 0)
        if occupancy < 70:
            result.add_issue(
                ValidationIssue(
                    severity="critical",
                    field="occupancyRate",
                    message=f"Occupancy below 70% - high vacancy risk: {occupancy}%",
                    current_value=occupancy,
                )
            )
        elif occupancy < 85:
            result.add_issue(
                ValidationIssue(
                    severity="warning",
                    field="occupancyRate",
                    message=f"Occupancy below 85%: {occupancy}%",
                    current_value=occupancy,
                )
            )

        return result

    def validate_cross_field_consistency(
        self, rent_roll_data: Dict, pl_data: Dict, financial_metrics: Dict
    ) -> ValidationResult:
        """Validate consistency across different data sources."""
        result = ValidationResult(is_valid=True, issues=[], confidence_score=1.0)

        rent_roll_occupancy = rent_roll_data.get("summary", {}).get("occupancy_rate", 0)
        metric_occupancy = financial_metrics.get("occupancyRate", 0)

        if rent_roll_occupancy and metric_occupancy:
            diff = abs(rent_roll_occupancy - metric_occupancy)
            if diff > 10:
                result.add_issue(
                    ValidationIssue(
                        severity="warning",
                        field="occupancyRate",
                        message=f"Occupancy mismatch between rent roll ({rent_roll_occupancy}%) and metrics ({metric_occupancy}%)",
                        current_value=metric_occupancy,
                        suggested_value=rent_roll_occupancy,
                    )
                )

        return result

    def _validate_numeric_field(
        self,
        result: ValidationResult,
        field: str,
        value: float,
        valid_range: tuple,
    ):
        """Validate a numeric field against a range."""
        min_val, max_val = valid_range

        if value is None:
            result.add_issue(
                ValidationIssue(
                    severity="critical" if self.RULES.get(field, {}).get("critical") else "warning",
                    field=field,
                    message=f"Missing required field: {field}",
                    current_value=None,
                )
            )
            return

        if min_val is not None and value < min_val:
            result.add_issue(
                ValidationIssue(
                    severity="critical" if self.RULES.get(field, {}).get("critical") else "warning",
                    field=field,
                    message=f"Value below minimum: {value} < {min_val}",
                    current_value=value,
                    suggested_value=min_val,
                )
            )

        if max_val is not None and value > max_val:
            result.add_issue(
                ValidationIssue(
                    severity="critical" if self.RULES.get(field, {}).get("critical") else "warning",
                    field=field,
                    message=f"Value above maximum: {value} > {max_val}",
                    current_value=value,
                    suggested_value=max_val,
                )
            )

    def _validate_tenant_record(
        self, result: ValidationResult, tenant: Dict, index: int
    ):
        """Validate a single tenant record."""
        unit = tenant.get("unit", f"index_{index}")

        if not tenant.get("tenant") and not tenant.get("occupied") == False:
            result.add_issue(
                ValidationIssue(
                    severity="warning",
                    field=f"tenant_{index}_name",
                    message=f"Missing tenant name for unit {unit}",
                    current_value=None,
                )
            )

        square_footage = tenant.get("square_footage", 0)
        if square_footage <= 0:
            result.add_issue(
                ValidationIssue(
                    severity="critical",
                    field=f"tenant_{index}_square_footage",
                    message=f"Invalid square footage for unit {unit}",
                    current_value=square_footage,
                    suggested_value="Expected > 0",
                )
            )

        rent = tenant.get("current_rent", 0)
        if rent < 0:
            result.add_issue(
                ValidationIssue(
                    severity="critical",
                    field=f"tenant_{index}_rent",
                    message=f"Negative rent for unit {unit}",
                    current_value=rent,
                    suggested_value="Expected >= 0",
                )
            )

    def _calculate_confidence(
        self, issues: List[ValidationIssue], data_points: int
    ) -> float:
        """Calculate confidence score based on issues and data points."""
        if data_points == 0:
            return 0.0

        critical_penalty = 0.1 * len(
            [i for i in issues if i.severity == "critical"]
        )
        warning_penalty = 0.05 * len(
            [i for i in issues if i.severity == "warning"]
        )
        info_penalty = 0.01 * len([i for i in issues if i.severity == "info"])

        confidence = 1.0 - critical_penalty - warning_penalty - info_penalty
        return round(max(0.0, min(1.0, confidence)), 2)

    def get_validation_report(
        self, rent_roll_data: Dict, pl_data: Dict, financial_metrics: Dict
    ) -> Dict:
        """Generate comprehensive validation report."""
        rent_roll_result = self.validate_rent_roll(rent_roll_data)
        pl_result = self.validate_pl_statement(pl_data)
        metrics_result = self.validate_financial_metrics(financial_metrics)
        cross_result = self.validate_cross_field_consistency(
            rent_roll_data, pl_data, financial_metrics
        )

        all_issues = (
            rent_roll_result.issues
            + pl_result.issues
            + metrics_result.issues
            + cross_result.issues
        )

        overall_valid = all(
            r.is_valid for r in [rent_roll_result, pl_result, metrics_result]
        )

        avg_confidence = (
            rent_roll_result.confidence_score
            + pl_result.confidence_score
            + metrics_result.confidence_score
        ) / 3

        return {
            "overall_valid": overall_valid,
            "confidence_score": round(avg_confidence, 2),
            "rent_roll_validation": rent_roll_result.get_summary(),
            "pl_validation": pl_result.get_summary(),
            "metrics_validation": metrics_result.get_summary(),
            "cross_validation": cross_result.get_summary(),
            "all_issues": [
                {
                    "severity": i.severity,
                    "field": i.field,
                    "message": i.message,
                    "current_value": i.current_value,
                    "suggested_value": i.suggested_value,
                }
                for i in all_issues
            ],
            "risk_flags": self._generate_risk_flags(metrics_result),
            "validated_at": datetime.now().isoformat(),
        }

    def _generate_risk_flags(self, metrics_result: ValidationResult) -> List[str]:
        """Generate risk flags from validation results."""
        flags = []
        for issue in metrics_result.issues:
            if issue.severity == "critical":
                flags.append(f"CRITICAL: {issue.field} - {issue.message}")
            elif issue.severity == "warning":
                flags.append(f"WARNING: {issue.field} - {issue.message}")
        return flags
