from datetime import timedelta

from django.utils import timezone

from jobs.clients.exceptions import JobFetcherClientError
from jobs.models import Company, JobListing
from jobs.services.exceptions import JobFetcherServiceError


class JobFetcherService:
    """Service for fetching jobs from companies and syncing with database"""
    
    DEFAULT_EXCLUDE_SENIORITY = [
        "Director",
        "Lead",
        "Manager",
        "Principal",
        "Senior",
        "Sr.",
        "Staff",
    ]
    STALE_JOB_CLEANUP_DAYS = 30
    
    def fetch_and_sync_jobs(
        self,
        company_name: str = None,
        keywords: str = None,
        location: str = None,
        exclude_seniority: list = None,
        max_results: int = None,
    ):
        """
        Fetch jobs from companies and sync with database.
        
        Args:
            company_name: Specific company to fetch from (None = all active)
            keywords: Search keywords
            location: Location filter
            exclude_seniority: Terms to exclude from titles (None = use defaults)
            max_results: Max results per company
            
        Returns:
            Dict with stats: {company_name: {new: X, updated: Y, total: Z}}
        """
        if exclude_seniority is None:
            exclude_seniority = self.DEFAULT_EXCLUDE_SENIORITY
        
        companies = self._get_companies(company_name)
        stats = {}
        
        for company in companies:
            try:
                jobs = self._fetch_jobs_for_company(
                    company, keywords, location, exclude_seniority, max_results
                )
                
                sync_stats = self._sync_jobs_to_database(company, jobs)
                stats[company.name] = sync_stats
                
            except JobFetcherClientError as e:
                print(f"Error fetching jobs from {company.name}: {e}")
                stats[company.name] = {"error": str(e)}

            except Exception as e:
                raise JobFetcherServiceError(
                    f"Unexpected error while fetching jobs for {company.name}"
                ) from e
        
        self._cleanup_stale_jobs()
        
        return stats
    
    def _get_companies(self, company_name: str = None):
        """Get active companies to fetch from."""
        companies = Company.objects.filter(active=True)
        if company_name:
            companies = companies.filter(name=company_name)
        return companies
    
    def _fetch_jobs_for_company(self, company, keywords, location, exclude_seniority, max_results):
        """Fetch jobs from a single company using appropriate client."""
        client = company.get_job_fetcher()
        return client.fetch_jobs(
            keywords=keywords,
            location=location,
            exclude_seniority=exclude_seniority,
            max_results=max_results,
        )
    
    
    def _sync_jobs_to_database(self, company, jobs):
        """
        Sync fetched jobs to database and return stats.
        
        Creates/updates job records, marks missing jobs as stale.
        """
        fetched_ids = set()
        new_count = 0
        updated_count = 0
        
        for job_data in jobs:
            fetched_ids.add(job_data["external_id"])
            
            _, created = JobListing.objects.update_or_create(
                company=company,
                external_id=job_data["external_id"],
                defaults={
                    "title": job_data["title"],
                    "location": job_data["location"],
                    "url": job_data["url"],
                    "posted_on": job_data["posted_on"],
                    "last_fetched": timezone.now(),
                    "is_stale": False,
                }
            )
            
            if created:
                new_count += 1
            else:
                updated_count += 1
        
        JobListing.objects.filter(
            company=company,
            is_stale=False
        ).exclude(
            external_id__in=fetched_ids
        ).update(is_stale=True)
        
        return {
            "new": new_count,
            "updated": updated_count,
            "total": len(jobs)
        }
    
    def _cleanup_stale_jobs(self):
        """Delete stale jobs older than threshold."""
        cutoff = timezone.now() - timedelta(days=self.STALE_JOB_CLEANUP_DAYS)
        JobListing.objects.filter(
            is_stale=True,
            last_fetched__lt=cutoff
        ).delete()
