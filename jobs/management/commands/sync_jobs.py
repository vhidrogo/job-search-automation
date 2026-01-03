from textwrap import dedent

from django.core.management.base import BaseCommand

from jobs.services import JobFetcherService


class Command(BaseCommand):
    help = "Fetch and sync jobs from configured companies"
    
    def add_arguments(self, parser):
        parser.add_argument("--company", type=str, help="Specific company name")
        parser.add_argument("--keywords", type=str, help="Filter search terms (e.g., 'engineer')")
        parser.add_argument("--max", type=int, help="Max results per company per search")
    
    def handle(self, *args, **options):
        keywords = options.get("keywords")
        sync_for = f"search terms containing '{keywords}'" if keywords else "all active search configurations"
        self.stdout.write(self.style.SUCCESS(f"\nSyncing jobs for {sync_for}\n"))
        
        service = JobFetcherService()
        stats = service.fetch_and_sync_jobs(
            company_name=options.get("company"),
            keywords=keywords,
            max_results=options.get("max"),
        )
        
        # --------------------
        # Sync Summary (DB-level, informational)
        # --------------------
        self.stdout.write(self.style.SUCCESS("=== SYNC SUMMARY ==="))

        status_rows = []

        for key, result in stats.items():
            if "error" in result:
                self.stdout.write(self.style.ERROR(f"{key}: {result['error']}"))
                continue

            new = result["new"]
            updated = result["updated"]
            total = result["total"]
            applied = result.get("applied", 0)
            to_review = max(new - applied, 0)

            message = dedent(f"""
                {key}
                    {new} new
                    {updated} updated
                    {total} total
            """).strip()

            self.stdout.write(self.style.SUCCESS(message))

            if to_review > 0:
                status_rows.append((key, to_review))

        # --------------------
        # Status Summary (signal)
        # --------------------
        if status_rows:
            self.stdout.write(self.style.WARNING("\n=== STATUS SUMMARY ==="))
            for company, to_review in status_rows:
                self.stdout.write(
                    self.style.WARNING(f"{company}: {to_review} to review")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n=== STATUS SUMMARY ===\nNo new jobs to review")
            )

