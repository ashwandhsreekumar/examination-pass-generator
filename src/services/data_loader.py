"""Data loading service for CSV files."""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple
import logging

from ..models.student import Student
from ..models.exam import Exam
from ..models.school import School
from ..config import STUDENT_LIST_FILE, EXAM_LIST_FILE, SCHOOL_LIST_FILE

logger = logging.getLogger(__name__)


class DataLoader:
    """Handles loading and parsing of CSV data files."""
    
    def load_students(self) -> List[Student]:
        """Load students from CSV file."""
        try:
            df = pd.read_csv(STUDENT_LIST_FILE, encoding='utf-8-sig')
            students = []
            
            for _, row in df.iterrows():
                # Extract required fields
                name = str(row.get('Display Name', '')).strip()
                # Clean up name: remove periods and fix spacing
                name = name.replace('.', '')  # Remove all periods
                name = ' '.join(name.split())  # Normalize whitespace
                
                school = str(row.get('School', '')).strip()
                grade = str(row.get('Grade', '')).strip()
                section = str(row.get('Section', '')).strip()
                enrollment_code = str(row.get('CF.Enrollment Code', '')).strip()
                
                # Skip invalid entries (section is optional)
                if not all([name, school, grade]):
                    continue
                
                # Handle empty enrollment codes
                if enrollment_code in ['', 'nan', 'None']:
                    enrollment_code = None
                
                student = Student(
                    name=name,
                    school=school,
                    grade=grade,
                    section=section,
                    enrollment_code=enrollment_code
                )
                students.append(student)
            
            logger.info(f"Loaded {len(students)} students")
            return students
            
        except Exception as e:
            logger.error(f"Error loading students: {e}")
            return []
    
    def load_exams(self) -> List[Exam]:
        """Load exams from CSV file."""
        try:
            df = pd.read_csv(EXAM_LIST_FILE, encoding='utf-8-sig')
            exams = []
            
            for _, row in df.iterrows():
                exam = Exam(
                    grade=str(row.get('Grade', '')).strip(),
                    subject=str(row.get('Subject', '')).strip(),
                    exam_date=str(row.get('Exam Date', '')).strip(),
                    day=str(row.get('Day', '')).strip(),
                    timing=str(row.get('Timing', '')).strip(),
                    school=str(row.get('School', '')).strip(),
                    exam_name=str(row.get('Exam Name', '')).strip(),
                    academic_year=str(row.get('Academic Year', '')).strip()
                )
                exams.append(exam)
            
            logger.info(f"Loaded {len(exams)} exams")
            return exams
            
        except Exception as e:
            logger.error(f"Error loading exams: {e}")
            return []
    
    def load_schools(self) -> Dict[str, School]:
        """Load schools from CSV file."""
        try:
            df = pd.read_csv(SCHOOL_LIST_FILE, encoding='utf-8-sig')
            schools = {}
            
            for _, row in df.iterrows():
                school = School(
                    name=str(row.get('School', '')).strip(),
                    address_line1=str(row.get('Address Line 1', '')).strip(),
                    address_line2=str(row.get('Address Line 2', '')).strip(),
                    email=str(row.get('Email Address', '')).strip()
                )
                schools[school.name] = school
            
            logger.info(f"Loaded {len(schools)} schools")
            return schools
            
        except Exception as e:
            logger.error(f"Error loading schools: {e}")
            return {}
    
    def group_students_by_school_and_grade(self, students: List[Student]) -> Dict[str, Dict[str, List[Student]]]:
        """Group students by school and grade."""
        grouped = {}
        
        for student in students:
            if student.school not in grouped:
                grouped[student.school] = {}
            
            if student.grade not in grouped[student.school]:
                grouped[student.school][student.grade] = []
            
            grouped[student.school][student.grade].append(student)
        
        # Sort students within each grade by section first, then by name
        for school in grouped:
            for grade in grouped[school]:
                grouped[school][grade].sort(key=lambda s: (s.section, s.name))
        
        return grouped
    
    def filter_exams_for_grade_and_school(self, exams: List[Exam], grade: str, school: str) -> List[Exam]:
        """Filter exams for a specific grade and school."""
        # Map student grades to exam grades
        mapped_exam_grade = self._map_student_grade_to_exam_grade(grade)
        
        filtered = [
            exam for exam in exams
            if exam.grade == mapped_exam_grade and exam.school == school
        ]
        
        # Sort by date
        from ..utils.date_formatter import parse_date
        filtered.sort(key=lambda e: parse_date(e.exam_date) or e.exam_date)
        
        return filtered
    
    def _map_student_grade_to_exam_grade(self, student_grade: str) -> str:
        """Map student grade format to exam grade format.
        
        Maps:
        - Grade 10 -> IGCSE
        - Grade 11 -> AS LEVEL
        - Grade 12 -> A LEVEL
        
        Returns the original grade if no mapping is found.
        """
        grade_mapping = {
            "Grade 10": "IGCSE",
            "Grade 11": "AS LEVEL", 
            "Grade 12": "A LEVEL"
        }
        
        return grade_mapping.get(student_grade, student_grade)
    
    def get_display_grade_name(self, student_grade: str) -> str:
        """Get the grade name to display in PDFs and filenames.
        
        For mapped grades (Grade 10/11/12), returns the exam grade name (IGCSE/AS LEVEL/A LEVEL).
        For other grades, returns the original student grade.
        """
        return self._map_student_grade_to_exam_grade(student_grade)