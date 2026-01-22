import logging
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass

from jobs.clients.exceptions import WorkdayClientError


HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


@dataclass
class WorkdayCompanyConfig:
    """Configuration for a Workday company"""
    name: str
    base_url: str
    tenant: str
    site: str
    location_filters: Dict[str, str]
    
    @classmethod
    def from_django_model(cls, workday_config):
        """Create config from Django WorkdayConfig model instance"""
        return cls(
            name=workday_config.company.name,
            base_url=workday_config.base_url,
            tenant=workday_config.tenant,
            site=workday_config.site,
            location_filters=workday_config.location_filters or {}
        )


class WorkdayClient:
    """
    Client for fetching jobs from Workday career sites.
    
    Handles pagination, location filtering, and seniority exclusion.
    """
    
    PAGE_SIZE = 20
    logger = logging.getLogger(__name__)
    
    def __init__(self, config: WorkdayCompanyConfig):
        self.config = config
        self.jobs_url = f"{config.base_url.rstrip('/')}/wday/cxs/{config.tenant}/{config.site}/jobs"
    
    def fetch_jobs(
        self,
        keywords: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> List[Dict]:
        """
        Fetch jobs from Workday API with filters.
        
        Args:
            keywords: Search keywords (server-side filter)
            max_results: Maximum number of jobs to return
            verbose: Print progress messages
            
        Returns:
            List of job dicts: {company_name, title, location, url_path, posted_on, external_id}
        """
        location_ids = self._get_location_ids()
        
        offset = 0
        total_available = None
        all_jobs = []
        
        while True:
            jobs, total = self._fetch_page(keywords, location_ids, offset)
            
            if offset == 0:
                total_available = total
            
            if not jobs:
                break
            
            for job in jobs:
                all_jobs.append(self._normalize_job(job))
            
            if max_results and len(all_jobs) >= max_results:
                all_jobs = all_jobs[:max_results]
                break
            
            offset += self.PAGE_SIZE
            if total_available and offset >= total_available:
                break
            
        return all_jobs

    def _get_location_ids(self):
        """Get all Workday location IDs from config."""
        if not self.config.location_filters:
            return []
        
        return list(self.config.location_filters.values())

    def _fetch_page(self, keywords, location_ids, offset):
        """Fetch a single page of jobs from Workday API."""
        payload = {
            "appliedFacets": {},
            "limit": self.PAGE_SIZE,
            "offset": offset,
            "searchText": keywords or "",
        }
        
        if location_ids:
            payload["appliedFacets"]["locations"] = location_ids
        
        try:
            response = requests.post(
                self.jobs_url,
                headers=HEADERS,
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()

            return data.get("jobPostings", []), data.get("total", 0)
        
        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"Workday API request failed for {self.config.name}: {e}",
                exc_info=True
            )
            raise WorkdayClientError(
                f"Failed to fetch jobs from Workday for {self.config.name}: {type(e).__name__}: {str(e)}"
            ) from e

    def _normalize_job(self, job):
        """Normalize Workday job data to standard format."""
        return {
            "company_name": self.config.name,
            "title": job.get("title", ""),
            "location": job.get("locationsText", ""),
            "url_path": job.get("externalPath", ""),
            "posted_on": job.get("postedOn", ""),
            "external_id": job.get("bulletFields", [None])[0] or job.get("externalPath", "").split("/")[-1],
        }
