import typer
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
import inquirer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

from profiles.config import ConfigValidator, FileManager, ConfigError
from documents.resume_generator import ResumeGenerator
from documents.cover_letter_generator import CoverLetterGenerator
from applications.manual_handler import ManualApplicationHandler

app = typer.Typer(help="AI-powered job application automation tool")
console = Console()

# Configuration wizard functions
def run_setup_wizard():
    """Run the comprehensive setup wizard for all configuration files."""
    console.print("\n[bold blue]🚀 Welcome to the Job Application Automation Setup Wizard![/bold blue]")
    console.print("This wizard will help you configure all necessary settings.\n")
    
    data_folder = Path("data_folder")
    data_folder.mkdir(exist_ok=True)
    
    # Run each configuration section
    setup_secrets(data_folder)
    setup_work_preferences(data_folder)
    setup_personal_profile(data_folder)
    
    console.print("\n[bold green]✅ Setup complete! You can now run the job application automation.[/bold green]")
    console.print("Run [bold]python -m cli.main run[/bold] to start applying for jobs.")

def setup_secrets(data_folder: Path):
    """Configure API keys and credentials."""
    console.print("\n[bold yellow]🔑 Setting up API Keys and Credentials[/bold yellow]")
    
    secrets_file = data_folder / "secrets.yaml"
    secrets = {}
    
    if secrets_file.exists():
        with open(secrets_file, 'r') as f:
            secrets = yaml.safe_load(f) or {}
    
    # OpenAI API Key
    if not secrets.get('llm_api_key'):
        api_key = typer.prompt("Enter your OpenAI API key", hide_input=True)
        secrets['llm_api_key'] = api_key
    
    # Email configuration for job applications
    console.print("\n[bold]Email Configuration (for sending applications)[/bold]")
    
    email_questions = [
        inquirer.Confirm('setup_email', message="Do you want to configure email sending?", default=True),
    ]
    email_answers = inquirer.prompt(email_questions)
    
    if email_answers['setup_email']:
        secrets['email'] = {}
        secrets['email']['smtp_server'] = typer.prompt("SMTP Server (e.g., smtp.gmail.com)", default="smtp.gmail.com")
        secrets['email']['smtp_port'] = typer.prompt("SMTP Port", default=587, type=int)
        secrets['email']['email_address'] = typer.prompt("Your email address")
        secrets['email']['email_password'] = typer.prompt("Email password (or app password)", hide_input=True)
    
    # LinkedIn credentials (optional)
    linkedin_questions = [
        inquirer.Confirm('setup_linkedin', message="Do you want to configure LinkedIn automation?", default=False),
    ]
    linkedin_answers = inquirer.prompt(linkedin_questions)
    
    if linkedin_answers['setup_linkedin']:
        secrets['linkedin'] = {}
        secrets['linkedin']['username'] = typer.prompt("LinkedIn username/email")
        secrets['linkedin']['password'] = typer.prompt("LinkedIn password", hide_input=True)
    
    # Save secrets
    with open(secrets_file, 'w') as f:
        yaml.dump(secrets, f, default_flow_style=False)
    
    console.print("[green]✅ Secrets configured successfully![/green]")

def setup_work_preferences(data_folder: Path):
    """Configure job search preferences and filters."""
    console.print("\n[bold yellow]💼 Setting up Job Search Preferences[/bold yellow]")
    
    prefs_file = data_folder / "work_preferences.yaml"
    prefs = {}
    
    if prefs_file.exists():
        with open(prefs_file, 'r') as f:
            prefs = yaml.safe_load(f) or {}
    
    # Work arrangement preferences
    console.print("\n[bold]Work Arrangement Preferences[/bold]")
    work_arrangement_questions = [
        inquirer.Confirm('remote', message="Accept remote positions?", default=prefs.get('remote', True)),
        inquirer.Confirm('hybrid', message="Accept hybrid positions?", default=prefs.get('hybrid', True)),
        inquirer.Confirm('onsite', message="Accept onsite positions?", default=prefs.get('onsite', True)),
    ]
    work_answers = inquirer.prompt(work_arrangement_questions)
    prefs.update(work_answers)
    
    # Experience level
    console.print("\n[bold]Experience Level Preferences[/bold]")
    experience_levels = {
        'internship': 'Internship',
        'entry': 'Entry Level',
        'associate': 'Associate',
        'mid_senior_level': 'Mid-Senior Level',
        'director': 'Director',
        'executive': 'Executive'
    }
    
    exp_questions = []
    for key, label in experience_levels.items():
        default_val = prefs.get('experience_level', {}).get(key, key in ['entry', 'associate', 'mid_senior_level'])
        exp_questions.append(inquirer.Confirm(key, message=f"Apply for {label} positions?", default=default_val))
    
    exp_answers = inquirer.prompt(exp_questions)
    prefs['experience_level'] = exp_answers
    
    # Job types
    console.print("\n[bold]Job Type Preferences[/bold]")
    job_types = {
        'full_time': 'Full-time',
        'contract': 'Contract',
        'part_time': 'Part-time',
        'temporary': 'Temporary',
        'internship': 'Internship',
        'other': 'Other',
        'volunteer': 'Volunteer'
    }
    
    job_questions = []
    for key, label in job_types.items():
        default_val = prefs.get('job_types', {}).get(key, key in ['full_time', 'temporary', 'volunteer'])
        job_questions.append(inquirer.Confirm(key, message=f"Apply for {label} positions?", default=default_val))
    
    job_answers = inquirer.prompt(job_questions)
    prefs['job_types'] = job_answers
    
    # Date filters
    console.print("\n[bold]Job Posting Date Preferences[/bold]")
    date_options = [
        ('24_hours', '24 hours'),
        ('week', 'Past week'),
        ('month', 'Past month'),
        ('all_time', 'All time')
    ]
    
    date_question = [
        inquirer.List('date_filter', 
                     message="How recent should job postings be?",
                     choices=[label for _, label in date_options],
                     default='24 hours')
    ]
    date_answer = inquirer.prompt(date_question)
    
    # Convert back to the key format
    selected_date = next(key for key, label in date_options if label == date_answer['date_filter'])
    prefs['date'] = {key: (key == selected_date) for key, _ in date_options}
    
    # Job positions and locations
    console.print("\n[bold]Job Positions and Locations[/bold]")
    
    current_positions = prefs.get('positions', ['Software Engineer'])
    positions_str = typer.prompt("Enter job positions (comma-separated)", default=', '.join(current_positions))
    prefs['positions'] = [pos.strip() for pos in positions_str.split(',')]
    
    current_locations = prefs.get('locations', ['Germany'])
    locations_str = typer.prompt("Enter preferred locations (comma-separated)", default=', '.join(current_locations))
    prefs['locations'] = [loc.strip() for loc in locations_str.split(',')]
    
    # Distance and other preferences
    distance_options = [0, 5, 10, 25, 50, 100]
    distance_question = [
        inquirer.List('distance',
                     message="Maximum distance from location (km)",
                     choices=[str(d) for d in distance_options],
                     default=str(prefs.get('distance', 100)))
    ]
    distance_answer = inquirer.prompt(distance_question)
    prefs['distance'] = int(distance_answer['distance'])
    
    prefs['apply_once_at_company'] = typer.confirm("Apply only once per company?", default=prefs.get('apply_once_at_company', True))
    
    # Blacklists
    console.print("\n[bold]Blacklists (Optional)[/bold]")
    
    current_company_blacklist = prefs.get('company_blacklist', [])
    if current_company_blacklist:
        company_blacklist_str = typer.prompt("Companies to avoid (comma-separated)", default=', '.join(current_company_blacklist))
    else:
        company_blacklist_str = typer.prompt("Companies to avoid (comma-separated, press Enter to skip)", default="")
    
    if company_blacklist_str.strip():
        prefs['company_blacklist'] = [company.strip() for company in company_blacklist_str.split(',')]
    else:
        prefs['company_blacklist'] = []
    
    current_title_blacklist = prefs.get('title_blacklist', [])
    if current_title_blacklist:
        title_blacklist_str = typer.prompt("Job titles to avoid (comma-separated)", default=', '.join(current_title_blacklist))
    else:
        title_blacklist_str = typer.prompt("Job titles to avoid (comma-separated, press Enter to skip)", default="")
    
    if title_blacklist_str.strip():
        prefs['title_blacklist'] = [title.strip() for title in title_blacklist_str.split(',')]
    else:
        prefs['title_blacklist'] = []
    
    current_location_blacklist = prefs.get('location_blacklist', [])
    if current_location_blacklist:
        location_blacklist_str = typer.prompt("Locations to avoid (comma-separated)", default=', '.join(current_location_blacklist))
    else:
        location_blacklist_str = typer.prompt("Locations to avoid (comma-separated, press Enter to skip)", default="")
    
    if location_blacklist_str.strip():
        prefs['location_blacklist'] = [location.strip() for location in location_blacklist_str.split(',')]
    else:
        prefs['location_blacklist'] = []
    
    # Save preferences
    with open(prefs_file, 'w') as f:
        yaml.dump(prefs, f, default_flow_style=False)
    
    console.print("[green]✅ Work preferences configured successfully![/green]")

def setup_personal_profile(data_folder: Path):
    """Configure personal information and resume profile."""
    console.print("\n[bold yellow]👤 Setting up Personal Profile[/bold yellow]")
    
    profile_file = data_folder / "plain_text_resume.yaml"
    profile = {}
    
    if profile_file.exists():
        with open(profile_file, 'r') as f:
            profile = yaml.safe_load(f) or {}
    
    # Personal Information
    console.print("\n[bold]Personal Information[/bold]")
    personal_info = profile.get('personal_information', {})
    
    personal_info['name'] = typer.prompt("First Name", default=personal_info.get('name', ''))
    personal_info['surname'] = typer.prompt("Last Name", default=personal_info.get('surname', ''))
    personal_info['email'] = typer.prompt("Email Address", default=personal_info.get('email', ''))
    personal_info['phone'] = typer.prompt("Phone Number", default=personal_info.get('phone', ''))
    personal_info['phone_prefix'] = typer.prompt("Phone Country Code", default=personal_info.get('phone_prefix', '+1'))
    
    # Address
    personal_info['country'] = typer.prompt("Country", default=personal_info.get('country', ''))
    personal_info['city'] = typer.prompt("City", default=personal_info.get('city', ''))
    personal_info['address'] = typer.prompt("Address", default=personal_info.get('address', ''))
    personal_info['zip_code'] = typer.prompt("ZIP/Postal Code", default=personal_info.get('zip_code', ''))
    
    # Optional fields
    personal_info['date_of_birth'] = typer.prompt("Date of Birth (DD-MM-YYYY)", default=personal_info.get('date_of_birth', ''))
    personal_info['linkedin'] = typer.prompt("LinkedIn Profile URL", default=personal_info.get('linkedin', ''))
    personal_info['github'] = typer.prompt("GitHub Profile URL", default=personal_info.get('github', ''))
    
    profile['personal_information'] = personal_info
    
    # Legal Authorization
    console.print("\n[bold]Work Authorization[/bold]")
    legal_auth = profile.get('legal_authorization', {})
    
    countries = [
        ('us', 'United States'),
        ('eu', 'European Union'),
        ('canada', 'Canada'),
        ('uk', 'United Kingdom')
    ]
    
    for country_code, country_name in countries:
        console.print(f"\n[bold]{country_name} Work Authorization[/bold]")
        
        auth_key = f"{country_code}_work_authorization"
        visa_key = f"requires_{country_code}_visa"
        sponsor_key = f"requires_{country_code}_sponsorship"
        legal_key = f"legally_allowed_to_work_in_{country_code}"
        
        legal_auth[auth_key] = "Yes" if typer.confirm(f"Are you authorized to work in {country_name}?", 
                                                     default=legal_auth.get(auth_key, 'No') == 'Yes') else "No"
        
        if legal_auth[auth_key] == "No":
            legal_auth[visa_key] = "Yes" if typer.confirm(f"Do you require a visa to work in {country_name}?", 
                                                         default=legal_auth.get(visa_key, 'Yes') == 'Yes') else "No"
            legal_auth[sponsor_key] = "Yes" if typer.confirm(f"Do you require sponsorship to work in {country_name}?", 
                                                            default=legal_auth.get(sponsor_key, 'Yes') == 'Yes') else "No"
        
        legal_auth[legal_key] = "Yes" if typer.confirm(f"Are you legally allowed to work in {country_name}?", 
                                                      default=legal_auth.get(legal_key, 'Yes') == 'Yes') else "No"
    
    profile['legal_authorization'] = legal_auth
    
    # Work Preferences
    console.print("\n[bold]Work Preferences[/bold]")
    work_prefs = profile.get('work_preferences', {})
    
    work_prefs['remote_work'] = "Yes" if typer.confirm("Are you open to remote work?", 
                                                      default=work_prefs.get('remote_work', 'Yes') == 'Yes') else "No"
    work_prefs['in_person_work'] = "Yes" if typer.confirm("Are you open to in-person work?", 
                                                         default=work_prefs.get('in_person_work', 'Yes') == 'Yes') else "No"
    work_prefs['open_to_relocation'] = "Yes" if typer.confirm("Are you open to relocation?", 
                                                             default=work_prefs.get('open_to_relocation', 'No') == 'Yes') else "No"
    work_prefs['willing_to_complete_assessments'] = "Yes" if typer.confirm("Are you willing to complete assessments?", 
                                                                          default=work_prefs.get('willing_to_complete_assessments', 'Yes') == 'Yes') else "No"
    work_prefs['willing_to_undergo_drug_tests'] = "Yes" if typer.confirm("Are you willing to undergo drug tests?", 
                                                                        default=work_prefs.get('willing_to_undergo_drug_tests', 'Yes') == 'Yes') else "No"
    work_prefs['willing_to_undergo_background_checks'] = "Yes" if typer.confirm("Are you willing to undergo background checks?", 
                                                                               default=work_prefs.get('willing_to_undergo_background_checks', 'Yes') == 'Yes') else "No"
    
    profile['work_preferences'] = work_prefs
    
    # Self Identification
    console.print("\n[bold]Self Identification (Optional)[/bold]")
    self_id = profile.get('self_identification', {})
    
    if typer.confirm("Would you like to provide self-identification information?", default=False):
        gender_options = ['Male', 'Female', 'Non-binary', 'Prefer not to say']
        gender_question = [
            inquirer.List('gender',
                         message="Gender",
                         choices=gender_options,
                         default=self_id.get('gender', 'Prefer not to say'))
        ]
        gender_answer = inquirer.prompt(gender_question)
        self_id['gender'] = gender_answer['gender']
        
        self_id['pronouns'] = typer.prompt("Pronouns", default=self_id.get('pronouns', 'They/Them'))
        self_id['veteran'] = "Yes" if typer.confirm("Are you a veteran?", default=self_id.get('veteran', 'No') == 'Yes') else "No"
        self_id['disability'] = "Yes" if typer.confirm("Do you have a disability?", default=self_id.get('disability', 'No') == 'Yes') else "No"
        self_id['ethnicity'] = typer.prompt("Ethnicity (optional)", default=self_id.get('ethnicity', ''))
    
    profile['self_identification'] = self_id
    
    # Availability
    console.print("\n[bold]Availability[/bold]")
    availability = profile.get('availability', {})
    availability['notice_period'] = typer.prompt("Notice period", default=availability.get('notice_period', '2 weeks'))
    profile['availability'] = availability
    
    # Languages
    console.print("\n[bold]Languages[/bold]")
    languages = profile.get('languages', [])
    
    if not languages:
        languages = [{'language': 'English', 'proficiency': 'Fluent'}]
    
    if typer.confirm("Would you like to add/edit languages?", default=False):
        languages = []
        while True:
            language = typer.prompt("Language name")
            proficiency_options = ['Native', 'Fluent', 'Conversational', 'Basic']
            proficiency_question = [
                inquirer.List('proficiency',
                             message=f"Proficiency level for {language}",
                             choices=proficiency_options,
                             default='Fluent')
            ]
            proficiency_answer = inquirer.prompt(proficiency_question)
            
            languages.append({
                'language': language,
                'proficiency': proficiency_answer['proficiency']
            })
            
            if not typer.confirm("Add another language?", default=False):
                break
    
    profile['languages'] = languages
    
    # Interests
    console.print("\n[bold]Interests[/bold]")
    current_interests = profile.get('interests', [])
    if current_interests:
        interests_str = typer.prompt("Interests (comma-separated)", default=', '.join(current_interests))
    else:
        interests_str = typer.prompt("Interests (comma-separated)", default="")
    
    if interests_str.strip():
        profile['interests'] = [interest.strip() for interest in interests_str.split(',')]
    else:
        profile['interests'] = []
    
    # Initialize other required sections if they don't exist
    if 'education_details' not in profile:
        profile['education_details'] = []
    if 'experience_details' not in profile:
        profile['experience_details'] = []
    if 'achievements' not in profile:
        profile['achievements'] = []
    
    # Save profile
    with open(profile_file, 'w') as f:
        yaml.dump(profile, f, default_flow_style=False, allow_unicode=True)
    
    console.print("[green]✅ Personal profile configured successfully![/green]")

def check_configuration() -> bool:
    """Check if all required configuration files exist and are valid."""
    try:
        data_folder = Path("data_folder")
        secrets_file, config_file, resume_file, output_folder = FileManager.validate_data_folder(data_folder)
        
        # Validate each file
        ConfigValidator.validate_secrets(secrets_file)
        ConfigValidator.validate_config(config_file)
        
        return True
    except (FileNotFoundError, ConfigError) as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        return False

def show_configuration_status():
    """Show the current configuration status."""
    console.print("\n[bold blue]📋 Configuration Status[/bold blue]")
    
    data_folder = Path("data_folder")
    files_to_check = [
        ("secrets.yaml", "API Keys & Credentials"),
        ("work_preferences.yaml", "Job Search Preferences"),
        ("plain_text_resume.yaml", "Personal Profile")
    ]
    
    table = Table(title="Configuration Files")
    table.add_column("File", style="cyan")
    table.add_column("Description", style="magenta")
    table.add_column("Status", style="green")
    
    for filename, description in files_to_check:
        file_path = data_folder / filename
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    content = yaml.safe_load(f)
                    if content:
                        status = "✅ Configured"
                    else:
                        status = "❌ Empty"
            except Exception:
                status = "❌ Invalid"
        else:
            status = "❌ Missing"
        
        table.add_row(filename, description, status)
    
    console.print(table)

# Main CLI commands
@app.command()
def setup():
    """Run the comprehensive setup wizard."""
    run_setup_wizard()

@app.command()
def status():
    """Show configuration status."""
    show_configuration_status()

@app.command()
def run():
    """Run the job application automation."""
    if not check_configuration():
        console.print("\n[yellow]⚠️  Configuration issues detected. Running setup wizard...[/yellow]")
        run_setup_wizard()
        return
    
    console.print("\n[bold green]🚀 Starting job application automation...[/bold green]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing automation...", total=None)
        
        # Simulate some work
        time.sleep(2)
        progress.update(task, description="Loading configuration...")
        time.sleep(1)
        progress.update(task, description="Ready to apply for jobs!")
        time.sleep(1)
    
    console.print("[green]✅ Automation started successfully![/green]")
    console.print("Check the logs for detailed progress information.")

@app.command()
def generate_resume(
    job_description: Optional[str] = typer.Option(None, "--job-description", "-j", help="Job description to tailor resume for"),
    output_path: Optional[str] = typer.Option(None, "--output", "-o", help="Output path for the resume"),
    format: str = typer.Option("pdf", "--format", "-f", help="Output format (pdf, html)")
):
    """Generate a resume, optionally tailored for a specific job."""
    if not check_configuration():
        console.print("[red]Please run setup first: python -m cli.main setup[/red]")
        return
    
    console.print("\n[bold blue]📄 Generating Resume...[/bold blue]")
    
    try:
        resume_generator = ResumeGenerator()
        
        if job_description:
            console.print("Tailoring resume for the provided job description...")
            resume_path = resume_generator.generate_tailored_resume(job_description, output_path, format=format)
        else:
            console.print("Generating standard resume...")
            resume_path = resume_generator.generate_standard_resume(output_path, format=format)
        
        console.print(f"[green]✅ Resume generated successfully: {resume_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error generating resume: {e}[/red]")

@app.command()
def generate_cover_letter(
    job_description: str = typer.Argument(..., help="Job description to generate cover letter for"),
    output_path: Optional[str] = typer.Option(None, "--output", "-o", help="Output path for the cover letter"),
    format: str = typer.Option("pdf", "--format", "-f", help="Output format (pdf, html, txt)")
):
    """Generate a cover letter for a specific job."""
    if not check_configuration():
        console.print("[red]Please run setup first: python -m cli.main setup[/red]")
        return
    
    console.print("\n[bold blue]📝 Generating Cover Letter...[/bold blue]")
    
    try:
        cover_letter_generator = CoverLetterGenerator()
        cover_letter_path = cover_letter_generator.generate_cover_letter(job_description, output_path, format=format)
        
        console.print(f"[green]✅ Cover letter generated successfully: {cover_letter_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error generating cover letter: {e}[/red]")

@app.command()
def review_manual():
    """Review and process jobs that require manual application."""
    console.print("\n[bold blue]📋 Reviewing Manual Applications...[/bold blue]")
    
    try:
        handler = ManualApplicationHandler()
        manual_jobs = handler.get_pending_manual_jobs()
        
        if not manual_jobs:
            console.print("[green]No manual applications pending![/green]")
            return
        
        console.print(f"Found {len(manual_jobs)} jobs requiring manual application:")
        
        for i, job in enumerate(manual_jobs, 1):
            console.print(f"\n[bold]{i}. {job.title} at {job.company}[/bold]")
            console.print(f"   Location: {job.location}")
            console.print(f"   URL: {job.link}")
            console.print(f"   Reason: {job.manual_reason}")
            
            action = typer.prompt(
                "Action [a]pply manually / [s]kip / [q]uit",
                type=str,
                default="s"
            ).lower()
            
            if action == 'a':
                handler.mark_as_applied(job)
                console.print("[green]✅ Marked as applied[/green]")
            elif action == 'q':
                break
            else:
                console.print("[yellow]⏭️  Skipped[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error reviewing manual applications: {e}[/red]")

@app.command()
def test_email():
    """Test email sending functionality."""
    console.print("\n[bold blue]📧 Testing Email Functionality...[/bold blue]")
    
    # Import here to avoid circular imports
    from applications.email_sender import EmailSender
    
    # Check if SMTP configuration exists
    import os
    required_env_vars = ['SMTP_SERVER', 'SMTP_USER', 'SMTP_PASSWORD']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        console.print(f"[red]Missing required environment variables: {', '.join(missing_vars)}[/red]")
        console.print("[yellow]Please set these in your .env file or environment:[/yellow]")
        console.print("  SMTP_SERVER=smtp.gmail.com")
        console.print("  SMTP_PORT=587")
        console.print("  SMTP_USER=your_email@gmail.com")
        console.print("  SMTP_PASSWORD=your_app_password")
        return
    
    # Get test email details
    test_email = typer.prompt("Enter test email address")
    subject = typer.prompt("Enter email subject", default="Test Email from Job Application Bot")
    
    # Generate test documents
    console.print("\n[yellow]Generating test documents...[/yellow]")
    try:
        resume_generator = ResumeGenerator()
        cover_letter_generator = CoverLetterGenerator()
        
        # Generate sample documents
        resume_path = resume_generator.generate_standard_resume(format="pdf")
        cover_letter_path = cover_letter_generator.generate_cover_letter(
            "Software Engineer position at Test Company. Looking for someone with Python experience.",
            format="pdf"
        )
        
        attachments = [Path(resume_path), Path(cover_letter_path)]
        
    except Exception as e:
        console.print(f"[yellow]Could not generate test documents: {e}[/yellow]")
        console.print("[yellow]Continuing with email test without attachments...[/yellow]")
        attachments = []
    
    # Create email body
    body = f"""Dear Hiring Manager,

This is a test email from the Job Application Automation Bot.

The system is working correctly and can send emails with the following capabilities:
- Professional email formatting
- File attachments (resume, cover letter, etc.)
- CC and BCC support
- Error handling and logging

This test was sent on {typer.get_app_name()} at {Path.cwd()}

Best regards,
Job Application Bot
"""
    
    # Send test email
    console.print(f"\n[yellow]Sending test email to {test_email}...[/yellow]")
    
    try:
        email_sender = EmailSender()
        success = email_sender.send_email(
            to_email=test_email,
            subject=subject,
            body=body,
            attachments=attachments
        )
        
        if success:
            console.print(f"[green]✅ Test email sent successfully to {test_email}![/green]")
            if attachments:
                console.print(f"[green]   Attachments: {len(attachments)} files[/green]")
        else:
            console.print(f"[red]❌ Failed to send test email to {test_email}[/red]")
            
    except Exception as e:
        console.print(f"[red]Error sending test email: {e}[/red]")

@app.command()
def update_profile():
    """Update your profile configuration."""
    console.print("\n[bold blue]👤 Updating Profile...[/bold blue]")
    
    questions = [
        inquirer.List('section',
                     message="Which section would you like to update?",
                     choices=[
                         'Personal Information',
                         'Work Preferences',
                         'Secrets & API Keys',
                         'All Sections'
                     ])
    ]
    
    answers = inquirer.prompt(questions)
    data_folder = Path("data_folder")
    
    if answers['section'] == 'Personal Information' or answers['section'] == 'All Sections':
        setup_personal_profile(data_folder)
    
    if answers['section'] == 'Work Preferences' or answers['section'] == 'All Sections':
        setup_work_preferences(data_folder)
    
    if answers['section'] == 'Secrets & API Keys' or answers['section'] == 'All Sections':
        setup_secrets(data_folder)
    
    console.print("[green]✅ Profile updated successfully![/green]")

if __name__ == "__main__":
    app()
