"""Pass generation orchestration service."""

import logging
from typing import Dict, List

from .data_loader import DataLoader
from .pdf_generator import PDFGenerator
from ..utils.file_manager import get_output_path, cleanup_empty_folders
from .. import config

logger = logging.getLogger(__name__)


class PassGenerator:
    """Orchestrates the examination pass generation process."""
    
    def __init__(self):
        self.data_loader = DataLoader()
        self.pdf_generator = PDFGenerator()
        self.student_counts = {}  # Track student counts by school
        self.grade_counts = {}    # Track students per grade
        self.grade_section_stats = {}  # Track grade/section wise stats
        
    def generate_all_passes(self) -> Dict[str, List[str]]:
        """Generate all examination passes grouped by school."""
        # Load all data
        students = self.data_loader.load_students()
        exams = self.data_loader.load_exams()
        schools = self.data_loader.load_schools()
        
        if not students:
            logger.error("No students found")
            return {}
        
        if not exams:
            logger.error("No exams found")
            return {}
        
        # Group students by school and grade
        grouped_students = self.data_loader.group_students_by_school_and_grade(students)
        
        # Track generated files
        generated_files = {}
        
        # Process each school
        for school_name, grades in grouped_students.items():
            if school_name not in schools:
                logger.warning(f"School '{school_name}' not found in school list")
                continue
            
            school = schools[school_name]
            generated_files[school_name] = []
            school_student_count = 0
            
            # Initialize school stats if not exists
            if school_name not in self.grade_section_stats:
                self.grade_section_stats[school_name] = {}
            
            # Process each grade
            for grade, grade_students in sorted(grades.items(), key=lambda x: self._extract_grade_number(x[0])):
                # Get exams for this grade and school
                grade_exams = self.data_loader.filter_exams_for_grade_and_school(
                    exams, grade, school_name
                )
                
                # Skip if no exams found
                if not grade_exams:
                    logger.info(f"No exams found for {school_name} - {grade}, skipping")
                    continue
                
                # Track student count
                school_student_count += len(grade_students)
                
                # Track grade/section stats
                if grade not in self.grade_section_stats[school_name]:
                    self.grade_section_stats[school_name][grade] = {
                        'with_passes': {},
                        'total_with_passes': 0,
                        'total_by_section': {}
                    }
                
                # Count students by section
                section_counts = {}
                for student in grade_students:
                    section = student.section
                    if section not in section_counts:
                        section_counts[section] = 0
                    section_counts[section] += 1
                
                # Store section counts for this grade
                self.grade_section_stats[school_name][grade]['with_passes'] = section_counts
                self.grade_section_stats[school_name][grade]['total_with_passes'] = len(grade_students)
                
                # Get exam name (assuming all exams for a grade have the same exam name)
                exam_name = grade_exams[0].exam_name if grade_exams else "Term I"
                
                # Generate PDF for this grade using original grade name from input
                output_path = get_output_path(school_name, grade, exam_name, config.OUTPUT_DIR)
                
                logger.info(f"Generating passes for {school_name} - {grade} ({len(grade_students)} students)")
                
                success = self.pdf_generator.generate_grade_passes(
                    grade_students, grade_exams, school, grade, output_path
                )
                
                if success:
                    generated_files[school_name].append(str(output_path))
                    
            # Store student count for this school
            self.student_counts[school_name] = school_student_count
        
        # Also track total students per school (including those without exams)
        for school_name, grades in grouped_students.items():
            total_in_school = sum(len(students) for students in grades.values())
            if school_name not in self.student_counts:
                self.student_counts[school_name] = 0
            # Store total students separately
            self.grade_counts[school_name] = total_in_school
            
            # Track total students by grade/section (including those without exams)
            for grade, grade_students in grades.items():
                if school_name not in self.grade_section_stats:
                    self.grade_section_stats[school_name] = {}
                if grade not in self.grade_section_stats[school_name]:
                    self.grade_section_stats[school_name][grade] = {
                        'with_passes': {},
                        'total_with_passes': 0,
                        'total_by_section': {}
                    }
                
                # Count all students by section
                for student in grade_students:
                    section = student.section
                    if section not in self.grade_section_stats[school_name][grade]['total_by_section']:
                        self.grade_section_stats[school_name][grade]['total_by_section'][section] = 0
                    self.grade_section_stats[school_name][grade]['total_by_section'][section] += 1
        
        # Clean up empty folders
        cleanup_empty_folders(config.OUTPUT_DIR)
        
        # Summary
        total_files = sum(len(files) for files in generated_files.values())
        logger.info(f"Generation complete: {total_files} PDF files created")
        
        return generated_files
    
    def get_school_student_count(self, school_name: str) -> int:
        """Get the number of students processed for a school."""
        return self.student_counts.get(school_name, 0)
    
    def get_total_school_students(self, school_name: str) -> int:
        """Get the total number of students in a school."""
        return self.grade_counts.get(school_name, 0)
    
    def get_grade_section_stats(self, school_name: str) -> dict:
        """Get grade and section wise statistics for a school."""
        return self.grade_section_stats.get(school_name, {})
    
    def _extract_grade_number(self, grade: str) -> int:
        """Extract grade number for sorting."""
        try:
            # Extract number from "Grade 01", "Grade 02", etc.
            return int(grade.split()[-1])
        except (ValueError, IndexError):
            return 0