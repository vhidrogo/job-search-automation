class JobFetcherClientError(Exception):
    """Base exception for all job fetcher clients."""


class WorkdayClientError(JobFetcherClientError):
    """Workday-specific client failure."""
