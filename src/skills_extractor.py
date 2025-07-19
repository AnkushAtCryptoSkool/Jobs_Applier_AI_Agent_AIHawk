import re
from typing import List, Set

# Example skill keywords for demonstration; can be expanded or loaded from a config
SKILL_KEYWORDS = [
    'java', 'spring', 'spring boot', 'backend', 'microservices', 'rest', 'api', 'sql', 'docker', 'kubernetes',
    'aws', 'azure', 'git', 'linux', 'agile', 'scrum', 'maven', 'gradle', 'hibernate', 'jpa', 'rabbitmq', 'redis',
    'mongodb', 'postgresql', 'mysql', 'jenkins', 'ci/cd', 'unit testing', 'integration testing', 'oop', 'design patterns'
]

def extract_skills_from_text(resume_text: str, skill_keywords: List[str] = SKILL_KEYWORDS) -> Set[str]:
    """
    Extracts a set of skills from the resume text based on a list of keywords.
    """
    found_skills = set()
    resume_text_lower = resume_text.lower()
    for skill in skill_keywords:
        # Use word boundaries for single-word skills, substring for multi-word
        if ' ' in skill:
            if skill in resume_text_lower:
                found_skills.add(skill)
        else:
            if re.search(r'\b' + re.escape(skill) + r'\b', resume_text_lower):
                found_skills.add(skill)
    return found_skills 