import os
import sys
from pathlib import Path

# Add project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_socketio import SocketIO, emit
import yaml
import json
import threading
import time
from typing import Dict, Any, Optional
import traceback
import tempfile
import base64

# Import existing functionality
from profiles.config import ConfigValidator, FileManager as ProfileFileManager, ConfigError
from documents.resume_generator import ResumeGenerator
from documents.cover_letter_generator import CoverLetterGenerator
from applications.manual_handler import ManualApplicationHandler
from applications.email_sender import EmailSender
from src.skills_extractor import extract_skills_from_text
from src.job_scoring import score_job
from src.excel_reporter import write_jobs_to_excel

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
socketio = SocketIO(app, cors_allowed_origins="*")

class WebFileManager:
    """Robust file management for the web UI that works in any deployment scenario."""
    
    @staticmethod
    def get_project_root():
        """Get the project root directory."""
        return PROJECT_ROOT
    
    @staticmethod
    def get_data_folder():
        """Get the data folder path."""
        return WebFileManager.get_project_root() / "data_folder"
    
    @staticmethod
    def get_output_folder():
        """Get the output folder path."""
        return WebFileManager.get_data_folder() / "output"
    
    @staticmethod
    def ensure_folders_exist():
        """Ensure all required folders exist."""
        data_folder = WebFileManager.get_data_folder()
        output_folder = WebFileManager.get_output_folder()
        
        data_folder.mkdir(exist_ok=True)
        output_folder.mkdir(exist_ok=True)
        
        return data_folder, output_folder
    
    @staticmethod
    def find_file(filename):
        """Find a file in common locations with comprehensive search."""
        if not filename:
            return None
            
        # Clean the filename - remove any path separators and get just the filename
        clean_filename = Path(filename).name
        
        # Define search locations in order of priority
        search_locations = [
            # 1. Direct path if it's absolute and exists
            Path(filename) if Path(filename).is_absolute() else None,
            
            # 2. In output folder (most common location)
            WebFileManager.get_output_folder() / clean_filename,
            
            # 3. In data folder
            WebFileManager.get_data_folder() / clean_filename,
            
            # 4. Relative to project root with original path
            WebFileManager.get_project_root() / filename,
            
            # 5. Relative to project root with clean filename
            WebFileManager.get_project_root() / clean_filename,
            
            # 6. In common output patterns
            WebFileManager.get_project_root() / "output" / clean_filename,
            WebFileManager.get_project_root() / "data" / clean_filename,
            
            # 7. As given (relative to current working directory)
            Path(filename),
            Path(clean_filename),
            
            # 8. In web_ui folder (in case files are generated there)
            WebFileManager.get_project_root() / "web_ui" / "data_folder" / "output" / clean_filename,
            WebFileManager.get_project_root() / "web_ui" / clean_filename,
        ]
        
        # Search through all locations
        for location in search_locations:
            if location and location.exists() and location.is_file():
                return location.resolve()  # Return absolute path
        
        return None
    
    @staticmethod
    def get_file_info(file_path):
        """Get file information for download."""
        if not file_path or not file_path.exists():
            return None
        
        return {
            'path': str(file_path),
            'name': file_path.name,
            'size': file_path.stat().st_size,
            'exists': True
        }
    
    @staticmethod
    def get_all_search_locations(filename):
        """Get all search locations for debugging purposes."""
        clean_filename = Path(filename).name if filename else ""
        
        return [
            str(Path(filename)) if Path(filename).is_absolute() else None,
            str(WebFileManager.get_output_folder() / clean_filename),
            str(WebFileManager.get_data_folder() / clean_filename),
            str(WebFileManager.get_project_root() / filename),
            str(WebFileManager.get_project_root() / clean_filename),
            str(WebFileManager.get_project_root() / "output" / clean_filename),
            str(WebFileManager.get_project_root() / "data" / clean_filename),
            str(Path(filename)),
            str(Path(clean_filename)),
            str(WebFileManager.get_project_root() / "web_ui" / "data_folder" / "output" / clean_filename),
            str(WebFileManager.get_project_root() / "web_ui" / clean_filename),
        ]

class UIBackend:
    """Backend service for the web UI."""
    
    def __init__(self):
        self.data_folder, self.output_folder = WebFileManager.ensure_folders_exist()
        
    def get_configuration_status(self) -> Dict[str, Any]:
        """Check configuration status and return details."""
        try:
            secrets_file, config_file, resume_file, output_folder = ProfileFileManager.validate_data_folder(self.data_folder)
            
            status = {
                'configured': True,
                'secrets_exists': secrets_file.exists(),
                'config_exists': config_file.exists(),
                'resume_exists': resume_file.exists(),
                'output_folder_exists': output_folder.exists(),
                'files': {
                    'secrets': str(secrets_file),
                    'config': str(config_file),
                    'resume': str(resume_file),
                    'output': str(output_folder)
                }
            }
            
            # Try to validate configuration
            try:
                ConfigValidator.validate_secrets(secrets_file)
                ConfigValidator.validate_config(config_file)
                status['valid_configuration'] = True
            except (FileNotFoundError, ConfigError) as e:
                status['valid_configuration'] = False
                status['validation_error'] = str(e)
                
            return status
            
        except Exception as e:
            return {
                'configured': False,
                'error': str(e),
                'valid_configuration': False
            }
    
    def save_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save configuration from UI form."""
        try:
            # Save secrets
            secrets_file = self.data_folder / "secrets.yaml"
            secrets = {
                'llm_api_key': config_data.get('openai_api_key', '')
            }
            
            if config_data.get('email_enabled'):
                secrets['email'] = {
                    'smtp_server': config_data.get('smtp_server', 'smtp.gmail.com'),
                    'smtp_port': int(config_data.get('smtp_port', 587)),
                    'email_address': config_data.get('email_address', ''),
                    'email_password': config_data.get('email_password', '')
                }
            
            with open(secrets_file, 'w') as f:
                yaml.dump(secrets, f, default_flow_style=False)
            
            # Save work preferences
            prefs_file = self.data_folder / "work_preferences.yaml"
            prefs = {
                'remote': config_data.get('remote_work', True),
                'hybrid': config_data.get('hybrid_work', True),
                'onsite': config_data.get('onsite_work', True),
                'positions': config_data.get('positions', ['Software Engineer']),
                'locations': config_data.get('locations', ['Remote']),
                'distance': int(config_data.get('distance', 100)),
                'apply_once_at_company': config_data.get('apply_once_at_company', True)
            }
            
            with open(prefs_file, 'w') as f:
                yaml.dump(prefs, f, default_flow_style=False)
            
            # Save resume data
            resume_file = self.data_folder / "plain_text_resume.yaml"
            resume_data = {
                'personal_information': {
                    'name': config_data.get('name', ''),
                    'surname': config_data.get('surname', ''),
                    'email': config_data.get('email', ''),
                    'phone': config_data.get('phone', ''),
                    'linkedin': config_data.get('linkedin', ''),
                    'github': config_data.get('github', '')
                },
                'summary': config_data.get('summary', ''),
                'experience_details': config_data.get('experience', []),
                'education_details': config_data.get('education', []),
                'skills': config_data.get('skills', []),
                'languages': config_data.get('languages', []),
                'interests': config_data.get('interests', [])
            }
            
            with open(resume_file, 'w') as f:
                yaml.dump(resume_data, f, default_flow_style=False)
            
            return {'success': True, 'message': 'Configuration saved successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load existing configuration for editing."""
        try:
            config = {}
            
            # Load secrets
            secrets_file = self.data_folder / "secrets.yaml"
            if secrets_file.exists():
                with open(secrets_file, 'r') as f:
                    secrets = yaml.safe_load(f) or {}
                    config['openai_api_key'] = secrets.get('llm_api_key', '')
                    if 'email' in secrets:
                        config.update({
                            'email_enabled': True,
                            'smtp_server': secrets['email'].get('smtp_server', 'smtp.gmail.com'),
                            'smtp_port': secrets['email'].get('smtp_port', 587),
                            'email_address': secrets['email'].get('email_address', ''),
                            'email_password': secrets['email'].get('email_password', '')
                        })
            
            # Load work preferences
            prefs_file = self.data_folder / "work_preferences.yaml"
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    prefs = yaml.safe_load(f) or {}
                    config.update({
                        'remote_work': prefs.get('remote', True),
                        'hybrid_work': prefs.get('hybrid', True),
                        'onsite_work': prefs.get('onsite', True),
                        'positions': prefs.get('positions', ['Software Engineer']),
                        'locations': prefs.get('locations', ['Remote']),
                        'distance': prefs.get('distance', 100),
                        'apply_once_at_company': prefs.get('apply_once_at_company', True)
                    })
            
            # Load resume data
            resume_file = self.data_folder / "plain_text_resume.yaml"
            if resume_file.exists():
                with open(resume_file, 'r') as f:
                    resume_data = yaml.safe_load(f) or {}
                    personal = resume_data.get('personal_information', {})
                    config.update({
                        'name': personal.get('name', ''),
                        'surname': personal.get('surname', ''),
                        'email': personal.get('email', ''),
                        'phone': personal.get('phone', ''),
                        'linkedin': personal.get('linkedin', ''),
                        'github': personal.get('github', ''),
                        'summary': resume_data.get('summary', ''),
                        'experience': resume_data.get('experience_details', []),
                        'education': resume_data.get('education_details', []),
                        'skills': resume_data.get('skills', []),
                        'languages': resume_data.get('languages', []),
                        'interests': resume_data.get('interests', [])
                    })
            
            return config
            
        except Exception as e:
            return {'error': str(e)}
    
    def generate_resume(self, job_description: Optional[str] = None, output_format: str = 'pdf') -> Dict[str, Any]:
        """Generate resume using existing functionality."""
        try:
            # Change to project root directory for generation
            original_cwd = os.getcwd()
            os.chdir(WebFileManager.get_project_root())
            
            resume_generator = ResumeGenerator()
            
            if job_description:
                result = resume_generator.generate_tailored_resume(job_description, format=output_format)
            else:
                result = resume_generator.generate_standard_resume(format=output_format)
            
            # Find the generated file
            file_path = WebFileManager.find_file(str(result))
            if file_path:
                result = file_path
            
            return {
                'success': True,
                'file_path': str(result),
                'file_info': WebFileManager.get_file_info(file_path) if file_path else None,
                'message': 'Resume generated successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def generate_cover_letter(self, job_description: str, output_format: str = 'pdf') -> Dict[str, Any]:
        """Generate cover letter using existing functionality."""
        try:
            # Change to project root directory for generation
            original_cwd = os.getcwd()
            os.chdir(WebFileManager.get_project_root())
            
            cover_generator = CoverLetterGenerator()
            result = cover_generator.generate_cover_letter(job_description, format=output_format)
            
            # Find the generated file
            file_path = WebFileManager.find_file(str(result))
            if file_path:
                result = file_path
            
            return {
                'success': True,
                'file_path': str(result),
                'file_info': WebFileManager.get_file_info(file_path) if file_path else None,
                'message': 'Cover letter generated successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
    
    def get_manual_applications(self) -> Dict[str, Any]:
        """Get list of manual applications."""
        try:
            handler = ManualApplicationHandler()
            applications = handler.get_manual_applications()
            
            return {
                'success': True,
                'applications': applications
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_email_configuration(self) -> Dict[str, Any]:
        """Test email configuration."""
        try:
            email_sender = EmailSender()
            # Test by sending a test email to yourself
            result = email_sender.test_connection()
            
            return {
                'success': True,
                'message': 'Email configuration is working'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Initialize backend
backend = UIBackend()

# Routes
@app.route('/')
def index():
    """Main dashboard page."""
    config_status = backend.get_configuration_status()
    return render_template('index.html', config_status=config_status)

@app.route('/setup')
def setup():
    """Configuration setup page."""
    config = backend.load_configuration()
    return render_template('setup.html', config=config)

@app.route('/api/save-config', methods=['POST'])
def save_config():
    """API endpoint to save configuration."""
    try:
        config_data = request.json
        result = backend.save_configuration(config_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/config-status')
def config_status():
    """API endpoint to get configuration status."""
    return jsonify(backend.get_configuration_status())

@app.route('/generate')
def generate():
    """Document generation page."""
    return render_template('generate.html')

@app.route('/api/generate-resume', methods=['POST'])
def generate_resume_api():
    """API endpoint to generate resume."""
    try:
        data = request.json
        job_description = data.get('job_description')
        output_format = data.get('format', 'pdf')
        
        result = backend.generate_resume(job_description, output_format)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-cover-letter', methods=['POST'])
def generate_cover_letter_api():
    """API endpoint to generate cover letter."""
    try:
        data = request.json
        job_description = data.get('job_description', '')
        output_format = data.get('format', 'pdf')
        
        if not job_description:
            return jsonify({'success': False, 'error': 'Job description is required'})
        
        result = backend.generate_cover_letter(job_description, output_format)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/manual')
def manual():
    """Manual applications management page."""
    applications = backend.get_manual_applications()
    return render_template('manual.html', applications=applications)

@app.route('/api/test-email', methods=['POST'])
def test_email_api():
    """API endpoint to test email configuration."""
    result = backend.test_email_configuration()
    return jsonify(result)

@app.route('/api/files')
def list_files():
    """List available files for download."""
    try:
        output_folder = WebFileManager.get_output_folder()
        files = []
        
        if output_folder.exists():
            for file_path in output_folder.iterdir():
                if file_path.is_file():
                    file_info = WebFileManager.get_file_info(file_path)
                    if file_info:
                        files.append({
                            'name': file_info['name'],
                            'path': str(file_path.relative_to(WebFileManager.get_project_root())),
                            'size': file_info['size'],
                            'download_url': f'/download/{file_info["name"]}'
                        })
        
        return jsonify({
            'success': True,
            'files': files,
            'output_folder': str(output_folder)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/system-info')
def system_info():
    """Get comprehensive system information for debugging."""
    try:
        output_folder = WebFileManager.get_output_folder()
        data_folder = WebFileManager.get_data_folder()
        
        info = {
            'project_root': str(WebFileManager.get_project_root()),
            'data_folder': str(data_folder),
            'output_folder': str(output_folder),
            'current_working_directory': os.getcwd(),
            'flask_app_location': str(Path(__file__)),
            'python_path': sys.path[:3],  # First 3 entries
            'folders_exist': {
                'data_folder': data_folder.exists(),
                'output_folder': output_folder.exists()
            },
            'files_in_output': [],
            'files_in_data': [],
            'sample_search_locations': WebFileManager.get_all_search_locations('cover_letter.pdf')
        }
        
        # List files in output folder
        if output_folder.exists():
            info['files_in_output'] = [
                {
                    'name': f.name,
                    'path': str(f),
                    'size': f.stat().st_size,
                    'is_file': f.is_file()
                }
                for f in output_folder.iterdir()
            ]
        
        # List files in data folder
        if data_folder.exists():
            info['files_in_data'] = [
                {
                    'name': f.name,
                    'path': str(f),
                    'size': f.stat().st_size if f.is_file() else None,
                    'is_file': f.is_file()
                }
                for f in data_folder.iterdir()
            ]
        
        return jsonify({
            'success': True,
            'system_info': info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/debug/paths')
def debug_paths():
    """Debug endpoint to check file paths."""
    import os
    project_root = Path(__file__).parent.parent
    data_folder = project_root / 'data_folder' / 'output'
    
    debug_info = {
        'current_working_directory': os.getcwd(),
        'flask_app_file': str(Path(__file__)),
        'project_root': str(project_root),
        'data_folder_output': str(data_folder),
        'data_folder_exists': data_folder.exists(),
        'cover_letter_pdf_exists': (data_folder / 'cover_letter.pdf').exists(),
        'files_in_data_folder': list(str(f) for f in data_folder.iterdir()) if data_folder.exists() else []
    }
    
    return jsonify(debug_info)

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download generated files with robust path resolution that works in any deployment scenario."""
    try:
        import urllib.parse
        # URL decode the filename
        decoded_filename = urllib.parse.unquote(filename)
        
        # Use WebFileManager to find the file with comprehensive search
        file_path = WebFileManager.find_file(decoded_filename)
        
        if file_path and file_path.exists():
            # Get file info for logging
            file_info = WebFileManager.get_file_info(file_path)
            app.logger.info(f"Successfully serving file: {file_info}")
            
            return send_file(
                file_path, 
                as_attachment=True,
                download_name=file_path.name
            )
        else:
            # Provide comprehensive error information for debugging
            search_info = {
                'requested_file': decoded_filename,
                'project_root': str(WebFileManager.get_project_root()),
                'data_folder': str(WebFileManager.get_data_folder()),
                'output_folder': str(WebFileManager.get_output_folder()),
                'current_working_directory': os.getcwd(),
                'flask_app_location': str(Path(__file__)),
                'searched_locations': WebFileManager.get_all_search_locations(decoded_filename),
                'existing_files_in_output': []
            }
            
            # List existing files in output folder for debugging
            output_folder = WebFileManager.get_output_folder()
            if output_folder.exists():
                search_info['existing_files_in_output'] = [
                    str(f) for f in output_folder.iterdir() if f.is_file()
                ]
            
            app.logger.error(f"File not found: {decoded_filename}. Search info: {search_info}")
            
            return jsonify({
                'error': f'File not found: {decoded_filename}',
                'message': 'The requested file could not be found in any of the expected locations.',
                'debug_info': search_info
            }), 404
            
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'requested_file': filename,
            'project_root': str(WebFileManager.get_project_root()),
            'current_working_directory': os.getcwd()
        }
        app.logger.error(f"Download error: {error_info}")
        
        return jsonify({
            'error': f'Download failed: {str(e)}',
            'debug_info': error_info
        }), 500

# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    emit('connected', {'message': 'Connected to Job Application Automation'})

@socketio.on('generate_document')
def handle_generate_document(data):
    """Handle document generation with real-time updates."""
    try:
        doc_type = data.get('type')
        job_description = data.get('job_description')
        output_format = data.get('format', 'pdf')
        
        emit('status', {'message': f'Starting {doc_type} generation...'})
        
        if doc_type == 'resume':
            result = backend.generate_resume(job_description, output_format)
        elif doc_type == 'cover_letter':
            result = backend.generate_cover_letter(job_description, output_format)
        else:
            result = {'success': False, 'error': 'Invalid document type'}
        
        emit('generation_complete', result)
        
    except Exception as e:
        emit('error', {'message': str(e)})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 