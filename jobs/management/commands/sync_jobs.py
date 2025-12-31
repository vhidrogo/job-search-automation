from django.core.management.base import BaseCommand

from jobs.services import JobFetcherService


class Command(BaseCommand):
    help = "Fetch and sync jobs from configured companies"
    
    def add_arguments(self, parser):
        parser.add_argument("--company", type=str, help="Specific company name")
        parser.add_argument("--keywords", type=str, help="Filter search terms (e.g., 'engineer')")
        parser.add_argument("--location", type=str, help="Location filter (e.g., Seattle)")
        parser.add_argument("--max", type=int, help="Max results per company per search")
    
    def handle(self, *args, **options):
        keywords = options.get("keywords")
        sync_for = f"search terms containing '{keywords}'" if keywords else "all active search configurations"
        self.stdout.write(self.style.SUCCESS(f"\nSyncing jobs for {sync_for}\n"))
        
        service = JobFetcherService()
        stats = service.fetch_and_sync_jobs(
            company_name=options.get("company"),
            keywords=keywords,
            location=options.get("location"),
            max_results=options.get("max"),
        )
        
        self.stdout.write(self.style.SUCCESS("\n=== SYNC SUMMARY ==="))
        for key, result in stats.items():
            if "error" in result:
                self.stdout.write(self.style.ERROR(f"{key}: {result['error']}"))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"{key}: {result['new']} new, {result['updated']} updated, {result['total']} total")
                )
