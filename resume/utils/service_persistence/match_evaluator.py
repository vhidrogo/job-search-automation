from resume.services import ResumeMatcher
from tracker.models import Job

def evaluate_and_update_match(job_id: int) -> None:
    job = Job.objects.get(pk=job_id)

    matcher = ResumeMatcher()
    match_result = matcher.evaluate(job_id)

    job.resume.match_ratio = match_result.match_ratio
    job.resume.unmet_requirements = match_result.unmet_requirements
    job.resume.save(update_fields=["match_ratio", "unmet_requirements"])
