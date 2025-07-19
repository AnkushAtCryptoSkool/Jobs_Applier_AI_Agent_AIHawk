import pandas as pd
from typing import List, Dict

def write_jobs_to_excel(jobs: List[Dict], excel_path: str):
    """
    Write a list of job dicts (with score, filenames, etc.) to an Excel file.
    """
    df = pd.DataFrame(jobs)
    # Reorder columns if present
    columns = [
        'title', 'company', 'location', 'link', 'score', 'score_explanation',
        'resume_filename', 'cover_letter_filename', 'source'
    ]
    df = df[[col for col in columns if col in df.columns]]
    df.to_excel(excel_path, index=False) 