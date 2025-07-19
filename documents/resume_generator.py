"""
This module is responsible for generating resumes and cover letters using the LLM model.
"""
# app/libs/resume_and_cover_builder/resume_generator.py
from string import Template
from typing import Any, Optional
from pathlib import Path
import yaml
from documents.llm.llm_generate_resume import LLMResumer
from documents.llm.llm_generate_resume_from_job import LLMResumeJobDescription
from documents.llm.llm_generate_cover_letter_from_job import LLMCoverLetterJobDescription
from documents.module_loader import load_module
from documents.config import global_config
from documents.resume_facade import ResumeFacade
from profiles.config import ConfigValidator, FileManager
from src.libs.resume_and_cover_builder.pdf_generator import PDFGenerator

class ResumeGenerator:
    def __init__(self, data_folder: Path = None):
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
        
        self.output_folder = output_folder
        self.set_resume_object(self.resume_data)
        
        # Set API key in global config
        global_config.API_KEY = self.llm_api_key
        
        # Set up module paths
        lib_directory = Path(__file__).resolve().parent
        global_config.STRINGS_MODULE_RESUME_PATH = lib_directory / "templates/resume_prompt/strings_feder-cr.py"
        global_config.STRINGS_MODULE_RESUME_JOB_DESCRIPTION_PATH = lib_directory / "templates/resume_job_description_prompt/strings_feder-cr.py"
        global_config.STRINGS_MODULE_COVER_LETTER_JOB_DESCRIPTION_PATH = lib_directory / "templates/cover_letter_prompt/strings_feder-cr.py"
        global_config.STRINGS_MODULE_NAME = "strings_feder_cr"
        global_config.STYLES_DIRECTORY = lib_directory / "styles"
        global_config.LOG_OUTPUT_FILE_PATH = Path(self.output_folder)
        
        # Initialize PDF generator
        self.pdf_generator = PDFGenerator()
    
    def _validate_setup(self):
        """Validate that all required files exist and are properly configured."""
        try:
            FileManager.validate_data_folder(self.data_folder)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Setup incomplete: {e}")
    
    def set_resume_object(self, resume_object):
         self.resume_object = resume_object
         

    def _create_resume(self, gpt_answerer: Any, style_path):
        # Imposta il resume nell'oggetto gpt_answerer
        gpt_answerer.set_resume(self.resume_object)
        
        # Leggi il template HTML
        template = Template(global_config.html_template)
        
        try:
            with open(style_path, "r") as f:
                style_css = f.read()  # Correzione: chiama il metodo `read` con le parentesi
        except FileNotFoundError:
            raise ValueError(f"Il file di stile non è stato trovato nel percorso: {style_path}")
        except Exception as e:
            raise RuntimeError(f"Errore durante la lettura del file CSS: {e}")
        
        # Genera l'HTML del resume
        body_html = gpt_answerer.generate_html_resume()
        
        # Applica i contenuti al template
        return template.substitute(body=body_html, style_css=style_css), style_css

    def create_resume(self, style_path):
        strings = load_module(global_config.STRINGS_MODULE_RESUME_PATH, global_config.STRINGS_MODULE_NAME)
        gpt_answerer = LLMResumer(global_config.API_KEY, strings)
        return self._create_resume(gpt_answerer, style_path)

    def create_resume_job_description_text(self, style_path: str, job_description_text: str):
        strings = load_module(global_config.STRINGS_MODULE_RESUME_JOB_DESCRIPTION_PATH, global_config.STRINGS_MODULE_NAME)
        gpt_answerer = LLMResumeJobDescription(global_config.API_KEY, strings)
        gpt_answerer.set_job_description_from_text(job_description_text)
        return self._create_resume(gpt_answerer, style_path)

    def create_cover_letter_job_description(self, style_path: str, job_description_text: str):
        strings = load_module(global_config.STRINGS_MODULE_COVER_LETTER_JOB_DESCRIPTION_PATH, global_config.STRINGS_MODULE_NAME)
        gpt_answerer = LLMCoverLetterJobDescription(global_config.API_KEY, strings)
        gpt_answerer.set_resume(self.resume_object)
        gpt_answerer.set_job_description_from_text(job_description_text)
        cover_letter_html = gpt_answerer.generate_cover_letter()
        template = Template(global_config.html_template)
        with open(style_path, "r") as f:
            style_css = f.read()
        return template.substitute(body=cover_letter_html, style_css=style_css), style_css
    
    def generate_standard_resume(self, output_path: Optional[str] = None, format: str = "pdf") -> str:
        """Generate a standard resume without job-specific tailoring.
        
        Args:
            output_path: Optional custom output path for the resume
            format: Output format ("pdf" or "html")
            
        Returns:
            Path to the generated resume file
        """
        # Use default style path
        style_path = Path("documents/styles/resume_style/style_josylad_blue.css")
        
        # Generate HTML resume
        html_content, css_content = self.create_resume(str(style_path))
        
        # Determine output path
        if output_path is None:
            base_name = "resume"
            output_path = self.output_folder / f"{base_name}.{format}"
        else:
            output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "pdf":
            # Generate both HTML and PDF
            base_path = str(output_path.with_suffix(""))
            html_path, pdf_path, success = self.pdf_generator.save_html_and_pdf(
                html_content, base_path, css_content
            )
            
            if success:
                print(f"✅ Resume generated successfully:")
                print(f"   HTML: {html_path}")
                print(f"   PDF:  {pdf_path}")
                return pdf_path
            else:
                print(f"⚠️  PDF generation failed, HTML saved: {html_path}")
                return html_path
        else:
            # Generate HTML only
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ Resume generated: {output_path}")
            return str(output_path)
    
    def generate_tailored_resume(self, job_description: str, output_path: Optional[str] = None, format: str = "pdf") -> str:
        """Generate a resume tailored for a specific job.
        
        Args:
            job_description: The job description to tailor the resume for
            output_path: Optional custom output path for the resume
            format: Output format ("pdf" or "html")
            
        Returns:
            Path to the generated resume file
        """
        if not job_description.strip():
            raise ValueError("Job description cannot be empty")
        
        # Use default style path
        style_path = Path("documents/styles/resume_style/style_josylad_blue.css")
        
        # Generate HTML resume tailored for job
        html_content, css_content = self.create_resume_job_description_text(str(style_path), job_description)
        
        # Determine output path
        if output_path is None:
            base_name = "resume_tailored"
            output_path = self.output_folder / f"{base_name}.{format}"
        else:
            output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "pdf":
            # Generate both HTML and PDF
            base_path = str(output_path.with_suffix(""))
            html_path, pdf_path, success = self.pdf_generator.save_html_and_pdf(
                html_content, base_path, css_content
            )
            
            if success:
                print(f"✅ Tailored resume generated successfully:")
                print(f"   HTML: {html_path}")
                print(f"   PDF:  {pdf_path}")
                return pdf_path
            else:
                print(f"⚠️  PDF generation failed, HTML saved: {html_path}")
                return html_path
        else:
            # Generate HTML only
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ Tailored resume generated: {output_path}")
            return str(output_path)