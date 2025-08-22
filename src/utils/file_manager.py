"""File and folder management utilities."""

import os
from pathlib import Path
from typing import List


def create_output_structure(schools: List[str], output_dir: Path) -> None:
    """Create output folder structure for schools."""
    for school in schools:
        school_dir = output_dir / school
        school_dir.mkdir(parents=True, exist_ok=True)


def get_output_path(school: str, grade: str, exam_name: str, output_dir: Path) -> Path:
    """Get output file path for a grade PDF."""
    school_dir = output_dir / school
    school_dir.mkdir(parents=True, exist_ok=True)
    
    # Get school abbreviation
    school_abbrev = get_school_abbreviation(school)
    
    # Format grade for filename (e.g., "Grade 01" -> "Grade_01")
    grade_filename = grade.replace(" ", "_")
    
    # Format exam name for filename (e.g., "Term I" -> "Term_I")
    exam_filename = exam_name.replace(" ", "_")
    
    return school_dir / f"{school_abbrev}_{grade_filename}_Passes_{exam_filename}.pdf"


def get_school_abbreviation(school_name: str) -> str:
    """Get school abbreviation from school name."""
    abbreviations = {
        "Excel Central School": "ECS",
        "Excel Global School": "EGS",
        "Excel Pathway School": "EPS"
    }
    return abbreviations.get(school_name, "XXX")


def cleanup_empty_folders(output_dir: Path) -> None:
    """Remove empty school folders."""
    if not output_dir.exists():
        return
    
    for school_dir in output_dir.iterdir():
        if school_dir.is_dir() and not any(school_dir.iterdir()):
            school_dir.rmdir()