import os
import json
import csv
from typing import Any, List
from pathlib import Path
from dataclasses import dataclass
from applications.logger import get_logger

logger = get_logger()


@dataclass
class ManualJob:
    """Represents a job that requires manual application."""
    title: str
    company: str
    location: str
    link: str
    manual_reason: str
    status: str = "pending"  # pending, applied, skipped
    job_info_path: str = ""
    
    
class ManualApplicationHandler:
    """
    Handles saving job applications that require manual action.
    """
    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            base_dir = Path("data_folder/output")
        
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.manual_apply_csv = self.base_dir / "manual_apply.csv"
        self.manual_jobs_dir = self.base_dir / "manual_jobs"
        self.manual_jobs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize CSV file with headers if it doesn't exist
        if not self.manual_apply_csv.exists():
            self._initialize_csv()

    def _initialize_csv(self):
        """Initialize the CSV file with headers."""
        with open(self.manual_apply_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['company', 'title', 'location', 'apply_url', 'manual_reason', 'status', 'job_dir'])

    def save_manual_application(self, job_info: dict, generated_docs: dict, manual_reason: str = "Manual application required") -> None:
        """
        Save job info and generated docs for manual application.
        
        Args:
            job_info: Dictionary containing job information
            generated_docs: Dictionary of generated documents {filename: content}
            manual_reason: Reason why manual application is required
        """
        company = job_info.get('company', 'Unknown')
        title = job_info.get('title', job_info.get('role', 'Unknown'))
        
        # Create safe directory name
        safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        dir_name = f"{safe_company}-{safe_title}".replace(' ', '_')
        
        app_dir = self.manual_jobs_dir / dir_name
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Save job info
        job_info_path = app_dir / "job_info.json"
        with open(job_info_path, "w", encoding='utf-8') as f:
            json.dump(job_info, f, indent=2, ensure_ascii=False)
        
        # Save generated docs
        for fname, content in generated_docs.items():
            file_path = app_dir / fname
            if isinstance(content, bytes):
                with open(file_path, "wb") as f:
                    f.write(content)
            else:
                with open(file_path, "w", encoding='utf-8') as f:
                    f.write(str(content))
        
        # Log to manual_apply.csv
        with open(self.manual_apply_csv, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                company,
                title,
                job_info.get('location', ''),
                job_info.get('apply_url', job_info.get('link', '')),
                manual_reason,
                'pending',
                str(app_dir)
            ])
        
        logger.info(f"Manual application saved for {company} - {title}")

    def get_pending_manual_jobs(self) -> List[ManualJob]:
        """
        Get all pending manual job applications.
        
        Returns:
            List of ManualJob objects that are pending
        """
        manual_jobs = []
        
        if not self.manual_apply_csv.exists():
            return manual_jobs
        
        try:
            with open(self.manual_apply_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('status', 'pending') == 'pending':
                        manual_job = ManualJob(
                            title=row.get('title', ''),
                            company=row.get('company', ''),
                            location=row.get('location', ''),
                            link=row.get('apply_url', ''),
                            manual_reason=row.get('manual_reason', 'Manual application required'),
                            status=row.get('status', 'pending'),
                            job_info_path=row.get('job_dir', '')
                        )
                        manual_jobs.append(manual_job)
        except Exception as e:
            logger.error(f"Error reading manual applications: {e}")
        
        return manual_jobs

    def mark_as_applied(self, job: ManualJob) -> None:
        """
        Mark a manual job as applied.
        
        Args:
            job: ManualJob object to mark as applied
        """
        self._update_job_status(job, 'applied')
        logger.info(f"Marked {job.company} - {job.title} as applied")

    def mark_as_skipped(self, job: ManualJob) -> None:
        """
        Mark a manual job as skipped.
        
        Args:
            job: ManualJob object to mark as skipped
        """
        self._update_job_status(job, 'skipped')
        logger.info(f"Marked {job.company} - {job.title} as skipped")

    def _update_job_status(self, job: ManualJob, new_status: str) -> None:
        """
        Update the status of a job in the CSV file.
        
        Args:
            job: ManualJob object to update
            new_status: New status to set
        """
        if not self.manual_apply_csv.exists():
            return
        
        # Read all rows
        rows = []
        try:
            with open(self.manual_apply_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    # Update matching row
                    if (row.get('company') == job.company and 
                        row.get('title') == job.title and 
                        row.get('apply_url') == job.link):
                        row['status'] = new_status
                    rows.append(row)
        except Exception as e:
            logger.error(f"Error reading CSV for update: {e}")
            return
        
        # Write back all rows
        try:
            with open(self.manual_apply_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        except Exception as e:
            logger.error(f"Error writing updated CSV: {e}")

    def get_job_details(self, job: ManualJob) -> dict:
        """
        Get detailed job information from the saved job info file.
        
        Args:
            job: ManualJob object
            
        Returns:
            Dictionary containing detailed job information
        """
        if not job.job_info_path:
            return {}
        
        job_info_file = Path(job.job_info_path) / "job_info.json"
        if not job_info_file.exists():
            return {}
        
        try:
            with open(job_info_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading job details: {e}")
            return {}

    def get_generated_documents(self, job: ManualJob) -> List[str]:
        """
        Get list of generated documents for a manual job.
        
        Args:
            job: ManualJob object
            
        Returns:
            List of file paths for generated documents
        """
        if not job.job_info_path:
            return []
        
        job_dir = Path(job.job_info_path)
        if not job_dir.exists():
            return []
        
        documents = []
        for file_path in job_dir.iterdir():
            if file_path.is_file() and file_path.name != "job_info.json":
                documents.append(str(file_path))
        
        return documents

    def get_statistics(self) -> dict:
        """
        Get statistics about manual job applications.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total': 0,
            'pending': 0,
            'applied': 0,
            'skipped': 0
        }
        
        if not self.manual_apply_csv.exists():
            return stats
        
        try:
            with open(self.manual_apply_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stats['total'] += 1
                    status = row.get('status', 'pending')
                    if status in stats:
                        stats[status] += 1
        except Exception as e:
            logger.error(f"Error reading statistics: {e}")
        
        return stats
