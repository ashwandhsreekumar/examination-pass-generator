# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python application that generates examination entry passes for Excel Schools (Excel Central School, Excel Global School, Excel Pathway School). The system creates professional PDF passes with 2 passes per A4 landscape page, organized by school and grade.

## Commands

### Running the Application
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the pass generator
python generate_passes.py
# OR
python src/main.py
```

### Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Check logs for debugging
tail -f pass_generator.log
```

## Architecture

The application follows a modular architecture with clear separation of concerns:

- **Entry Points**: `generate_passes.py` (convenience script) → `src/main.py` (main logic)
- **Data Flow**: CSV files → Data Models → Pass Generator Service → PDF Generator → Output PDFs
- **Grade-based Processing**: Generates one PDF per grade containing all students, filtering based on exam availability
- **School Organization**: Output PDFs are automatically organized into school-specific folders

### Key Components

1. **PassGenerator** (`src/services/pass_generator.py`): Orchestrates the entire generation process, handles data loading, grade filtering, and statistics
2. **PDFGenerator** (`src/services/pdf_generator.py`): Creates the actual PDF passes using ReportLab, handles layout and formatting
3. **Data Models** (`src/models/`): Student, Exam, School - dataclasses representing core entities
4. **Configuration** (`src/config.py`): Centralized settings for fonts, dimensions, paths, and fixed values

## Grade Mapping System

The system uses a sophisticated grade mapping to handle different grade formats:
- Maps formatted grades (e.g., "Grade 01", "Grade 02") to various input formats
- Handles special cases like "Foundation 01" → "Grade 01"
- Supports multiple date formats through the DateFormatter utility

## Input Data Requirements

### CSV Files Required in `input/` directory:
- `student_list.csv`: Student records with Display Name, School, Grade, Section, enrollment codes
- `exam_list.csv`: Exam schedules with Grade, Subject, Exam Date, Day, Timing, School, Exam Name
- `school_list.csv`: School details with name, address, contact information

### Image Assets in `images/` directory:
- `logos/`: School logos (ecs.png, egs.png, eps.png)
- `signatures/`: Principal signatures (ecs-principal.png, egs-principal.png, eps-principal.png)

## Output Structure
```
output/
├── Excel Central School/
│   ├── ECS_Grade_01_Passes_Term_I.pdf
│   └── ECS_Grade_02_Passes_Term_I.pdf
└── Excel Global School/
    └── EGS_Grade_01_Passes_Term_I.pdf
```

## Key Features

- Generates 2 passes per A4 landscape page for efficient printing
- Includes comprehensive statistics (total students, passes generated, students without passes)
- Grade and section-wise breakdown in generation summary
- Automatic school logo and principal signature inclusion
- Handles multiple date formats and missing data gracefully
- Detailed logging to `pass_generator.log`