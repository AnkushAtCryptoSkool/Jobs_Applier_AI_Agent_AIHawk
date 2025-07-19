# Job Application Automation System - User Guide

## Overview

This automated job application system helps you streamline your job search process by automatically generating tailored resumes and cover letters, scoring job matches, and managing applications. The system supports both automated email applications and manual application workflows.

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Getting Started](#getting-started)
3. [Web UI Interface](#web-ui-interface)
4. [CLI Interface](#cli-interface)
5. [Configuration](#configuration)
6. [Basic Usage](#basic-usage)
7. [Advanced Features](#advanced-features)
8. [CLI Commands](#cli-commands)
9. [Troubleshooting](#troubleshooting)

---

## Initial Setup

### 1. Prerequisites

- Python 3.9 or higher
- Git (for cloning the repository)
- A text editor for configuration files

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd Jobs_Applier_AI_Agent_AIHawk

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file in the project root with your API keys and email configuration:

```env
# OpenAI API Key (required for resume/cover letter generation)
OPENAI_API_KEY=your_openai_api_key_here

# Email Configuration (for automated applications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Optional: Other LLM providers
CLAUDE_API_KEY=your_claude_key
GEMINI_API_KEY=your_gemini_key
```

---

## Getting Started

The Job Application Automation system now offers **two interfaces** for your convenience:

### 🌐 Web UI (Recommended)
- **Modern, intuitive interface** with real-time updates
- **Easy configuration** through web forms
- **Visual progress tracking** for document generation
- **Application management** with drag-and-drop functionality
- **File preview and download** capabilities

### 💻 CLI (Command Line Interface)
- **Scriptable automation** for power users
- **Batch operations** for processing multiple jobs
- **Advanced configuration** options
- **Integration** with existing workflows

### Quick Start

1. **Run the launcher:**
   ```bash
   python launcher.py
   ```

2. **Choose your interface:**
   - Option 1: Web UI (opens in browser)
   - Option 2: CLI (terminal-based)
   - Option 3: Setup wizard (for first-time configuration)

3. **Alternative direct access:**
   ```bash
   # Start Web UI directly
   python launcher.py --web
   
   # Start CLI directly
   python launcher.py --cli
   
   # Run setup wizard
   python launcher.py --setup
   ```

---

## Web UI Interface

### Accessing the Web UI

1. **Start the Web UI:**
   ```bash
   python launcher.py --web
   ```
   Or select option 1 from the main menu.

2. **Browser Access:**
   - The system will automatically open your browser
   - Navigate to: `http://localhost:5000`
   - Works with Chrome, Firefox, Safari, and Edge

### Web UI Features

#### 🏠 Dashboard
- **Configuration status** overview
- **Quick actions** for common tasks
- **Recent activity** tracking
- **System health** indicators

#### ⚙️ Setup & Configuration
- **Interactive forms** for all settings
- **Real-time validation** of inputs
- **Test connections** (email, API keys)
- **Import/export** configuration

#### 📄 Document Generation
- **Resume generation** (standard and job-tailored)
- **Cover letter creation** with job-specific customization
- **Multiple output formats** (PDF, HTML, TXT)
- **Real-time progress** updates
- **Download and preview** generated documents

#### 📋 Manual Applications
- **Job application tracking** with status management
- **Bulk operations** for multiple applications
- **Application details** with full job descriptions
- **Deadline tracking** and priority management
- **Document generation** for specific applications

### Web UI Workflow

1. **First-time setup:**
   - Navigate to Setup page
   - Fill in personal information
   - Configure API keys
   - Set work preferences
   - Test email configuration

2. **Generate documents:**
   - Go to Generate Documents page
   - Choose document type (resume/cover letter)
   - Paste job description (for tailored documents)
   - Select output format
   - Monitor real-time progress
   - Download completed documents

3. **Manage applications:**
   - Visit Manual Applications page
   - Add new job applications
   - Track application status
   - Generate documents for specific jobs
   - Use bulk operations for efficiency

---

## CLI Interface

### Accessing the CLI

1. **Start the CLI:**
   ```bash
   python launcher.py --cli
   ```
   Or select option 2 from the main menu.

2. **Direct CLI commands:**
   ```bash
   # Run setup wizard
   python -m cli.main setup
   
   # Generate resume
   python -m cli.main generate-resume
   
   # Check configuration
   python -m cli.main check-config
   ```

### CLI Benefits

- **Automation scripts** for repetitive tasks
- **Batch processing** of multiple jobs
- **Integration** with CI/CD pipelines
- **Advanced configuration** options
- **Scriptable workflows** for power users

---

## Configuration

### 1. Setup Wizard (Recommended)

Run the interactive setup wizard to configure all settings:

```bash
python3 cli/main.py setup
```

This wizard will guide you through:
- Personal information
- Work preferences
- Resume details
- Email configuration
- Job search criteria

### 2. Manual Configuration

If you prefer manual setup, configure these files in the `data_folder/` directory:

#### `secrets.yaml`
```yaml
llm_api_key: "your_openai_api_key_here"
```

#### `plain_text_resume.yaml`
```yaml
personal_information:
  name: "John"
  surname: "Doe"
  email: "john.doe@email.com"
  phone_prefix: "+1"
  phone: "555-123-4567"
  linkedin: "https://linkedin.com/in/johndoe"
  github: "https://github.com/johndoe"

experience_details:
  - position: "Senior Software Engineer"
    company: "Tech Corp"
    employment_period: "2020-2024"
    location: "San Francisco, CA"
    industry: "Technology"
    key_responsibilities:
      - responsibility_1: "Developed scalable web applications"
      - responsibility_2: "Led team of 5 developers"
    skills_acquired:
      - "Python"
      - "Django"
      - "React"
      - "AWS"

education_details:
  - education_level: "Bachelor's Degree"
    field_of_study: "Computer Science"
    institution: "University of Technology"
    start_date: "2016"
    year_of_completion: "2020"
    final_evaluation_grade: "3.8 GPA"

languages:
  - language: "English"
    proficiency: "Native"
  - language: "Spanish"
    proficiency: "Conversational"

interests:
  - "Machine Learning"
  - "Open Source"
  - "Photography"
```

#### `work_preferences.yaml`
```yaml
remote_work: true
in_person_work: true
open_to_relocation: true
willing_to_complete_assessments: true
willing_to_undergo_drug_tests: false
willing_to_undergo_background_checks: true
requires_visa_sponsorship: false

preferred_locations:
  - "San Francisco, CA"
  - "New York, NY"
  - "Remote"

salary_expectations:
  salary_range_usd: "80000-120000"
```

---

## Basic Usage

### 1. Check Configuration

Verify your setup is correct:

```bash
python3 cli/main.py check-config
```

### 2. Generate Resume

Create a standard resume:

```bash
# Generate PDF resume
python3 cli/main.py generate-resume --format pdf

# Generate HTML resume
python3 cli/main.py generate-resume --format html

# Generate both formats
python3 cli/main.py generate-resume --format both
```

### 3. Generate Cover Letter

Create a cover letter for a specific job:

```bash
# Interactive mode (will prompt for job description)
python3 cli/main.py generate-cover-letter

# With job description file
python3 cli/main.py generate-cover-letter --job-file job_description.txt

# Specify output format
python3 cli/main.py generate-cover-letter --format pdf
```

### 4. Generate Tailored Resume

Create a resume tailored to a specific job:

```bash
# Interactive mode
python3 cli/main.py generate-tailored-resume

# With job description file
python3 cli/main.py generate-tailored-resume --job-file job_description.txt
```

---

## Advanced Features

### 1. Job Search and Scoring

The system can automatically score jobs based on your skills and preferences:

```python
# Example: Score a job manually
from src.job_scoring import score_job
from src.skills_extractor import extract_skills_from_text

# Extract skills from your resume
with open('data_folder/plain_text_resume.yaml', 'r') as f:
    resume_text = f.read()
    
skills = extract_skills_from_text(resume_text)

# Score a job
job = {
    'title': 'Senior Python Developer',
    'company': 'Tech Corp',
    'description': 'Looking for Python developer with Django experience...',
    'location': 'Dublin, Ireland'
}

score, explanation = score_job(job, skills)
print(f"Job Score: {score}% - {explanation}")
```

### 2. Manual Application Management

For jobs requiring manual application:

```bash
# Review pending manual applications
python3 cli/main.py review-manual
```

This will show you jobs that need manual attention and let you:
- View job details
- Mark jobs as applied
- Skip jobs
- Generate documents for specific jobs

### 3. Email Testing

Test your email configuration:

```bash
python3 cli/main.py test-email
```

### 4. Batch Operations

Generate documents for multiple jobs:

```python
from documents.cover_letter_generator import CoverLetterGenerator

generator = CoverLetterGenerator()

jobs = [
    {'description': 'Job 1 description...', 'company': 'Company A'},
    {'description': 'Job 2 description...', 'company': 'Company B'}
]

# Generate cover letters for all jobs
paths = generator.generate_multiple_cover_letters(jobs, format='pdf')
```

---

## CLI Commands

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `setup` | Interactive setup wizard | `python3 cli/main.py setup` |
| `check-config` | Validate configuration | `python3 cli/main.py check-config` |
| `generate-resume` | Generate standard resume | `python3 cli/main.py generate-resume --format pdf` |
| `generate-cover-letter` | Generate cover letter | `python3 cli/main.py generate-cover-letter` |
| `generate-tailored-resume` | Generate job-specific resume | `python3 cli/main.py generate-tailored-resume` |
| `review-manual` | Review manual applications | `python3 cli/main.py review-manual` |
| `test-email` | Test email configuration | `python3 cli/main.py test-email` |

### Command Options

| Option | Description | Commands |
|--------|-------------|----------|
| `--format` | Output format (pdf, html, both) | `generate-resume`, `generate-cover-letter` |
| `--job-file` | Job description file | `generate-cover-letter`, `generate-tailored-resume` |
| `--output` | Custom output path | All generation commands |

---

## File Structure

```
Jobs_Applier_AI_Agent_AIHawk/
├── data_folder/                 # Your configuration and data
│   ├── secrets.yaml            # API keys
│   ├── plain_text_resume.yaml  # Your resume data
│   ├── work_preferences.yaml   # Job preferences
│   └── output/                 # Generated documents
├── cli/                        # Command-line interface
├── documents/                  # Document generation
├── applications/               # Application management
├── src/                        # Core functionality
└── USER_GUIDE.md              # This guide
```

---

## Troubleshooting

### Common Issues

#### 1. "OpenAI API Key not found"
- Ensure `OPENAI_API_KEY` is set in your `.env` file
- Check that `secrets.yaml` contains the correct API key
- Verify the API key is valid and has credits

#### 2. "Resume generation failed"
- Run `python3 cli/main.py check-config` to validate setup
- Ensure all required fields are filled in `plain_text_resume.yaml`
- Check that the output directory exists and is writable

#### 3. "Email sending failed"
- Verify SMTP settings in `.env` file
- For Gmail, use an App Password instead of your regular password
- Check firewall and network settings

#### 4. "Skills extraction not working"
- The system uses keyword matching - ensure your resume contains relevant technical terms
- Skills are extracted from both explicit "Skills" sections and job descriptions
- Add more specific technical terms to improve matching

#### 5. "Cover letter generation takes too long"
- This is normal - the system uses AI to generate personalized content
- Ensure stable internet connection
- Check OpenAI API status if requests are failing

### Getting Help

1. **Check Configuration**: Always run `check-config` first
2. **Review Logs**: Check the `log/` directory for detailed error messages
3. **Validate Files**: Ensure YAML files are properly formatted
4. **Test Components**: Use individual commands to isolate issues

### Performance Tips

1. **Use PDF Format**: PDF generation is optimized and faster than HTML
2. **Batch Operations**: Generate multiple documents at once when possible
3. **Cache Results**: The system caches some AI responses to improve speed
4. **Monitor API Usage**: Keep track of your OpenAI API usage and costs

---

## Example Workflow

Here's a typical workflow for using the system:

### 1. Initial Setup
```bash
# First time setup
python3 cli/main.py setup

# Verify configuration
python3 cli/main.py check-config
```

### 2. Generate Base Documents
```bash
# Create your standard resume
python3 cli/main.py generate-resume --format pdf

# Test email configuration
python3 cli/main.py test-email
```

### 3. Apply to Jobs
```bash
# For each job, generate tailored documents
python3 cli/main.py generate-tailored-resume --job-file job1.txt
python3 cli/main.py generate-cover-letter --job-file job1.txt

# Review any manual applications
python3 cli/main.py review-manual
```

### 4. Track Applications
- Generated documents are saved in `data_folder/output/`
- Manual applications are tracked in CSV format
- Use the review system to manage your application pipeline

---

## Tips for Best Results

1. **Complete Resume**: Fill out all sections in `plain_text_resume.yaml` thoroughly
2. **Specific Skills**: Include specific technical skills and tools you've used
3. **Quantify Achievements**: Use numbers and metrics in your experience descriptions
4. **Tailor Job Descriptions**: Provide detailed job descriptions for better matching
5. **Regular Updates**: Keep your resume and preferences updated as you gain experience

---

## Support

For issues, feature requests, or contributions:
1. Check the troubleshooting section above
2. Review the configuration files
3. Check the logs in the `log/` directory
4. Ensure all dependencies are installed correctly

The system is designed to be flexible and extensible - you can modify templates, add new job sources, or customize the scoring algorithms to fit your specific needs. 