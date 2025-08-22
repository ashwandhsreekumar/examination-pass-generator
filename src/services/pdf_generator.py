"""PDF generation service using ReportLab."""

from pathlib import Path
from typing import List, Optional
import logging

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader
from PIL import Image

from ..models.student import Student
from ..models.exam import Exam
from ..models.school import School
from ..config import (
    LOGOS_DIR, SIGNATURES_DIR, SCHOOL_LOGO_MAP, SCHOOL_SIGNATURE_MAP,
    PAGE_WIDTH, PAGE_HEIGHT, PASS_WIDTH, MARGIN,
    FONT_FAMILY, FONT_FAMILY_BOLD, TITLE_FONT_SIZE, HEADING_FONT_SIZE,
    NORMAL_FONT_SIZE, SMALL_FONT_SIZE, DATE_OF_ISSUE, ACADEMIC_YEAR,
    LIGHT_GRAY, BORDER_COLOR
)

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Handles PDF generation for examination passes."""
    
    def __init__(self):
        self.canvas = None
        
    def generate_grade_passes(self, students: List[Student], exams: List[Exam], 
                            school: School, grade: str, output_path: Path) -> bool:
        """Generate PDF with all passes for a grade."""
        try:
            self.canvas = canvas.Canvas(str(output_path), pagesize=landscape(A4))
            
            # Process students in pairs (2 per page)
            for i in range(0, len(students), 2):
                # Left pass
                self._draw_pass(students[i], exams, school, is_left=True)
                
                # Right pass (if exists)
                if i + 1 < len(students):
                    self._draw_pass(students[i + 1], exams, school, is_left=False)
                
                # Draw center divider line
                self._draw_center_divider()
                
                # New page for next pair
                if i + 2 < len(students):
                    self.canvas.showPage()
            
            self.canvas.save()
            logger.info(f"Generated {output_path.name} with {len(students)} passes")
            return True
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return False
    
    def _draw_center_divider(self) -> None:
        """Draw vertical line in the center to separate two passes."""
        self.canvas.setStrokeColorRGB(*BORDER_COLOR)
        self.canvas.setLineWidth(0.5)  # Reduced to 1px
        self.canvas.line(PAGE_WIDTH / 2, 0, PAGE_WIDTH / 2, PAGE_HEIGHT)
    
    def _draw_pass_border(self, x_offset: float, pass_width: float) -> None:
        """Draw border around the entire pass."""
        self.canvas.setStrokeColorRGB(*BORDER_COLOR)
        self.canvas.setLineWidth(1)
        self.canvas.rect(x_offset, MARGIN, pass_width, PAGE_HEIGHT - 2 * MARGIN)
    
    def _draw_pass(self, student: Student, exams: List[Exam], school: School, is_left: bool) -> None:
        """Draw a single examination pass."""
        # Calculate starting X position (shifted left)
        if is_left:
            x_offset = MARGIN - 10  # Shifted left
            pass_width = PASS_WIDTH - MARGIN  # Reduced width to increase right margin
        else:
            x_offset = PASS_WIDTH + MARGIN - 10  # Shifted left
            pass_width = PASS_WIDTH - MARGIN
        
        # Start higher up to reduce top gap
        y_top = PAGE_HEIGHT - MARGIN + 10
        
        # Draw all components with dynamic positioning
        y_current = y_top
        
        # Header returns the bottom position
        y_current = self._draw_header(school, exams, x_offset, pass_width, y_current)
        
        # Student info - reduced gap from 15 to 8
        y_current = self._draw_student_info(student, x_offset, pass_width, y_current - 8)
        
        # Exam schedule - reduced gap further to 8
        y_current = self._draw_exam_schedule(exams, x_offset, pass_width, y_current - 8)
        
        # Instructions - reduced gap to 8
        y_current = self._draw_instructions(x_offset, pass_width, y_current - 8)
        
        # Footer at fixed position from bottom
        self._draw_footer(school, x_offset, pass_width, MARGIN + 50)
    
    def _draw_header(self, school: School, exams: List[Exam], x_offset: float, pass_width: float, y_offset: float) -> float:
        """Draw header with logo and school details. Returns bottom Y position."""
        # Logo on the left (moved down more)
        logo_path = LOGOS_DIR / SCHOOL_LOGO_MAP.get(school.name, "")
        logo_y_position = y_offset - 85  # Moved down even more
        
        if logo_path.exists():
            try:
                img = Image.open(logo_path)
                # Scale logo to fit (approximately 30mm width)
                logo_width = 30 * mm
                aspect_ratio = img.height / img.width
                logo_height = logo_width * aspect_ratio
                
                self.canvas.drawImage(
                    str(logo_path),
                    x_offset + 10,
                    logo_y_position,
                    width=logo_width,
                    height=logo_height,
                    preserveAspectRatio=True
                )
            except Exception as e:
                logger.error(f"Error loading logo: {e}")
        
        # School details on the right (moved up)
        text_x = x_offset + pass_width - 10
        text_y = y_offset - 15  # Moved up from -20
        
        self.canvas.setFont(FONT_FAMILY_BOLD, 12)  # Reduced from 14
        self.canvas.drawRightString(text_x, text_y, school.name)
        
        self.canvas.setFont(FONT_FAMILY, 8)  # Reduced from 9
        self.canvas.drawRightString(text_x, text_y - 14, school.address_line1)
        self.canvas.drawRightString(text_x, text_y - 26, school.address_line2)
        self.canvas.drawRightString(text_x, text_y - 38, school.email)
        
        # Title and academic year right-aligned below email
        title_y = text_y - 58
        
        # Get exam name from the first exam (all exams for a grade should have the same exam name)
        exam_name = exams[0].exam_name if exams else "Term I"
        
        self.canvas.setFont(FONT_FAMILY_BOLD, 12)
        self.canvas.drawRightString(text_x, title_y, f"Examination Entry Pass - {exam_name}")
        
        self.canvas.setFont(FONT_FAMILY_BOLD, 9)
        self.canvas.drawRightString(text_x, title_y - 15, f"Academic Year {ACADEMIC_YEAR}")
        
        # Return the bottom position - reduced gap
        return title_y - 20
    
    
    def _draw_student_info(self, student: Student, x_offset: float, pass_width: float, y_offset: float) -> float:
        """Draw student information as three cells with label and value in same cell. Returns bottom Y position."""
        # Calculate dimensions
        table_width = pass_width - 20
        cell_width = table_width / 3
        cell_height = 45
        
        # Draw borders only (no background)
        self.canvas.setStrokeColorRGB(*BORDER_COLOR)
        self.canvas.setLineWidth(0.5)
        # Outer border
        self.canvas.rect(x_offset + 10, y_offset - cell_height, table_width, cell_height)
        # Vertical dividers
        self.canvas.line(x_offset + 10 + cell_width, y_offset, x_offset + 10 + cell_width, y_offset - cell_height)
        self.canvas.line(x_offset + 10 + cell_width * 2, y_offset, x_offset + 10 + cell_width * 2, y_offset - cell_height)
        
        # Draw text content in each cell
        cells = [
            ("Student Name", student.name),
            ("Grade & Section", student.grade_section),
            ("Enrollment Code", student.enrollment_code or '')
        ]
        
        for i, (label, value) in enumerate(cells):
            cell_x = x_offset + 10 + (i * cell_width) + 10  # 10px padding
            
            # Draw label (smaller, bold)
            self.canvas.setFont(FONT_FAMILY_BOLD, 8)
            self.canvas.setFillColor(colors.black)
            self.canvas.drawString(cell_x, y_offset - 15, label)
            
            # Draw value (larger, normal)
            self.canvas.setFont(FONT_FAMILY, 11)
            self.canvas.drawString(cell_x, y_offset - 32, value)
        
        # Return the bottom position
        return y_offset - cell_height
    
    def _draw_exam_schedule(self, exams: List[Exam], x_offset: float, pass_width: float, y_offset: float) -> float:
        """Draw examination schedule table."""
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        # Create styles for wrapping text
        styles = getSampleStyleSheet()
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Normal'],
            fontName=FONT_FAMILY_BOLD,
            fontSize=8,
            alignment=TA_CENTER
        )
        cell_style = ParagraphStyle(
            'CustomCell',
            parent=styles['Normal'],
            fontName=FONT_FAMILY,
            fontSize=8,
            alignment=TA_CENTER,
            leading=10
        )
        subject_style = ParagraphStyle(
            'SubjectCell',
            parent=styles['Normal'],
            fontName=FONT_FAMILY,
            fontSize=8,
            alignment=TA_LEFT,
            leading=10
        )
        
        # Table headers
        headers = [
            Paragraph('Subject', header_style),
            Paragraph('Exam Date', header_style),
            Paragraph('Day', header_style),
            Paragraph('Timing', header_style),
            Paragraph("Invigilator's Sign", header_style)
        ]
        data = [headers]
        
        # Add only actual exam data (no empty rows)
        for exam in exams:
            data.append([
                Paragraph(exam.subject, subject_style),  # Subject can wrap
                Paragraph(exam.formatted_date(), cell_style),
                Paragraph(exam.day, cell_style),
                Paragraph(exam.timing.capitalize(), cell_style),
                ''  # Empty for signature
            ])
        
        # Calculate table width and column widths
        table_width = pass_width - 20
        col_widths = [
            table_width * 0.32,  # Subject - expanded
            table_width * 0.19,  # Exam Date - slightly reduced
            table_width * 0.15,  # Day - slightly reduced
            table_width * 0.13,  # Timing - slightly reduced
            table_width * 0.21   # Invigilator's Sign - same
        ]
        
        # Create and style table with dynamic row heights
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(*LIGHT_GRAY)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Left align subject column
            ('FONTNAME', (0, 0), (-1, 0), FONT_FAMILY_BOLD),
            ('FONTNAME', (0, 1), (-1, -1), FONT_FAMILY),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            # Grid lines with DCDCDC color
            ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(*BORDER_COLOR)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        # Draw table
        table.wrapOn(self.canvas, table_width, 200)
        # Calculate actual table height based on number of rows
        table_height = sum(table._rowHeights)
        table.drawOn(self.canvas, x_offset + 10, y_offset - table_height - 10)
        
        # Return the bottom position
        return y_offset - table_height - 10
    
    def _draw_instructions(self, x_offset: float, pass_width: float, y_offset: float) -> float:
        """Draw instructions section as a table. Returns bottom Y position."""
        from reportlab.platypus import Paragraph, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        
        # Create styles
        styles = getSampleStyleSheet()
        header_style = ParagraphStyle(
            'InstructionHeader',
            parent=styles['Normal'],
            fontName=FONT_FAMILY_BOLD,
            fontSize=8,
            alignment=TA_CENTER
        )
        instruction_style = ParagraphStyle(
            'InstructionStyle',
            parent=styles['Normal'],
            fontName=FONT_FAMILY,
            fontSize=7,
            alignment=TA_LEFT,
            leading=10,
            leftIndent=5,
            rightIndent=5
        )
        
        # Instructions as formatted text with HTML for bold
        instructions_text = """1. Bring this Entry Pass. <b>Read questions and instructions carefully.</b><br/>
2. <b>No Mobile Phones, Digital Watches or Electronic Devices.</b> Arrive 15 minutes early.<br/>
3. <b>No entry 15 minutes after exam starts.</b> Complete on time.<br/>
4. Use the washroom before arriving. No leaving during the first hour.<br/>
5. Use blue or black ink only. <b>Write legibly.</b> Bring pencils, erasers, etc.<br/>
6. Keep your eyes on your own paper. <b>COPYING IS CHEATING!</b><br/>
7. <b>Review your answers thoroughly.</b> Remain silent until you exit."""
        
        # Create table data
        data = [
            [Paragraph('General Examination Instructions for Students', header_style)],
            [Paragraph(instructions_text, instruction_style)]
        ]
        
        # Calculate table width
        table_width = pass_width - 20
        
        # Create and style table
        table = Table(data, colWidths=[table_width])
        table.setStyle(TableStyle([
            # Header row with gray background
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(*LIGHT_GRAY)),
            # White background for content
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            # Border styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(*BORDER_COLOR)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, 0), 3),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        # Draw table
        table.wrapOn(self.canvas, table_width, 200)
        table_height = sum(table._rowHeights)
        table.drawOn(self.canvas, x_offset + 10, y_offset - table_height - 10)
        
        # Return the bottom position
        return y_offset - table_height - 10
    
    def _draw_footer(self, school: School, x_offset: float, pass_width: float, y_offset: float) -> None:
        """Draw footer with signatures matching student details style."""
        # Calculate dimensions
        table_width = pass_width - 20
        cell_width = table_width / 4
        cell_height = 45
        
        # Draw borders only (no background)
        self.canvas.setStrokeColorRGB(*BORDER_COLOR)
        self.canvas.setLineWidth(0.5)
        # Outer border
        self.canvas.rect(x_offset + 10, y_offset - cell_height, table_width, cell_height)
        # Vertical dividers
        for i in range(1, 4):
            self.canvas.line(x_offset + 10 + cell_width * i, y_offset, 
                           x_offset + 10 + cell_width * i, y_offset - cell_height)
        
        # Add principal signature image first (so it appears behind text)
        sig_path = SIGNATURES_DIR / SCHOOL_SIGNATURE_MAP.get(school.name, "")
        if sig_path.exists():
            try:
                # Position signature in the principal's sign cell
                sig_x = x_offset + 10 + cell_width * 3 + (cell_width - 60) / 2
                sig_y = y_offset - 45
                
                self.canvas.drawImage(
                    str(sig_path),
                    sig_x,
                    sig_y,
                    width=60,
                    height=30,
                    preserveAspectRatio=True
                )
            except Exception as e:
                logger.error(f"Error loading signature: {e}")
        
        # Draw text content in each cell (on top of signature)
        cells = [
            ("Date of Issue", DATE_OF_ISSUE),
            ("Parent's Sign", ""),
            ("Class Teacher's Sign", ""),
            ("Principal's Sign", "")
        ]
        
        for i, (label, value) in enumerate(cells):
            cell_x = x_offset + 10 + (i * cell_width) + 10  # 10px padding
            
            # Draw label (smaller, bold)
            self.canvas.setFont(FONT_FAMILY_BOLD, 8)
            self.canvas.setFillColor(colors.black)
            self.canvas.drawString(cell_x, y_offset - 15, label)
            
            # Draw value (larger, normal) - only for date
            if value:
                self.canvas.setFont(FONT_FAMILY, 8)
                self.canvas.drawString(cell_x, y_offset - 32, value)