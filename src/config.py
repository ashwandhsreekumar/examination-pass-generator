"""Configuration settings for the Examination Entry Pass Generator."""

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = BASE_DIR / "images"
TEMPLATES_DIR = BASE_DIR / "templates"

# Input files
STUDENT_LIST_FILE = INPUT_DIR / "student_list.csv"
EXAM_LIST_FILE = INPUT_DIR / "exam_list.csv"
SCHOOL_LIST_FILE = INPUT_DIR / "school_list.csv"

# Image paths
LOGOS_DIR = IMAGES_DIR / "logos"
SIGNATURES_DIR = IMAGES_DIR / "signatures"

# School logo mapping
SCHOOL_LOGO_MAP = {
    "Excel Central School": "ecs.png",
    "Excel Global School": "egs.png",
    "Excel Pathway School": "eps.png"
}

# School signature mapping
SCHOOL_SIGNATURE_MAP = {
    "Excel Central School": "ecs-principal.png",
    "Excel Global School": "egs-principal.png",
    "Excel Pathway School": "eps-principal.png"  # Will be added later
}

# PDF settings (A4 Landscape)
PAGE_WIDTH = 842  # A4 landscape width in points (297mm)
PAGE_HEIGHT = 595  # A4 landscape height in points (210mm)
PASS_WIDTH = PAGE_WIDTH / 2  # Two passes side by side
MARGIN = 20  # Margin in points

# Font settings
FONT_FAMILY = "Helvetica"
FONT_FAMILY_BOLD = "Helvetica-Bold"
TITLE_FONT_SIZE = 16
HEADING_FONT_SIZE = 14
NORMAL_FONT_SIZE = 10
SMALL_FONT_SIZE = 9

# Fixed values
DATE_OF_ISSUE = "28 July 2025"
ACADEMIC_YEAR = "2025-26"

# Colors
BLACK = (0, 0, 0)
GRAY = (0.5, 0.5, 0.5)
LIGHT_GRAY = (0.917, 0.917, 0.917)  # EAEAEA
BORDER_COLOR = (0.863, 0.863, 0.863)  # DCDCDC