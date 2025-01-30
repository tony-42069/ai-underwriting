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
        
    def can_handle(self, content: str, filename: str) -> bool:
        """
        Determine if this is a P&L statement.
        
        Args:
            content: Document content
            filename: Name of the file
            
        Returns:
            bool: True if this is a P&L statement
        """
        # Check filename
        filename_indicators = [
            'p&l', 'profit', 'loss', 'income', 'operating'
        ]
        if any(term in filename.lower() for term in filename_indicators):
            return True
            
        # Check content for P&L indicators
        indicators = [
            r'profit\s*(?:and|&)\s*loss',
            r'income\s*statement',
            r'operating\s*statement',
            r'revenue[s]?',
            r'expenses?',
            r'net\s*operating\s*income',
            r'gross\s*income'
        ]
        
        content_lower = content.lower()
        return any(re.search(pattern, content_lower) for pattern in indicators)
    
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
        """Calculate confidence scores for extracted data."""
        # Calculate revenue confidence
        revenue_confidences = []
        for item in self.revenue_items:
            score = 1.0 if item['category'] != 'other' else 0.7
            revenue_confidences.append(score)
        
        # Calculate expense confidence
        expense_confidences = []
        for item in self.expense_items:
            score = 1.0 if item['category'] != 'other' else 0.7
            expense_confidences.append(score)
        
        # Store confidence scores
        self.confidence_scores = {
            "revenue": sum(revenue_confidences) / len(revenue_confidences) if revenue_confidences else 0.0,
            "expenses": sum(expense_confidences) / len(expense_confidences) if expense_confidences else 0.0,
            "overall": 0.0  # Will be calculated below
        }
        
        # Calculate overall confidence
        scores = list(self.confidence_scores.values())
        self.confidence_scores["overall"] = sum(scores) / len(scores)
    
    def validate(self) -> bool:
        """
        Validate the extracted P&L data.
        
        Returns:
            bool: True if validation passed
        """
        self.validation_errors = []
        
        # Check for minimum required data
        if not self.revenue_items and not self.expense_items:
            self.validation_errors.append("No financial data extracted")
            return False
        
        # Validate summary calculations
        summary = self.extracted_data.get("summary", {})
        
        if summary.get("expense_ratio", 0) > 100:
            self.validation_errors.append("Invalid expense ratio > 100%")
        
        if summary.get("noi", 0) > summary.get("gross_income", 0):
            self.validation_errors.append("NOI cannot be greater than gross income")
        
        # Validate individual items
        for item in self.revenue_items + self.expense_items:
            if item.get("amount", 0) < 0:
                self.validation_errors.append(
                    f"Negative amount found: {item.get('description', 'Unknown item')}"
                )
        
        return len(self.validation_errors) == 0
