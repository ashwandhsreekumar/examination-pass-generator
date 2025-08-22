"""School data model."""

from dataclasses import dataclass


@dataclass
class School:
    """Represents a school."""
    
    name: str
    address_line1: str
    address_line2: str
    email: str
    
    @property
    def full_address(self) -> str:
        """Get full address formatted for display."""
        return f"{self.address_line1}\n{self.address_line2}"