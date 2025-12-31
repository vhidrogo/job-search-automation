from datetime import timedelta

from django.utils import timezone

from jobs.clients.exceptions import JobFetcherClientError
from jobs.models import Company, JobListing, SearchConfig
from jobs.services.exceptions import JobFetcherServiceError
from tracker.models import Job


class JobFetcherService:
    """Service for fetching jobs from companies and syncing with database"""

    STALE_JOB_CLEANUP_DAYS = 30
    
    def fetch_and_sync_jobs(
        self,
        company_name: str = None,
        keywords: str = None,
        location: str = None,
        max_results: int = None,
    ):
        """
        Fetch jobs from companies and sync with database.
        
        Loops through all active search configurations (or filters by keywords)
        and all active companies (or filters by company_name). For each 
        company-search combination, fetches jobs, applies exclusion filtering,
        and syncs to database.
        
        Args:
            company_name: Specific company to fetch from (None = all active companies)
            keywords: Filter search configurations by search_term (None = all active configs)
            location: Location filter passed to platform client
            max_results: Max results per company per search
            
        Returns:
            Dict with stats keyed by "{company_name} - {search_term}":
            {
                "Company - Search Term": {
                    "new": X,
                    "updated": Y,
                    "total": Z
                },
                ...
            }
            
        Example:
            service.fetch_and_sync_jobs(keywords="engineer", location="Seattle")
            # Returns stats for all companies, all search configs containing "engineer"
        """
        companies = self._get_companies(company_name)
        search_configs = self._get_search_configs(keywords)
        
        all_stats = {}
        
        for company in companies:
            for config in search_configs:
                key = f"{company.name} - {config.search_term}"
                
                try:
                    jobs = self._fetch_jobs_for_company(
                        company,
                        config.search_term,
                        location,
                        max_results
                    )
                    filtered_jobs = self._filter_excluded_jobs(jobs, config.exclude_terms)
                    all_stats[key] = self._sync_jobs_to_database(company, filtered_jobs, config.search_term)
                    
                except JobFetcherClientError as e:
                    print(f"Error fetching jobs from {company.name}: {e}")
                    all_stats[key] = {"error": str(e)}

                except Exception as e:
                    raise JobFetcherServiceError(
                        f"Unexpected error while fetching jobs for {company.name}"
                    ) from e
        
        self._cleanup_stale_jobs()

        return all_stats
    
    def _get_search_configs(self, keywords):
        configs = SearchConfig.objects.filter(active=True)
        if keywords:
            configs = configs.filter(search_term__icontains=keywords)

        return configs
        
    def _filter_excluded_jobs(self, jobs, exclude_terms):
        if not exclude_terms:
            return jobs
        
        filtered = []
        for job in jobs:
            if not any(term.lower() in job["title"].lower() for term in exclude_terms):
                filtered.append(job)

        return filtered
    
    def _get_companies(self, company_name: str = None):
        """Get active companies to fetch from."""
        companies = Company.objects.filter(active=True)
        if company_name:
            companies = companies.filter(name=company_name)
        return companies
    
    def _fetch_jobs_for_company(self, company, search_term, location, max_results):
        """Fetch jobs from a single company using appropriate client."""
        client = company.get_job_fetcher()

        return client.fetch_jobs(
            keywords=search_term,
            location=location,
            max_results=max_results,
        )
    
    
    def _sync_jobs_to_database(self, company, jobs, search_term):
        """
        Sync fetched jobs to database and return stats.
    
        Creates/updates job records, marks missing jobs as stale,
        sets status=APPLIED for jobs user has already applied to.
        """
        applied_external_ids = set(
            Job.objects.filter(company=company.name)
            .values_list("external_job_id", flat=True)
        )
        
        fetched_ids = set()
        new_count = 0
        updated_count = 0
        applied_count = 0
        
        for job_data in jobs:
            fetched_ids.add(job_data["external_id"])
            
            job_listing, created = JobListing.objects.update_or_create(
                company=company,
                external_id=job_data["external_id"],
                defaults={
                    "title": job_data["title"],
                    "location": job_data["location"],
                    "url_path": job_data["url_path"],
                    "posted_on": job_data["posted_on"],
                    "search_term": search_term,
                    "last_fetched": timezone.now(),
                    "is_stale": False,
                }
            )

            if job_data["external_id"] in applied_external_ids:
                job_listing.status = JobListing.Status.APPLIED
                job_listing.save(update_fields=["status"])
                applied_count += 1
            
            if created:
                new_count += 1
            else:
                updated_count += 1
        
        JobListing.objects.filter(
            company=company,
            search_term=search_term,
            is_stale=False,
        ).exclude(
            external_id__in=fetched_ids
        ).update(is_stale=True)
        
        return {
            "new": new_count,
            "updated": updated_count,
            "applied": applied_count,
            "total": len(jobs)
        }
    
    def _cleanup_stale_jobs(self):
        """Delete stale jobs older than threshold."""
        cutoff = timezone.now() - timedelta(days=self.STALE_JOB_CLEANUP_DAYS)
        JobListing.objects.filter(
            is_stale=True,
            last_fetched__lt=cutoff
        ).delete()
