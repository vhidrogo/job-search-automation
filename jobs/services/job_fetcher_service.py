from datetime import timedelta

from django.utils import timezone

from jobs.clients.exceptions import JobFetcherClientError
from jobs.models import Company, JobListing, SearchRole, SearchRoleConfig
from jobs.services.exceptions import JobFetcherServiceError
from tracker.models import Job


class JobFetcherService:
    """Service for fetching jobs from companies and syncing with database"""

    STALE_JOB_CLEANUP_DAYS = 30
    
    def fetch_and_sync_jobs(
        self,
        search_role,
        company_name: str = None,
        location: str = None,
        max_results: int = None,
    ):
        """
        Fetch jobs from companies and sync with database.
        
        Args:
            search_role: The role to use as search keywords
            company_name: Specific company to fetch from (None = all active)
            location: Location filter
            max_results: Max results per company
            
        Returns:
            Dict with stats: {company_name: {new: X, updated: Y, total: Z}}
        """
        role_label = SearchRole(search_role).label
        exclude_terms = self._get_exclude_terms(search_role)
        
        companies = self._get_companies(company_name)
        stats = {}
        
        for company in companies:
            key = f"{company.name} - {role_label}"

            try:
                jobs = self._fetch_jobs_for_company(
                    company,
                    role_label,
                    location,
                    max_results
                )
                
                filtered_jobs = self._filter_excluded_jobs(jobs, exclude_terms)
                
                sync_stats = self._sync_jobs_to_database(
                    company, filtered_jobs, search_role
                )
                stats[key] = sync_stats
                
            except JobFetcherClientError as e:
                print(f"Error fetching jobs from {company.name}: {e}")
                stats[key] = {"error": str(e)}

            except Exception as e:
                raise JobFetcherServiceError(
                    f"Unexpected error while fetching jobs for {company.name}"
                ) from e
        
        self._cleanup_stale_jobs()

        return stats
    
    def _get_exclude_terms(self, role):
        try:
            config = SearchRoleConfig.objects.get(role=role)

            return config.exclude_terms
        
        except SearchRoleConfig.DoesNotExist:
            return []
        
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
    
    
    def _sync_jobs_to_database(self, company, jobs, search_role):
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
                    "search_role": search_role,
                    "last_fetched": timezone.now(),
                    "is_stale": False,
                }
            )

            if job_data["external_id"] in applied_external_ids:
                job_listing.status = JobListing.Status.APPLIED
                job_listing.save(update_fields=["status"])
            
            if created:
                new_count += 1
            else:
                updated_count += 1
        
        JobListing.objects.filter(
            company=company,
            search_role=search_role,
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
