"""Date formatting utilities."""

from datetime import datetime
from typing import Optional


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in various formats."""
    if not date_str or not isinstance(date_str, str):
        return None
    
    date_formats = [
        "%d/%m/%y",      # 6/8/25
        "%d/%m/%Y",      # 06/08/2025
        "%d-%m-%Y",      # 06-08-2025
        "%Y-%m-%d",      # 2025-08-06
        "%m/%d/%y",      # 8/6/25
        "%m/%d/%Y",      # 08/06/2025
        "%d/%m/%y",      # 28/07/2025
        "%d/%m/%Y"       # 28/07/2025
    ]
    
    date_str = date_str.strip()
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def format_date(date_str: str) -> str:
    """Format date as 'DD Month YYYY'."""
    date_obj = parse_date(date_str)
    if date_obj:
        return date_obj.strftime("%d %B %Y")
    return date_str  # Return original if parsing fails