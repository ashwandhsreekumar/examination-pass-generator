import streamlit as st
import pandas as pd
import os
import shutil
import zipfile
import tempfile
from pathlib import Path
import base64
from io import BytesIO
import PyPDF2
from PIL import Image
import logging
from datetime import datetime

from src.services.pass_generator import PassGenerator
from src.utils.file_manager import get_display_grade_for_school
import src.config as config

# Hardcoded school data
SCHOOL_DATA = {
    "Excel Central School": {
        "address_line1": "17/190A, Awai Farm Lane, Thiruvattar",
        "address_line2": "Kanyakumari District, Tamil Nadu",
        "email": "contact@excelschools.edu.in"
    },
    "Excel Global School": {
        "address_line1": "17/190B, Awai Farm Lane, Thiruvattar",
        "address_line2": "Kanyakumari District, Tamil Nadu",
        "email": "contact@excelschools.edu.in"
    },
    "Excel Pathway School": {
        "address_line1": "17/190C, Awai Farm Lane, Thiruvattar",
        "address_line2": "Kanyakumari District, Tamil Nadu",
        "email": "contact@excelschools.edu.in"
    }
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Exam Pass Generator | Excel Group of Schools",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    if 'generated_pdfs' not in st.session_state:
        st.session_state.generated_pdfs = []
    if 'temp_dir' not in st.session_state:
        st.session_state.temp_dir = None
    if 'generation_stats' not in st.session_state:
        st.session_state.generation_stats = None
    if 'instructions_expanded' not in st.session_state:
        st.session_state.instructions_expanded = True

def create_download_link(file_path, link_text):
    """Create a download link for a sample file."""
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            file_contents = f.read()
        b64 = base64.b64encode(file_contents).decode()
        file_name = os.path.basename(file_path)
        href = f'<a href="data:text/csv;base64,{b64}" download="{file_name}">{link_text}</a>'
        return href
    return None

def save_uploaded_file(uploaded_file, directory, filename=None):
    if filename:
        file_path = os.path.join(directory, filename)
    else:
        file_path = os.path.join(directory, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def save_uploaded_image(uploaded_file, directory, filename):
    file_path = os.path.join(directory, filename)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def create_zip_file(source_dir):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zip_file.write(file_path, arcname)
    zip_buffer.seek(0)
    return zip_buffer

def display_pdf_preview(pdf_path):
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def get_pdf_page_as_image(pdf_path, page_num=0):
    try:
        import fitz
        pdf_document = fitz.open(pdf_path)
        page = pdf_document[page_num]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img = Image.open(BytesIO(img_data))
        pdf_document.close()
        return img
    except ImportError:
        # PyMuPDF not installed, but we have a fallback method
        return None
    except Exception as e:
        st.error(f"Error loading PDF preview: {e}")
        return None

def main():
    initialize_session_state()
    
    # Custom CSS to reduce sidebar top padding
    st.markdown("""
        <style>
        [data-testid="stSidebarUserContent"] {
            padding-top: 24px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🎓 Examination Pass Generator")
    st.markdown("Generate professional examination entry passes for Excel Schools")
    
    with st.sidebar:
        st.header("📁 Upload Required Files")
        
        st.subheader("CSV Files")
        
        # Student List Upload
        student_file = st.file_uploader(
            "Student List CSV",
            type=['csv'],
            help="Upload student list with Display Name, School, Grade, Section, enrollment codes"
        )
        sample_student_path = Path(__file__).parent / "samples" / "student_list.sample.csv"
        if sample_student_path.exists():
            with open(sample_student_path, 'rb') as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                href = f'<a href="data:text/csv;base64,{b64}" download="student_list.csv" style="text-decoration: none; color: #0068C9;">📥 Download sample file</a>'
                st.markdown(href, unsafe_allow_html=True)
        st.divider()
        
        # Exam List Upload
        exam_file = st.file_uploader(
            "Exam List CSV",
            type=['csv'],
            help="Upload exam schedule with Grade, Subject, Exam Date, Day, Timing, School, Exam Name"
        )
        sample_exam_path = Path(__file__).parent / "samples" / "exam_list.sample.csv"
        if sample_exam_path.exists():
            with open(sample_exam_path, 'rb') as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                href = f'<a href="data:text/csv;base64,{b64}" download="exam_list.csv" style="text-decoration: none; color: #0068C9;">📥 Download sample file</a>'
                st.markdown(href, unsafe_allow_html=True)
        st.divider()
        
        st.info("📌 School information, logos, and principal signatures are automatically included in the generated passes.")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button("🚀 Generate Passes", type="primary", use_container_width=True):
            # Collapse instructions when generating
            st.session_state.instructions_expanded = False
            
            if not all([student_file, exam_file]):
                st.error("Please upload student list and exam list CSV files!")
                return
            
            with st.spinner("Generating examination passes..."):
                try:
                    temp_dir = tempfile.mkdtemp()
                    st.session_state.temp_dir = temp_dir
                    
                    input_dir = os.path.join(temp_dir, "input")
                    output_dir = os.path.join(temp_dir, "output")
                    images_dir = os.path.join(temp_dir, "images")
                    logos_dir = os.path.join(images_dir, "logos")
                    signatures_dir = os.path.join(images_dir, "signatures")
                    
                    os.makedirs(input_dir, exist_ok=True)
                    os.makedirs(output_dir, exist_ok=True)
                    os.makedirs(logos_dir, exist_ok=True)
                    os.makedirs(signatures_dir, exist_ok=True)
                    
                    # Save with specific names that match config expectations
                    save_uploaded_file(student_file, input_dir, "student_list.csv")
                    save_uploaded_file(exam_file, input_dir, "exam_list.csv")
                    
                    # Create school list CSV from hardcoded data
                    school_csv_path = os.path.join(input_dir, "school_list.csv")
                    with open(school_csv_path, 'w') as f:
                        f.write("School,Address Line 1,Address Line 2,Email Address\n")
                        for school_name, school_info in SCHOOL_DATA.items():
                            f.write(f'"{school_name}","{school_info["address_line1"]}","{school_info["address_line2"]}",{school_info["email"]}\n')
                    
                    # Copy existing logos from the project directory
                    project_logos_dir = Path(__file__).parent / "images" / "logos"
                    if project_logos_dir.exists():
                        for logo_file in project_logos_dir.glob("*.png"):
                            shutil.copy2(logo_file, logos_dir)
                    else:
                        st.warning("Default logos not found. Passes will be generated without logos.")
                    
                    # Copy existing signatures from the project directory
                    project_signatures_dir = Path(__file__).parent / "images" / "signatures"
                    if project_signatures_dir.exists():
                        for sig_file in project_signatures_dir.glob("*.png"):
                            shutil.copy2(sig_file, signatures_dir)
                    else:
                        st.warning("Default signatures not found. Passes will be generated without signatures.")
                    
                    original_cwd = os.getcwd()
                    os.chdir(temp_dir)
                    
                    config.INPUT_DIR = Path(input_dir)
                    config.OUTPUT_DIR = Path(output_dir)
                    config.IMAGES_DIR = Path(images_dir)
                    config.STUDENT_LIST_FILE = Path(input_dir) / "student_list.csv"
                    config.EXAM_LIST_FILE = Path(input_dir) / "exam_list.csv"
                    config.SCHOOL_LIST_FILE = Path(input_dir) / "school_list.csv"
                    config.LOGOS_DIR = Path(logos_dir)
                    config.SIGNATURES_DIR = Path(signatures_dir)
                    
                    generator = PassGenerator()
                    generated_files = generator.generate_all_passes()
                    
                    os.chdir(original_cwd)
                    
                    # Find all generated PDF files - scan the output directory
                    pdf_files = []
                    if os.path.exists(output_dir):
                        for root, dirs, files in os.walk(output_dir):
                            for file in files:
                                if file.endswith('.pdf'):
                                    full_path = os.path.join(root, file)
                                    pdf_files.append(full_path)
                                    logger.info(f"Found PDF: {full_path}")
                    
                    # Calculate statistics
                    total_students = 0
                    total_all_students = 0
                    grade_breakdown = {}
                    
                    for school, files in generated_files.items():
                        school_students = generator.get_school_student_count(school)
                        total_school_students = generator.get_total_school_students(school)
                        total_students += school_students
                        total_all_students += total_school_students
                        
                        grade_stats = generator.get_grade_section_stats(school)
                        if grade_stats:
                            grade_breakdown[school] = grade_stats
                    
                    stats = {
                        'total_students': total_all_students,
                        'passes_generated': total_students,
                        'students_without_passes': total_all_students - total_students,
                        'grade_breakdown': grade_breakdown,
                        'pdf_files_generated': len(pdf_files)
                    }
                    st.session_state.generation_stats = stats
                    
                    st.session_state.generated_pdfs = pdf_files
                    
                    if pdf_files:
                        st.success(f"✅ Successfully generated {len(pdf_files)} PDF files!")
                        logger.info(f"Total PDFs found: {len(pdf_files)}")
                    else:
                        # Log what was generated vs what was found
                        logger.warning(f"No PDFs found in {output_dir}")
                        logger.warning(f"Generated files dict: {generated_files}")
                        st.warning("⚠️ No PDF files were generated. This may occur if there are no matching exams for the students in the uploaded files.")
                    
                except Exception as e:
                    st.error(f"Error generating passes: {str(e)}")
                    logger.error(f"Generation error: {e}", exc_info=True)
    
    with col2:
        if st.session_state.generated_pdfs and st.session_state.temp_dir:
            output_dir = os.path.join(st.session_state.temp_dir, "output")
            if os.path.exists(output_dir):
                zip_buffer = create_zip_file(output_dir)
                st.download_button(
                    label="📥 Download All Generated Passes (ZIP)",
                    data=zip_buffer,
                    file_name=f"examination_passes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
    
    with col3:
        if st.button("🗑️ Clear All", use_container_width=True):
            if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
                shutil.rmtree(st.session_state.temp_dir)
            st.session_state.generated_pdfs = []
            st.session_state.temp_dir = None
            st.session_state.generation_stats = None
            st.rerun()
    
    if st.session_state.generation_stats:
        st.header("📊 Generation Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Students", st.session_state.generation_stats['total_students'])
        with col2:
            st.metric("Passes Generated", st.session_state.generation_stats['passes_generated'])
        with col3:
            st.metric("Students Without Passes", st.session_state.generation_stats['students_without_passes'])
        with col4:
            st.metric("PDF Files Created", st.session_state.generation_stats.get('pdf_files_generated', 0))
        
        if st.session_state.generation_stats.get('grade_breakdown'):
            st.subheader("Grade-wise Breakdown")
            
            # Prepare data
            breakdown_data = []
            for school, grades in st.session_state.generation_stats['grade_breakdown'].items():
                for grade, stats in grades.items():
                    total_by_section = stats.get('total_by_section', {})
                    with_passes = stats.get('with_passes', {})
                    for section, total_count in total_by_section.items():
                        passes_count = with_passes.get(section, 0)
                        # Get display grade name for Excel Global School
                        display_grade = get_display_grade_for_school(grade, school)
                        breakdown_data.append({
                            'School': school,
                            'Grade': display_grade,
                            'Section': section,
                            'Total Students': total_count,
                            'With Passes': passes_count,
                            'Without Passes': total_count - passes_count,
                            'Pass Rate': f"{(passes_count/total_count*100):.1f}%" if total_count > 0 else "0%"
                        })
            
            if breakdown_data:
                grade_df = pd.DataFrame(breakdown_data)
                
                # Add filter controls
                st.markdown("**🔍 Filter Options**")
                filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 2, 2, 2])
                
                with filter_col1:
                    schools = ['All'] + sorted(grade_df['School'].unique().tolist())
                    selected_school = st.selectbox(
                        "School",
                        schools,
                        key="filter_school"
                    )
                
                with filter_col2:
                    if selected_school != 'All':
                        filtered_grades = grade_df[grade_df['School'] == selected_school]['Grade'].unique()
                    else:
                        filtered_grades = grade_df['Grade'].unique()
                    grades = ['All'] + sorted(filtered_grades.tolist())
                    selected_grade = st.selectbox(
                        "Grade",
                        grades,
                        key="filter_grade"
                    )
                
                with filter_col3:
                    if selected_school != 'All' and selected_grade != 'All':
                        filtered_sections = grade_df[
                            (grade_df['School'] == selected_school) & 
                            (grade_df['Grade'] == selected_grade)
                        ]['Section'].unique()
                    elif selected_school != 'All':
                        filtered_sections = grade_df[grade_df['School'] == selected_school]['Section'].unique()
                    elif selected_grade != 'All':
                        filtered_sections = grade_df[grade_df['Grade'] == selected_grade]['Section'].unique()
                    else:
                        filtered_sections = grade_df['Section'].unique()
                    sections = ['All'] + sorted(filtered_sections.tolist())
                    selected_section = st.selectbox(
                        "Section",
                        sections,
                        key="filter_section"
                    )
                
                with filter_col4:
                    pass_status = st.selectbox(
                        "Pass Status",
                        ['All', 'With Passes', 'Without Passes', 'Partial'],
                        key="filter_status"
                    )
                
                # Apply filters
                filtered_df = grade_df.copy()
                
                if selected_school != 'All':
                    filtered_df = filtered_df[filtered_df['School'] == selected_school]
                
                if selected_grade != 'All':
                    filtered_df = filtered_df[filtered_df['Grade'] == selected_grade]
                
                if selected_section != 'All':
                    filtered_df = filtered_df[filtered_df['Section'] == selected_section]
                
                if pass_status == 'With Passes':
                    filtered_df = filtered_df[filtered_df['With Passes'] == filtered_df['Total Students']]
                elif pass_status == 'Without Passes':
                    filtered_df = filtered_df[filtered_df['With Passes'] == 0]
                elif pass_status == 'Partial':
                    filtered_df = filtered_df[
                        (filtered_df['With Passes'] > 0) & 
                        (filtered_df['With Passes'] < filtered_df['Total Students'])
                    ]
                
                # Display filtered results
                st.markdown(f"**Showing {len(filtered_df)} of {len(grade_df)} records**")
                
                # Display the filtered dataframe
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Total Students": st.column_config.NumberColumn(
                            "Total Students",
                            format="%d"
                        ),
                        "With Passes": st.column_config.NumberColumn(
                            "With Passes",
                            format="%d"
                        ),
                        "Without Passes": st.column_config.NumberColumn(
                            "Without Passes",
                            format="%d"
                        ),
                        "Pass Rate": st.column_config.TextColumn(
                            "Pass Rate",
                            help="Percentage of students with passes"
                        )
                    }
                )
    
    if st.session_state.generated_pdfs:
        st.header("📄 Generated PDF Files")
        
        tab1, tab2 = st.tabs(["File List", "PDF Preview"])
        
        with tab1:
            for pdf_path in st.session_state.generated_pdfs:
                rel_path = os.path.relpath(pdf_path, st.session_state.temp_dir)
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(rel_path)
                with col2:
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Download",
                            data=f.read(),
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf",
                            key=f"download_{rel_path}"
                        )
        
        with tab2:
            if st.session_state.generated_pdfs:
                selected_pdf = st.selectbox(
                    "Select a PDF to preview",
                    options=st.session_state.generated_pdfs,
                    format_func=lambda x: os.path.relpath(x, st.session_state.temp_dir)
                )
                
                if selected_pdf:
                    st.subheader(f"Preview: {os.path.basename(selected_pdf)}")
                    
                    try:
                        pdf_image = get_pdf_page_as_image(selected_pdf, 0)
                        if pdf_image:
                            st.image(pdf_image, caption="First page preview", use_column_width=True)
                        else:
                            with open(selected_pdf, "rb") as f:
                                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                            pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf">'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Could not display PDF preview: {e}")
                        with open(selected_pdf, "rb") as f:
                            st.download_button(
                                label="Download PDF to view",
                                data=f.read(),
                                file_name=os.path.basename(selected_pdf),
                                mime="application/pdf"
                            )
    
    with st.expander("ℹ️ Instructions", expanded=st.session_state.instructions_expanded):
        st.markdown("""
        ### How to use this application:
        
        1. **Upload Required CSV Files:**
           - Student List: Contains student information (name, school, grade, section)
           - Exam List: Contains exam schedules and details
        
        2. **Automatic Assets:**
           - School information (address, email) is pre-configured
           - School logos and principal signatures are automatically included
           - No image or school data uploads required
        
        3. **Generate Passes:**
           - Click the "Generate Passes" button
           - Wait for the generation process to complete
        
        4. **Download Results:**
           - Download individual PDFs or
           - Download all files as a ZIP archive
        
        5. **Preview:**
           - Use the PDF Preview tab to view generated passes
        """)

if __name__ == "__main__":
    main()