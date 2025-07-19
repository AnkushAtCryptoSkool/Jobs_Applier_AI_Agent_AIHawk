import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime, timedelta
from job_search.base import JobFetcher
from job_search.models import Job

RELOCATE_ME_URL = 'https://relocate.me/search?keywords={keywords}&date=last-24-hours'

TARGET_COUNTRIES = [
    'Ireland', 'Netherlands', 'Finland', 'Denmark', 'Luxembourg',
    'Germany', 'Sweden', 'Norway', 'Switzerland', 'Belgium', 'France', 'Estonia', 'Lithuania', 'Latvia', 'Czech Republic'
]

CITY_KEYWORDS = [
    'dublin', 'amsterdam', 'helsinki', 'copenhagen', 'luxembourg', 'berlin', 'stockholm', 'oslo', 'zurich', 'brussels', 'paris', 'tallinn', 'vilnius', 'riga', 'prague'
]

def scrape_jobs(keywords: List[str]) -> List[Dict]:
    """
    Scrape Relocate.me for jobs matching the given keywords, posted in the last 24 hours, in target countries/cities.
    Returns a list of job dicts with title, company, location, link, and description.
    """
    jobs = []
    for keyword in keywords:
        url = RELOCATE_ME_URL.format(keywords=keyword.replace(' ', '+'))
        resp = requests.get(url)
        if resp.status_code != 200:
            continue
        soup = BeautifulSoup(resp.text, 'html.parser')
        for job_card in soup.select('div.job-listing'):
            title = job_card.select_one('h2').get_text(strip=True) if job_card.select_one('h2') else ''
            company = job_card.select_one('div.company').get_text(strip=True) if job_card.select_one('div.company') else ''
            location = job_card.select_one('div.location').get_text(strip=True) if job_card.select_one('div.location') else ''
            link = job_card.select_one('a.job-link')['href'] if job_card.select_one('a.job-link') else ''
            description = job_card.select_one('div.description').get_text(strip=True) if job_card.select_one('div.description') else ''
            # Filter by country/city
            if any(country.lower() in location.lower() for country in TARGET_COUNTRIES) or \
               any(city in location.lower() for city in CITY_KEYWORDS):
                jobs.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'link': link if link.startswith('http') else f'https://relocate.me{link}',
                    'description': description,
                    'source': 'Relocate.me',
                })
    return jobs

class RelocateMeJobFetcher(JobFetcher):
    """
    Job fetcher for Relocate.me job board.
    """
    def fetch_jobs(self, query: str = "", filters: Dict[str, Any] = None) -> List[Job]:
        # Use the existing scrape_jobs logic, but return List[Job]
        keywords = [query] if query else []
        # TODO: Integrate filters (location, date, etc.)
        raw_jobs = scrape_jobs(keywords)
        jobs = []
        for job in raw_jobs:
            try:
                jobs.append(Job(
                    title=job.get("title", ""),
                    company=job.get("company", ""),
                    description=job.get("description", ""),
                    location=job.get("location", ""),
                    posting_date=datetime.strptime(job.get("posting_date", "1970-01-01"), "%Y-%m-%d"),
                    apply_url=job.get("apply_url", "http://example.com"),
                    source="relocate_me",
                    email=job.get("email"),
                    extra=job
                ))
            except Exception as e:
                # Optionally log or print error
                continue
        return jobs 