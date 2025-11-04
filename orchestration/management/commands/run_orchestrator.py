from django.core.management.base import BaseCommand, CommandError
from orchestration.orchestrator import Orchestrator


class Command(BaseCommand):
    help = (
        "Runs the orchestration workflow: parse job description, persist data, generate resume, render PDF"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "jd_path",
            type=str,
            help="Path to the job description file to process",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="output/resumes",
            help="Directory where generated PDF(s) will be saved",
        )
        parser.add_argument(
            "--no-open",
            action="store_false",
            dest="auto_open_pdf",
            help="Do not auto-open the generated PDF after creation",
        )

    def handle(self, *args, **options):
        jd_path = options["jd_path"]
        output_dir = options["output_dir"]
        auto_open = options["auto_open_pdf"]

        orchestrator = Orchestrator()
        try:
            resume = orchestrator.run(
                jd_path=jd_path,
                output_dir=output_dir,
                auto_open_pdf=auto_open,
            )
        except Exception as e:
            raise CommandError(f"Orchestration failed: {e}")

        self.stdout.write(self.style.SUCCESS(
            f"Orchestration completed successfully for JD at {jd_path}"
        ))
