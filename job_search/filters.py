from typing import List, Optional
from datetime import datetime, timedelta
from job_search.models import Job


def filter_by_keywords(jobs: List[Job], keywords: List[str]) -> List[Job]:
    """
    Filter jobs by presence of any keyword in title or description.
    """
    if not keywords:
        return jobs
    keywords_lower = [k.lower() for k in keywords]
    return [job for job in jobs if any(k in job.title.lower() or k in job.description.lower() for k in keywords_lower)]


def filter_by_location(jobs: List[Job], locations: List[str]) -> List[Job]:
    """
    Filter jobs by location (case-insensitive substring match).
    """
    if not locations:
        return jobs
    locations_lower = [l.lower() for l in locations]
    return [job for job in jobs if any(loc in job.location.lower() for loc in locations_lower)]


def filter_by_date(jobs: List[Job], days: int = 1) -> List[Job]:
    """
    Filter jobs by posting date (within the last X days).
    """
    cutoff = datetime.now() - timedelta(days=days)
    return [job for job in jobs if job.posting_date >= cutoff]


def filter_jobs(
    jobs: List[Job],
    keywords: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    days: Optional[int] = None
) -> List[Job]:
    """
    General job filter applying all filters in sequence.
    """
    filtered = jobs
    if keywords:
        filtered = filter_by_keywords(filtered, keywords)
    if locations:
        filtered = filter_by_location(filtered, locations)
    if days is not None:
        filtered = filter_by_date(filtered, days)
    return filtered
