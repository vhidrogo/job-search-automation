# Job Discovery & Aggregation - Subsystem Design

*Automated job discovery from company career sites with unified review interface*

## Overview

The Job Discovery & Aggregation subsystem automates discovery of job postings from company career sites and job boards, aggregating listings from multiple platforms (Workday, Greenhouse, Lever, Indeed) into a unified interface. It tracks user interactions (new/interested/dismissed/applied) and filters out previously applied positions to surface only new, relevant opportunities.

---

## Functional Requirements

### Platform Support

**Current:** Workday (primary enterprise ATS platform)
**Planned:** Greenhouse, Lever, Ashby, Indeed

The architecture uses an extensible client pattern where each platform has a dedicated client implementing a common interface for fetching and normalizing job data.

### Company Configuration

- Company model stores platform type, active status, and company-wide exclusion terms
- Platform-specific config models (WorkdayConfig, etc.) store API endpoints and location filters
- Factory method `Company.get_job_fetcher()` returns appropriate client based on platform

### Search Configuration Management

Job filtering is configured via the SearchConfig model, which supports both explicit search terms and related term variations:

- Each active SearchConfig defines a primary `search_term` (e.g., "Software Engineer")
- Each config can specify `related_terms` (e.g., ["Software Developer", "Backend Engineer"]) to capture valid title variations
- Each config can specify `exclude_terms` (e.g., ["Senior", "Staff", "Principal"]) applied across all terms
- Companies can define `exclude_terms` at the company level for company-specific filtering

**Filtering approach:**
- Service makes a single API call for the primary `search_term`
- Post-processing enforces exact match: job title must contain the `search_term` or any `related_terms`
- Then applies exclusion terms as secondary filter (both config-level and company-level)
- This approach prioritizes specificity over broad fuzzy matching

**Rationale:**
Platform search APIs lack exact-match operators and return overly broad results (e.g., "Business Analyst" searches return "Senior Software Engineer"). Rather than maintaining complex exclusion rules to filter noise, the system fetches a single broad set for the main search term and filters for known valid variations, enforcing exact title matching. This shifts effort from excluding unwanted results to curating valid term lists—a more maintainable approach as variations are discovered organically.

**Example configuration:**
```python
SearchConfig(
    search_term="Software Engineer",
    related_terms=["Software Developer", "Backend Engineer", "Python Engineer"],
    exclude_terms=["Senior", "Staff", "Principal", "Frontend"]
)
```

**Service behavior:**
- When `keywords` parameter is provided, syncs only SearchConfigs where search_term contains the keyword
- When `keywords` is omitted, syncs all active SearchConfigs
- Company-level exclude_terms are merged with config-level exclude_terms during filtering

### Syncing Process

1. **Client initialization**: Platform client created from company config
2. **API fetching**: Client handles platform-specific pagination and location filtering
3. **Title matching**: Post-processing enforces exact match against search_term and related_terms
4. **Exclusion filtering**: Applies search-specific and company-specific exclusion terms
5. **Applied job detection**: Checks fetched jobs against tracker.Job records and marks matching jobs as APPLIED
6. **Database sync**: Updates via `update_or_create`, tracking `last_fetched` timestamps
7. **Stale detection**: Jobs not in current fetch marked as `is_stale=True`
8. **Cleanup**: Stale jobs older than 30 days automatically deleted

### Deduplication

- During sync, fetched jobs are checked against `tracker.Job.external_job_id` (scoped to company)
- Jobs found in tracker are automatically set to `status=APPLIED` in JobListing
- This prevents duplicate applications and maintains consistency across views
- Applied jobs are excluded from default view but visible when filtering by "Applied" status

### Status Management

Job listings track their review state through a single `status` field with four possible values:

- **NEW**: Default state for all fetched jobs (unless already applied via tracker.Job)
- **INTERESTED**: User has flagged job for potential application
- **DISMISSED**: User has rejected job as not a fit
- **APPLIED**: Job was found in tracker.Job during sync (user already applied)

**Status transitions:**
1. **Automatic sync detection**: JobFetcherService sets status=APPLIED for jobs matching tracker.Job records
2. **User actions**: View provides controls to transition between NEW → INTERESTED → APPLIED or NEW → DISMISSED
3. **Immutable applied status**: Once marked APPLIED (either via sync or user action), jobs maintain this status

---

## Data Models

### Company
| Field | Type | Description |
|-------|------|-------------|
| id | IntegerField | Primary key |
| name | CharField | Company name (unique) |
| platform | CharField | ATS platform (workday, greenhouse, lever, ashby) |
| public_site_url | URLField | Base URL for public job listings |
| exclude_terms | JSONField | Company-specific list of terms to exclude from job titles |
| active | BooleanField | Whether to include in job syncing |

### WorkdayConfig
| Field | Type | Description |
|-------|------|-------------|
| id | IntegerField | Primary key |
| company | OneToOne(Company) | Associated company (platform must be workday) |
| base_url | URLField | Workday careers site base URL |
| tenant | CharField | Workday tenant identifier |
| site | CharField | Workday site identifier |
| location_filters | JSONField | Map of location names to Workday location IDs - all IDs used in API requests when populated |

### SearchConfig
| Field | Type | Description |
|-------|------|-------------|
| id | IntegerField | Primary key |
| search_term | CharField | Primary search keyword (e.g., "Software Engineer") - unique |
| related_terms | JSONField | List of related search terms sharing the same exclusion rules |
| exclude_terms | JSONField | List of terms to exclude from job titles (applied after exact matching) |
| active | BooleanField | Include in automated syncs |

### JobListing
| Field | Type | Description |
|-------|------|-------------|
| id | IntegerField | Primary key |
| company | FK(Company) | Company posting this job |
| external_id | CharField | Platform-specific job ID |
| title | CharField | Job title |
| location | CharField | Job location |
| url_path | CharField | Relative job path from API (combined with company.public_site_url for full URL) |
| posted_on | CharField | Posted date from platform |
| status | CharField | Current review status (new, interested, dismissed, applied) |
| search_term | CharField | Search keyword used to fetch this job |
| last_fetched | DateTimeField | Last time job appeared in API results |
| is_stale | BooleanField | No longer appears in API results |

---

## Services & Clients

### WorkdayClient

Client responsible for retrieving and normalizing job postings from the Workday platform.

**Responsibilities:**
- Retrieve job postings from the Workday API with built-in pagination
- Apply configured location constraints to all requests
- Translate Workday-specific payloads into the canonical job representation
- Handle API errors, retries, and rate limiting internally

**Exposed interface:**
- Fetch job postings based on search keywords and result limits, returning normalized job records

---

### JobFetcherService

Service responsible for orchestrating job ingestion across companies, search configurations, and platform-specific clients.

**Responsibilities:**
- Iterate through active companies and associated search configurations
- Delegate job retrieval to the appropriate platform client
- Enforce exact title matching rules per search configuration
- Apply exclusion-term filtering
- Detect and mark previously applied jobs
- Persist job data and manage stale job lifecycle
- Perform cleanup of outdated or stale job records

**Core workflow:**
- Resolve target companies and search configurations
- Fetch jobs via platform-specific clients
- Apply filtering and enrichment rules
- Synchronize results to the database and reconcile stale entries

---

## Views

### Job Listings View (`/jobs/`)

**Purpose:** Aggregated job discovery interface with status filtering and interaction tracking

**Features:**
- Status filter with options: All, New (default), Interested, Dismissed, Applied
- Automatically excludes stale jobs from all views
- Company and keyword filters
- Per-job status actions based on current state:
  - **New jobs**: Mark Interesting or Dismiss
  - **Interested jobs**: Mark Applied or Dismiss
- Bulk actions:
  - "Mark All as Dismissed" (visible when viewing new jobs)
  - "Mark All as Applied" (visible when viewing interested jobs)
- Stats display (total new jobs available)

**Status Workflow:**
1. User reviews job title and company
2. Clicks "View Job Posting" to see full listing on company site
3. Updates status:
   - NEW → INTERESTED: Flags job for potential application
   - NEW → DISMISSED: Permanently hides job (not a fit)
   - INTERESTED → APPLIED: Marks job as applied after submission
   - INTERESTED → DISMISSED: Changes mind, hides job

**Implementation Details:**
- AJAX endpoints for status updates without page reload
- Default query: `status=NEW, is_stale=False, company__active=True`
- Applied job status set during sync by JobFetcherService
- Full job URL constructed from `company.public_site_url + job.url_path`
- Select-related optimization for company data

**Endpoints:**
- `GET /jobs/` - Main view with filtering
- `POST /jobs/<id>/update-status/` - Update single job status
- `POST /jobs/bulk-dismiss-new/` - Bulk dismiss all new jobs
- `POST /jobs/bulk-mark-applied/` - Bulk mark all interested jobs as applied

---

## Command-Line Interface

### sync_jobs Management Command

Fetches and syncs jobs from configured companies.

**Usage:**
```bash
python manage.py sync_jobs [--company NAME] [--keywords TERM] [--max N]
```

**Arguments:**
- `--company`: Specific company name (optional, default: all active companies)
- `--keywords`: Filter search configurations by search_term (optional, default: all active configs)
- `--max`: Max results per company per search (optional)

**Examples:**
```bash
# Sync all jobs for all companies and search configs
python manage.py sync_jobs

# Sync only "engineer" search configs
python manage.py sync_jobs --keywords engineer

# Sync only Nordstrom
python manage.py sync_jobs --company Nordstrom

# Sync engineer roles at Nordstrom, max 50 per search
python manage.py sync_jobs --company Nordstrom --keywords engineer --max 50
```

**Output:**
```
Syncing jobs for all active search configurations

=== SYNC SUMMARY ===
Nordstrom - Software Engineer: 8 new (4 already applied), 2 updated, 10 total
Nordstrom - Data Analyst: 5 new, 1 updated, 6 total
Boeing - Software Engineer: 3 new, 0 updated, 3 total
```

---

## User Workflow

1. **Configure companies and search terms** (one-time setup via Django admin)
   - Add Company records with platform and location filters
   - Add SearchConfig records with search terms, related terms, and exclusion rules

2. **Run sync command** to fetch jobs:
   ```bash
   python manage.py sync_jobs --keywords engineer
   ```

3. **Visit `/jobs/`** to review new listings (default filter: `status=NEW`)

4. **Review each job:**
   - Click "View Job Posting" to see full details on company site
   - Mark as INTERESTED to flag for potential application
   - Mark as DISMISSED to hide permanently
   - Use "Mark All as Dismissed" for remaining uninteresting jobs

5. **Switch to interested view** (`status=INTERESTED`) to see flagged jobs

6. **Apply to jobs** (via resume generation subsystem)

7. **Mark as APPLIED** or use "Mark All as Applied" for applied jobs

8. **Next sync** only shows NEW jobs that haven't been reviewed

---

## Integration with Other Subsystems

### Application Tracking Integration

- JobFetcherService queries `tracker.Job.external_job_id` to identify applied jobs
- Automatically sets `JobListing.status=APPLIED` for matching records
- This prevents duplicate applications and maintains consistency
- When user applies via resume generation, job appears as APPLIED in next sync

### Resume Generation Integration

- User identifies interesting jobs via job listings view
- Copies job posting URL to use as input for resume generation
- After generating resume and applying, manually marks job as APPLIED
- Future syncs will automatically detect application via tracker.Job

---

## Future Enhancements

- Additional platform support (Greenhouse, Lever, Ashby, Indeed)
- Automated application detection via email parsing or browser extension
- Job recommendation engine based on application history
- Salary range filtering and company size filtering
- Save search configurations with email/push notifications for new matches