from abc import ABC, abstractmethod
from typing import List, Dict, Any

class JobFetcher(ABC):
    """
    Abstract base class for job fetchers.
    All job board/source fetchers should inherit from this and implement fetch_jobs.
    """
    @abstractmethod
    def fetch_jobs(self, query: str = "", filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Fetch jobs from the source.
        Args:
            query: Search query string (e.g., job title, keywords)
            filters: Dictionary of filters (location, date, etc.)
        Returns:
            List of standardized job dicts.
        """
        pass
