# Examination Entry Pass Generator

A Python application to generate examination entry passes for Excel Schools (Excel Central School, Excel Global School, Excel Pathway School).

## Features

- Generates professional examination entry passes in PDF format
- Creates one PDF per grade containing all students (2 passes per A4 landscape page)
- Automatically organizes output by school folders
- Includes school logos and principal signatures
- Handles multiple date formats
- Skips grades without matching exam schedules

## Requirements

- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

## Installation

1. Clone this repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Ensure your CSV files are in the `input/` directory:
   - `student_list.csv` - Student information
   - `exam_list.csv` - Examination schedules
   - `school_list.csv` - School details

2. Activate the virtual environment (if not already activated):
   ```bash
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Run the generator:
   ```bash
   python generate_passes.py
   ```
   
   Or from the src directory:
   ```bash
   python src/main.py
   ```

4. Generated PDFs will be saved in the `output/` directory, organized by school:
   ```
   output/
   ├── Excel Central School/
   │   ├── ECS_Grade_01_Passes_Term_I.pdf
   │   ├── ECS_Grade_02_Passes_Term_I.pdf
   │   └── ...
   └── Excel Global School/
       └── ...
   ```

## Project Structure

```
examination-pass-generator/
├── src/
│   ├── models/          # Data models
│   ├── services/        # Core services
│   ├── utils/           # Utility functions
│   ├── config.py        # Configuration
│   └── main.py          # Entry point
├── input/               # Input CSV files
├── images/              # Logos and signatures
├── templates/           # Pass templates
├── output/              # Generated PDFs (gitignored)
├── requirements.txt     # Python dependencies
└── generate_passes.py   # Convenience script
```

## Configuration

Edit `src/config.py` to modify:
- Font settings
- Page dimensions
- Date of issue
- Academic year

## Notes

- Admission numbers are left blank if not provided
- Excel Pathway School passes require principal signature to be added
- Only generates passes for grades with matching exam schedules
- Each PDF contains 2 passes per page for efficient printing