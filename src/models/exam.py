"""Exam data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Exam:
    """Represents an exam."""
    
    grade: str
    subject: str
    exam_date: str
    day: str
    timing: str
    school: str
    exam_name: str
    academic_year: str
    
    def formatted_date(self) -> str:
        """Format date consistently as 'DD Month YYYY'."""
        # Try different date formats
        date_formats = [
            "%d/%m/%y",      # 6/8/25
            "%d/%m/%Y",      # 06/08/2025
            "%d-%m-%Y",      # 06-08-2025
            "%Y-%m-%d",      # 2025-08-06
            "%m/%d/%y",      # 8/6/25
            "%m/%d/%Y"       # 08/06/2025
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(self.exam_date.strip(), fmt)
                return date_obj.strftime("%d %b %Y")
            except ValueError:
                continue
        
        # If no format matches, return original
        return self.exam_date