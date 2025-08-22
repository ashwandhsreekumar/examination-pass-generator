"""Student data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Student:
    """Represents a student."""
    
    name: str
    school: str
    grade: str
    section: str
    enrollment_code: Optional[str] = None
    
    @property
    def grade_section(self) -> str:
        """Get combined grade and section."""
        if self.section and self.section.strip() and self.section.strip().lower() not in ['nan', 'none', '', '-']:
            return f"{self.grade} {self.section}"
        return self.grade
    
    @property
    def grade_number(self) -> int:
        """Extract grade number for sorting."""
        try:
            # Extract number from "Grade 01", "Grade 02", etc.
            return int(self.grade.split()[-1])
        except (ValueError, IndexError):
            return 0