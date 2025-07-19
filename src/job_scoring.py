from typing import Dict, Set, Tuple

# Example weights for scoring
WEIGHTS = {
    'skill_match': 0.6,
    'location_match': 0.2,
    'visa_or_remote': 0.2,
}

EUROPE_COUNTRIES = [
    'Ireland', 'Netherlands', 'Finland', 'Denmark', 'Luxembourg',
    'Germany', 'Sweden', 'Norway', 'Switzerland', 'Belgium', 'France', 'Estonia', 'Lithuania', 'Latvia', 'Czech Republic'
]

REMOTE_KEYWORDS = ['remote', 'work from home']
VISA_KEYWORDS = ['visa', 'sponsorship', 'relocation']


def score_job(job: Dict, user_skills: Set[str]) -> Tuple[float, str]:
    """
    Score a job based on skill match, location, and visa/remote/relocation.
    Returns (score, explanation).
    """
    # Skill match
    job_text = (job.get('title', '') + ' ' + job.get('description', '')).lower()
    skill_matches = [skill for skill in user_skills if skill in job_text]
    skill_score = len(skill_matches) / max(1, len(user_skills))
    
    # Location match
    location = job.get('location', '').lower()
    location_score = 1.0 if any(country.lower() in location for country in EUROPE_COUNTRIES) else 0.0
    
    # Visa/remote/relocation
    visa_score = 0.0
    if any(k in job_text for k in VISA_KEYWORDS) or any(k in location for k in REMOTE_KEYWORDS):
        visa_score = 1.0
    
    # Weighted sum
    score = (
        WEIGHTS['skill_match'] * skill_score +
        WEIGHTS['location_match'] * location_score +
        WEIGHTS['visa_or_remote'] * visa_score
    )
    explanation = (
        f"Skill match: {len(skill_matches)}/{len(user_skills)}; "
        f"Location: {'Europe' if location_score else 'Other'}; "
        f"Visa/Remote: {'Yes' if visa_score else 'No'}"
    )
    return round(score * 100, 2), explanation 