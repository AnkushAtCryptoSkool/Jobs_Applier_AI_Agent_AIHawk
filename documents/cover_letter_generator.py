from pathlib import Path
from typing import Optional
import yaml
from documents.llm.llm_generate_cover_letter_from_job import LLMCoverLetterJobDescription
from profiles.config import ConfigValidator, FileManager
from src.libs.resume_and_cover_builder.pdf_generator import PDFGenerator


class CoverLetterGenerator:
    """High-level cover letter generator that uses LLM to create tailored cover letters."""
    
    def __init__(self, data_folder: Path = None):
        """Initialize the cover letter generator.
        
        Args:
            data_folder: Path to the data folder containing configuration files
        """
        if data_folder is None:
            data_folder = Path("data_folder")
        
        self.data_folder = data_folder
        self._validate_setup()
        
        # Load configuration
        secrets_file, config_file, resume_file, output_folder = FileManager.validate_data_folder(data_folder)
        self.llm_api_key = ConfigValidator.validate_secrets(secrets_file)
        
        # Load resume data
        with open(resume_file, 'r') as f:
            self.resume_data = yaml.safe_load(f)
        
        # Initialize global config for logging
        from .config import global_config
        global_config.LOG_OUTPUT_FILE_PATH = output_folder
        
        # Initialize LLM generator
        # Import templates directly from file
        cover_letter_template = """
Compose a brief and impactful cover letter based on the provided job description and resume. The letter should be no longer than three paragraphs and should be written in a professional, yet conversational tone. Avoid using any placeholders, and ensure that the letter flows naturally and is tailored to the job.

Analyze the job description to identify key qualifications and requirements. Introduce the candidate succinctly, aligning their career objectives with the role. Highlight relevant skills and experiences from the resume that directly match the job's demands, using specific examples to illustrate these qualifications. Reference notable aspects of the company, such as its mission or values, that resonate with the candidate's professional goals. Conclude with a strong statement of why the candidate is a good fit for the position, expressing a desire to discuss further.

Please write the cover letter in a way that directly addresses the job role and the company's characteristics, ensuring it remains concise and engaging without unnecessary embellishments. The letter should be formatted into paragraphs and should not include a greeting or signature.

## Rules:
- Do not include any introductions, explanations, or additional information.

## Details :
- **Job Description:**
```
{job_description}
```
- **My resume:**
```
{resume}
```
"""

        summarize_prompt_template = """
As a seasoned HR expert, your task is to identify and outline the key skills and requirements necessary for the position of this job. Use the provided job description as input to extract all relevant information. This will involve conducting a thorough analysis of the job's responsibilities and the industry standards. You should consider both the technical and soft skills needed to excel in this role. Additionally, specify any educational qualifications, certifications, or experiences that are essential. Your analysis should also reflect on the evolving nature of this role, considering future trends and how they might affect the required competencies.

Rules:
Remove boilerplate text
Include only relevant information to match the job description against the resume

# Analysis Requirements
Your analysis should include the following sections:
Technical Skills: List all the specific technical skills required for the role based on the responsibilities described in the job description.
Soft Skills: Identify the necessary soft skills, such as communication abilities, problem-solving, time management, etc.
Educational Qualifications and Certifications: Specify the essential educational qualifications and certifications for the role.
Professional Experience: Describe the relevant work experiences that are required or preferred.
Role Evolution: Analyze how the role might evolve in the future, considering industry trends and how these might influence the required skills.

# Final Result:
Your analysis should be structured in a clear and organized document with distinct sections for each of the points listed above. Each section should contain:
This comprehensive overview will serve as a guideline for the recruitment process, ensuring the identification of the most qualified candidates.

# Job Description:
```
{text}
```

---

# Job Description Summary"""
        
        # Create a simple strings object
        class CoverLetterStrings:
            def __init__(self):
                self.cover_letter_template = cover_letter_template
                self.summarize_prompt_template = summarize_prompt_template
        
        strings = CoverLetterStrings()
        self.llm_generator = LLMCoverLetterJobDescription(
            openai_api_key=self.llm_api_key,
            strings=strings
        )
        
        self.output_folder = output_folder
        
        # Initialize PDF generator
        self.pdf_generator = PDFGenerator()
    
    def _format_resume_data(self, resume_data: dict) -> str:
        """Format resume data dictionary into a readable string."""
        formatted_parts = []
        
        # Personal Information
        if 'personal_information' in resume_data:
            personal = resume_data['personal_information']
            formatted_parts.append(f"Name: {personal.get('name', '')} {personal.get('surname', '')}")
            formatted_parts.append(f"Email: {personal.get('email', '')}")
            formatted_parts.append(f"Phone: {personal.get('phone_prefix', '')} {personal.get('phone', '')}")
            if personal.get('linkedin'):
                formatted_parts.append(f"LinkedIn: {personal.get('linkedin')}")
            if personal.get('github'):
                formatted_parts.append(f"GitHub: {personal.get('github')}")
            formatted_parts.append("")
        
        # Experience
        if 'experience_details' in resume_data:
            formatted_parts.append("EXPERIENCE:")
            for exp in resume_data['experience_details']:
                formatted_parts.append(f"• {exp.get('position', '')} at {exp.get('company', '')}")
                formatted_parts.append(f"  {exp.get('employment_period', '')} - {exp.get('location', '')}")
                if 'key_responsibilities' in exp:
                    for resp in exp['key_responsibilities']:
                        if isinstance(resp, dict):
                            formatted_parts.append(f"  - {list(resp.values())[0]}")
                        else:
                            formatted_parts.append(f"  - {resp}")
                formatted_parts.append("")
        
        # Education
        if 'education_details' in resume_data:
            formatted_parts.append("EDUCATION:")
            for edu in resume_data['education_details']:
                formatted_parts.append(f"• {edu.get('education_level', '')} in {edu.get('field_of_study', '')}")
                formatted_parts.append(f"  {edu.get('institution', '')} ({edu.get('start_date', '')}-{edu.get('year_of_completion', '')})")
                if edu.get('final_evaluation_grade'):
                    formatted_parts.append(f"  Grade: {edu.get('final_evaluation_grade')}")
                formatted_parts.append("")
        
        # Skills (extracted from experience)
        skills = set()
        if 'experience_details' in resume_data:
            for exp in resume_data['experience_details']:
                if 'skills_acquired' in exp:
                    skills.update(exp['skills_acquired'])
        
        if skills:
            formatted_parts.append("SKILLS:")
            formatted_parts.append(", ".join(sorted(skills)))
            formatted_parts.append("")
        
        return "\n".join(formatted_parts)
    
    def _validate_setup(self):
        """Validate that all required files exist and are properly configured."""
        try:
            FileManager.validate_data_folder(self.data_folder)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Setup incomplete: {e}")
    
    def _create_html_cover_letter(self, content: str) -> str:
        """Create HTML formatted cover letter."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Cover Letter</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            color: #333;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
        }}
        .content {{
            text-align: justify;
            margin-bottom: 30px;
        }}
        .paragraph {{
            margin-bottom: 15px;
        }}
        .signature {{
            margin-top: 30px;
            text-align: right;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Cover Letter</h1>
    </div>
    <div class="content">
        {content}
    </div>
</body>
</html>
"""
        
        # Format content into paragraphs
        paragraphs = content.split('\n\n')
        formatted_content = ""
        for paragraph in paragraphs:
            if paragraph.strip():
                formatted_content += f'<div class="paragraph">{paragraph.strip()}</div>\n'
        
        return html_template.format(content=formatted_content)
    
    def generate_cover_letter(self, job_description: str, output_path: Optional[str] = None, format: str = "txt") -> str:
        """Generate a cover letter for a specific job.
        
        Args:
            job_description: The job description to tailor the cover letter for
            output_path: Optional custom output path for the cover letter
            format: Output format ("txt", "html", or "pdf")
            
        Returns:
            Path to the generated cover letter file
        """
        if not job_description.strip():
            raise ValueError("Job description cannot be empty")
        
        # Generate cover letter using LLM
        # Convert resume data to string format
        resume_str = self._format_resume_data(self.resume_data)
        self.llm_generator.set_resume(resume_str)
        self.llm_generator.set_job_description_from_text(job_description)
        cover_letter_content = self.llm_generator.generate_cover_letter()
        
        # Determine output path
        if output_path is None:
            output_path = self.output_folder / f"cover_letter.{format}"
        else:
            output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "pdf":
            # Generate HTML version first
            html_content = self._create_html_cover_letter(cover_letter_content)
            
            # Generate both HTML and PDF
            base_path = str(output_path.with_suffix(""))
            html_path, pdf_path, success = self.pdf_generator.save_html_and_pdf(
                html_content, base_path
            )
            
            if success:
                print(f"✅ Cover letter generated successfully:")
                print(f"   HTML: {html_path}")
                print(f"   PDF:  {pdf_path}")
                return pdf_path
            else:
                print(f"⚠️  PDF generation failed, HTML saved: {html_path}")
                return html_path
        
        elif format.lower() == "html":
            # Generate HTML version
            html_content = self._create_html_cover_letter(cover_letter_content)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ Cover letter generated: {output_path}")
            return str(output_path)
        
        else:
            # Generate text version (default)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cover_letter_content)
            print(f"✅ Cover letter generated: {output_path}")
            return str(output_path)
    
    def generate_multiple_cover_letters(self, jobs: list, output_dir: Optional[str] = None, format: str = "txt") -> list:
        """Generate cover letters for multiple jobs.
        
        Args:
            jobs: List of job dictionaries containing 'description' and optionally 'company' and 'title'
            output_dir: Optional custom output directory
            
        Returns:
            List of paths to generated cover letter files
        """
        if output_dir is None:
            output_dir = self.output_folder / "cover_letters"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        for i, job in enumerate(jobs):
            job_description = job.get('description', '')
            if not job_description.strip():
                continue
            
            # Create filename
            company = job.get('company', f'company_{i+1}')
            title = job.get('title', f'position_{i+1}')
            filename = f"cover_letter_{company}_{title}.txt".replace(' ', '_').replace('/', '_')
            
            output_path = output_dir / filename
            
            try:
                cover_letter_path = self.generate_cover_letter(job_description, str(output_path), format=format)
                generated_files.append(cover_letter_path)
            except Exception as e:
                print(f"Error generating cover letter for {company} - {title}: {e}")
                continue
        
        return generated_files 