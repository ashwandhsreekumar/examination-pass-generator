"""Main entry point for the Examination Entry Pass Generator."""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.pass_generator import PassGenerator
from src.config import OUTPUT_DIR


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pass_generator.log')
        ]
    )


def main():
    """Main function to generate examination passes."""
    print("\n" + "="*60)
    print("EXAMINATION ENTRY PASS GENERATOR")
    print("="*60 + "\n")
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create output directory if it doesn't exist
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Initialize pass generator
        generator = PassGenerator()
        
        print("Starting pass generation...")
        print("Note: Existing PDFs will be overwritten.")
        print("-" * 60)
        
        # Generate all passes
        generated_files = generator.generate_all_passes()
        
        # Print summary
        print("\n" + "="*60)
        print("GENERATION SUMMARY")
        print("="*60)
        
        if generated_files:
            total_students = 0
            total_files = 0
            
            for school, files in generated_files.items():
                print(f"\n{school}:")
                if files:
                    # Count students from generated files
                    school_students = 0
                    for file in files:
                        # Extract grade from filename to count students
                        file_path = Path(file)
                        print(f"  ✓ {file_path.name}")
                    
                    # Get student count for this school
                    school_students = generator.get_school_student_count(school)
                    total_students += school_students
                    total_files += len(files)
                    
                    # Calculate students without passes
                    total_in_school = generator.get_total_school_students(school)
                    students_without_passes = total_in_school - school_students
                    
                    print(f"\n  Statistics:")
                    print(f"  - Total students in school: {total_in_school}")
                    print(f"  - Students with passes generated: {school_students}")
                    print(f"  - Students without passes: {students_without_passes}")
                    print(f"  - Grades with exams: {len(files)}")
                    print(f"  - Average students per grade: {school_students // len(files) if files else 0}")
                    
                    # Print grade and section wise statistics
                    grade_stats = generator.get_grade_section_stats(school)
                    if grade_stats:
                        print(f"\n  Grade & Section wise breakdown:")
                        # Custom sorting function to handle grades with non-numeric parts
                        def extract_grade_number(grade_str):
                            try:
                                # Try to extract number from grade string
                                parts = grade_str.split()
                                for part in parts:
                                    if part.isdigit():
                                        return int(part)
                                # If no number found, return high value to put at end
                                return 999
                            except:
                                return 999
                        
                        for grade in sorted(grade_stats.keys(), key=extract_grade_number):
                            stats = grade_stats[grade]
                            total_by_section = stats.get('total_by_section', {})
                            with_passes = stats.get('with_passes', {})
                            
                            # Print grade summary
                            total_in_grade = sum(total_by_section.values())
                            total_with_passes = stats.get('total_with_passes', 0)
                            print(f"    {grade}: {total_with_passes}/{total_in_grade} passes")
                            
                            # Print section details
                            for section in sorted(total_by_section.keys()):
                                section_total = total_by_section[section]
                                section_with_passes = with_passes.get(section, 0)
                                print(f"      - Section {section}: {section_with_passes}/{section_total} passes")
                else:
                    print("  - No passes generated (no matching exams)")
                    total_in_school = generator.get_total_school_students(school)
                    print(f"\n  Statistics:")
                    print(f"  - Total students in school: {total_in_school}")
                    print(f"  - Students with passes generated: 0")
                    print(f"  - Students without passes: {total_in_school}")
            
            # Calculate overall statistics
            total_all_students = sum(generator.get_total_school_students(school) 
                                    for school in generated_files.keys())
            total_without_passes = total_all_students - total_students
            
            print("\n" + "-"*60)
            print("OVERALL STATISTICS")
            print("-"*60)
            print(f"Total schools processed: {len(generated_files)}")
            print(f"Total PDF files generated: {total_files}")
            print(f"Total students in all schools: {total_all_students}")
            print(f"Students with passes generated: {total_students}")
            print(f"Students without passes: {total_without_passes}")
        else:
            print("\nNo passes were generated.")
        
        print("\n" + "="*60)
        print("All passes have been saved to the 'output' folder.")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()