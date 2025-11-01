"""
Specialized extractor for profit and loss (P&L) statements.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from .base import BaseExtractor

logger = logging.getLogger(__name__)

class PLStatementExtractor(BaseExtractor):
    """Extracts financial data from profit and loss statements."""
    
    def __init__(self):
        """Initialize the P&L statement extractor."""
        super().__init__()
        self.revenue_items: List[Dict[str, Any]] = []
        self.expense_items: List[Dict[str, Any]] = []
        
    def can_handle(self, content: str, filename: str) -> Tuple[bool, float]:
        """
        Determine if this is a P&L statement with confidence score.
        
        Args:
            content: Document content
            filename: Name of the file
            
        Returns:
            Tuple[bool, float]: (Can handle, confidence score)
        """
        confidence = 0.0
        
        # Check filename (30% of confidence)
        filename_indicators = [
            ('p&l', 0.3),
            ('profit', 0.2),
            ('loss', 0.2),
            ('income', 0.2),
            ('operating', 0.1)
        ]
        filename_lower = filename.lower()
        filename_confidence = sum(
            weight for term, weight in filename_indicators 
            if term in filename_lower
        )
        
        # Check content for P&L indicators (70% of confidence)
        content_indicators = [
            (r'profit\s*(?:and|&)\s*loss', 0.2),
            (r'income\s*statement', 0.15),
            (r'operating\s*statement', 0.1),
            (r'revenue[s]?', 0.1),
            (r'expenses?', 0.05),
            (r'net\s*operating\s*income', 0.05),
            (r'gross\s*income', 0.05)
        ]
        
        content_lower = content.lower()
        content_confidence = sum(
            weight for pattern, weight in content_indicators 
            if re.search(pattern, content_lower)
        )
        
        # Calculate total confidence
        confidence = filename_confidence + content_confidence
        
        # Require minimum confidence of 0.3 to handle
        can_handle = confidence >= 0.3
        
        return can_handle, round(confidence, 3)
    
    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract data from P&L statement content.
        
        Args:
            content: Document content
            
        Returns:
            Dict[str, Any]: Extracted P&L data
        """
        try:
            # Extract revenue and expense items
            self.revenue_items = self._extract_revenue_items(content)
            self.expense_items = self._extract_expense_items(content)
            
            # Calculate key metrics
            total_revenue = sum(item['amount'] for item in self.revenue_items)
            total_expenses = sum(item['amount'] for item in self.expense_items)
            noi = total_revenue - total_expenses
            
            # Store extracted data
            self.extracted_data = {
                "revenue": {
                    "items": self.revenue_items,
                    "total": total_revenue
                },
                "expenses": {
                    "items": self.expense_items,
                    "total": total_expenses
                },
                "summary": {
                    "gross_income": total_revenue,
                    "total_expenses": total_expenses,
                    "noi": noi,
                    "expense_ratio": (total_expenses / total_revenue * 100) if total_revenue > 0 else 0
                }
            }
            
            # Calculate confidence scores
            self._calculate_confidence_scores()
            
            # Validate extracted data
            self.validate()
            
            return self.get_result()
            
        except Exception as e:
            logger.error(f"Error extracting P&L data: {str(e)}")
            self.validation_errors.append(f"Extraction error: {str(e)}")
            return self.get_result()
    
    def _extract_revenue_items(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract revenue line items from the content.
        
        Args:
            content: Document content
            
        Returns:
            List[Dict[str, Any]]: List of revenue items
        """
        revenue_items = []
        
        # Common revenue categories
        revenue_categories = [
            r'rental\s*income',
            r'parking\s*income',
            r'other\s*income',
            r'recovery\s*income',
            r'utility\s*reimbursement',
            r'late\s*fees?',
            r'miscellaneous\s*income'
        ]
        
        # Find revenue section
        revenue_section = self._extract_section(content, 
            start_patterns=[r'revenue', r'income', r'receipts'],
            end_patterns=[r'expenses', r'costs', r'deductions'])
            
        if revenue_section:
            # Process each line in the revenue section
            lines = revenue_section.split('\n')
            for line in lines:
                # Skip empty lines and headers
                if not line.strip() or any(header in line.lower() for header in ['revenue', 'income', 'total']):
                    continue
                
                # Extract amount and description
                amount = self._extract_amount(line)
                if amount is not None:
                    description = self._clean_description(line, amount)
                    category = self._categorize_item(description, revenue_categories)
                    
                    revenue_items.append({
                        "description": description,
                        "amount": amount,
                        "category": category
                    })
        
        return revenue_items
    
    def _extract_expense_items(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract expense line items from the content.
        
        Args:
            content: Document content
            
        Returns:
            List[Dict[str, Any]]: List of expense items
        """
        expense_items = []
        
        # Common expense categories
        expense_categories = [
            r'utilities',
            r'repairs?\s*(?:and|&)?\s*maintenance',
            r'property\s*tax(?:es)?',
            r'insurance',
            r'management\s*fees?',
            r'payroll',
            r'marketing',
            r'administrative',
            r'professional\s*fees?',
            r'landscaping',
            r'security',
            r'cleaning',
            r'supplies'
        ]
        
        # Find expense section
        expense_section = self._extract_section(content,
            start_patterns=[r'expenses', r'costs', r'deductions'],
            end_patterns=[r'net\s*income', r'total', r'summary'])
            
        if expense_section:
            # Process each line in the expense section
            lines = expense_section.split('\n')
            for line in lines:
                # Skip empty lines and headers
                if not line.strip() or any(header in line.lower() for header in ['expense', 'cost', 'total']):
                    continue
                
                # Extract amount and description
                amount = self._extract_amount(line)
                if amount is not None:
                    description = self._clean_description(line, amount)
                    category = self._categorize_item(description, expense_categories)
                    
                    expense_items.append({
                        "description": description,
                        "amount": amount,
                        "category": category
                    })
        
        return expense_items
    
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
    
    def _extract_amount(self, line: str) -> Optional[float]:
        """Extract dollar amount from a line of text."""
        # Look for amount at the end of the line first
        amount_pattern = r'\$?\s*([\d,]+\.?\d*)\s*$'
        match = re.search(amount_pattern, line)
        
        if not match:
            # Try finding any dollar amount in the line
            amount_pattern = r'\$?\s*([\d,]+\.?\d*)'
            match = re.search(amount_pattern, line)
        
        if match:
            return self.extract_number(match.group(1))
        return None
    
    def _clean_description(self, line: str, amount: float) -> str:
        """Clean up the line item description."""
        # Remove the amount and any trailing separators
        description = re.sub(rf'\$?{amount:,.2f}', '', line)
        description = re.sub(r'[\s\-_\.]+$', '', description)
        return description.strip()
    
    def _categorize_item(self, description: str, categories: List[str]) -> str:
        """Categorize a line item based on its description."""
        description_lower = description.lower()
        
        for category in categories:
            if re.search(category, description_lower):
                return category.replace(r'\s*', ' ').strip()
        
        return 'other'
    
    def _calculate_confidence_scores(self):
        """Calculate enhanced confidence scores with market validation."""
        # Get market data for validation
        if not self.market_data:
            property_type = self._infer_property_type()
            location = self._infer_location()
            self.fetch_market_data(property_type, location)
        
        # Calculate revenue confidence
        revenue_confidences = []
        for item in self.revenue_items:
            base_score = 1.0 if item['category'] != 'other' else 0.7
            market_score = self._calculate_market_alignment(item['category'], item['amount'])
            score = (base_score * 0.7) + (market_score * 0.3)
            revenue_confidences.append(score)
            self.confidence_scores[f"revenue.{item['category']}"] = round(score, 3)
        
        # Calculate expense confidence
        expense_confidences = []
        for item in self.expense_items:
            base_score = 1.0 if item['category'] != 'other' else 0.7
            market_score = self._calculate_market_alignment(item['category'], item['amount'])
            score = (base_score * 0.7) + (market_score * 0.3)
            expense_confidences.append(score)
            self.confidence_scores[f"expense.{item['category']}"] = round(score, 3)
        
        # Calculate metrics confidence
        metrics_confidence = self._calculate_metrics_confidence()
        self.confidence_scores["metrics"] = metrics_confidence
        
        # Calculate risk-adjusted confidence
        risk_score = self._calculate_financial_risk()
        risk_confidence = 1 - risk_score  # Convert risk to confidence
        self.confidence_scores["risk_adjusted"] = round(risk_confidence, 3)
        
        # Store category confidences
        self.confidence_scores["revenue"] = round(
            sum(revenue_confidences) / len(revenue_confidences) if revenue_confidences else 0.0,
            3
        )
        self.confidence_scores["expenses"] = round(
            sum(expense_confidences) / len(expense_confidences) if expense_confidences else 0.0,
            3
        )
        
        # Calculate overall confidence with weightings
        weights = {
            "revenue": 0.3,
            "expenses": 0.3,
            "metrics": 0.2,
            "risk_adjusted": 0.2
        }
        
        self.confidence_scores["overall"] = round(
            self.confidence_scores["revenue"] * weights["revenue"] +
            self.confidence_scores["expenses"] * weights["expenses"] +
            metrics_confidence * weights["metrics"] +
            risk_confidence * weights["risk_adjusted"],
            3
        )
    
    def _get_required_fields(self) -> List[str]:
        """Get list of required fields for P&L statement."""
        return ['gross_income', 'total_expenses', 'noi']

    def _get_format_rules(self) -> Dict[str, Any]:
        """Get format validation rules for P&L fields."""
        import re
        return {
            'amount': re.compile(r'^\-?\d+(\.\d{1,2})?$'),
            'percentage': re.compile(r'^\d+(\.\d{1,2})?%$'),
            'description': re.compile(r'^[A-Za-z0-9\s\-\&\.]+$')
        }

    def _get_range_rules(self) -> Dict[str, Tuple[float, float]]:
        """Get numerical range rules for P&L fields."""
        return {
            'expense_ratio': (20, 80),      # 20% to 80%
            'noi_margin': (20, 80),         # 20% to 80%
            'revenue_per_sf': (10, 1000),   # $10 to $1000 per SF annually
            'expense_per_sf': (5, 500)      # $5 to $500 per SF annually
        }

    def _calculate_metrics_confidence(self) -> float:
        """Calculate confidence score for financial metrics."""
        summary = self.extracted_data.get("summary", {})
        if not summary:
            return 0.0
            
        scores = []
        
        # Validate expense ratio against market data
        if self.market_data and "expense_ratio" in summary:
            market_range = self.market_data.get("expense_ratio_range")
            if market_range:
                min_ratio, max_ratio = market_range
                ratio = summary["expense_ratio"]
                scores.append(
                    self._calculate_range_confidence("expense_ratio", ratio, (min_ratio, max_ratio))
                )
        
        # Validate NOI against market data
        if self.market_data and "noi" in summary:
            market_range = self.market_data.get("noi_range")
            if market_range:
                min_noi, max_noi = market_range
                noi = summary["noi"]
                scores.append(
                    self._calculate_range_confidence("noi", noi, (min_noi, max_noi))
                )
        
        return sum(scores) / len(scores) if scores else 0.0

    def _calculate_market_alignment(self, category: str, amount: float) -> float:
        """Calculate market alignment score for a line item."""
        if not self.market_data:
            return 1.0
            
        try:
            # Get market ranges for the category
            ranges = {
                # Revenue categories
                'rental_income': self.market_data.get('rental_income_range'),
                'parking_income': self.market_data.get('parking_income_range'),
                'other_income': self.market_data.get('other_income_range'),
                
                # Expense categories
                'utilities': self.market_data.get('utilities_range'),
                'repairs_maintenance': self.market_data.get('repairs_range'),
                'property_tax': self.market_data.get('tax_range'),
                'insurance': self.market_data.get('insurance_range'),
                'management_fees': self.market_data.get('management_range')
            }
            
            category_range = ranges.get(category.lower().replace(' ', '_'))
            if category_range:
                min_val, max_val = category_range
                if min_val <= amount <= max_val:
                    return 1.0
                
                # Calculate distance from valid range
                distance = min(abs(amount - min_val), abs(amount - max_val))
                range_size = max_val - min_val
                return max(0, 1 - (distance / range_size))
                
            return 1.0  # Default to full confidence if no range available
            
        except Exception as e:
            logger.error(f"Error calculating market alignment: {str(e)}")
            return 1.0

    def _infer_property_type(self) -> str:
        """Infer property type from P&L data."""
        # Analyze revenue sources to infer property type
        revenue_categories = [item['category'].lower() for item in self.revenue_items]
        
        if any('apartment' in cat or 'residential' in cat for cat in revenue_categories):
            return 'multifamily'
        elif any('retail' in cat or 'restaurant' in cat for cat in revenue_categories):
            return 'retail'
        elif any('warehouse' in cat or 'industrial' in cat for cat in revenue_categories):
            return 'industrial'
        else:
            return 'office'

    def _infer_location(self) -> str:
        """Infer property location from document content."""
        # TODO: Implement location extraction from document header or metadata
        return "unknown"

    def validate(self) -> bool:
        """
        Enhanced validation with market data comparison.
        
        Returns:
            bool: True if validation passed
        """
        self.validation_errors = []
        
        try:
            # Basic validation
            if not self.revenue_items and not self.expense_items:
                self.validation_errors.append("No financial data extracted")
                return False
            
            summary = self.extracted_data.get("summary", {})
            
            # Validate ratios
            if summary.get("expense_ratio", 0) > 100:
                self.validation_errors.append("Invalid expense ratio > 100%")
            
            if summary.get("noi", 0) > summary.get("gross_income", 0):
                self.validation_errors.append("NOI cannot be greater than gross income")
            
            # Validate against market data
            if self.market_data:
                # Validate expense ratio
                market_expense_ratio = self.market_data.get("expense_ratio_range")
                if market_expense_ratio:
                    min_ratio, max_ratio = market_expense_ratio
                    current_ratio = summary.get("expense_ratio", 0)
                    if not min_ratio <= current_ratio <= max_ratio:
                        self.validation_errors.append(
                            f"Expense ratio ({current_ratio}%) outside market range "
                            f"[{min_ratio}%, {max_ratio}%]"
                        )
                
                # Validate NOI
                market_noi_range = self.market_data.get("noi_range")
                if market_noi_range:
                    min_noi, max_noi = market_noi_range
                    current_noi = summary.get("noi", 0)
                    if not min_noi <= current_noi <= max_noi:
                        self.validation_errors.append(
                            f"NOI (${current_noi:,.2f}) outside market range "
                            f"[${min_noi:,.2f}, ${max_noi:,.2f}]"
                        )
            
            # Validate individual items
            for item in self.revenue_items + self.expense_items:
                if item.get("amount", 0) < 0:
                    self.validation_errors.append(
                        f"Negative amount found: {item.get('description', 'Unknown item')}"
                    )
                
                # Validate against market ranges if available
                category = item['category'].lower().replace(' ', '_')
                if self.market_data:
                    range_key = f"{category}_range"
                    if range_key in self.market_data:
                        min_val, max_val = self.market_data[range_key]
                        amount = item['amount']
                        if not min_val <= amount <= max_val:
                            self.validation_errors.append(
                                f"{item['description']} (${amount:,.2f}) outside "
                                f"market range [${min_val:,.2f}, ${max_val:,.2f}]"
                            )
            
            # Record validation metadata
            self.processing_metadata["validation_completed"] = datetime.now().isoformat()
            self.processing_metadata["validation_success"] = len(self.validation_errors) == 0
            
            return len(self.validation_errors) == 0
            
        except Exception as e:
            logger.error(f"Error in validation: {str(e)}")
            self.validation_errors.append(f"Validation error: {str(e)}")
            return False
