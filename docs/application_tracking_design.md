# Application Tracking & Metrics - Subsystem Design

*Comprehensive tracking and analytics for job applications and outcomes*

## Overview

The Application Tracking subsystem tracks job applications from submission through final outcome, capturing status transitions (callbacks, rejections, closures) and enabling funnel analytics. It provides dimensional analysis across role, location, salary, and other attributes to identify success patterns.

---

## Functional Requirements

### Application Lifecycle Tracking

**Core workflow:**
1. User creates Application record after applying to a job
2. Application references Job (with requirements) and Resume
3. System tracks status transitions via ApplicationStatus records
4. System tracks interview scheduling via Interview records
5. System tracks final outcome via InterviewProcessStatus (if interviews occurred)

**Status types:**
- **Callback**: Received response requesting interview
- **Rejected**: Application rejected without interview
- **Closed**: Position closed/filled
- **No status**: No response received (default state)

**Interview process outcomes:**
- **Offer**: Received job offer
- **Rejected**: Rejected after interview process
- **Failed**: Did not perform well in interviews
- **Ghosted**: No communication after interviews
- **Withdrew**: Candidate withdrew from process

### Multi-Dimensional Analytics

**Analysis dimensions:**
- Role, specialization, level
- Location (with metro area grouping)
- Work setting (remote, hybrid, onsite)
- Experience requirements
- Salary ranges (bucketed)
- Time-based trends

**Key metrics:**
- Callback rate (callbacks / total applications)
- Rejection patterns by dimension
- Interview-to-offer conversion rate
- Application volume over time
- Top performing dimensions

---

## Data Models

### Application
| Field | Type | Description |
|-------|------|-------------|
| id | IntegerField | Primary key |
| applied_date | DateField | When application was submitted |
| job_id | OneToOne(Job) | Job applied to |

### ApplicationStatus
| Field | Type | Description |
|-------|------|-------------|
| id | IntegerField | Primary key |
| state | CharField | Application state (rejected, callback, closed) |
| application_id | OneToOne(Application) | Associated application |
| status_date | DateField | When event occurred |

### Interview
| Field | Type | Description |
|-------|------|-------------|
| id | IntegerField | Primary key |
| application | FK(Application) | Associated application |
| stage | CharField | Interview stage (recruiter_screen, technical_screen, final_loop) |
| format | CharField | Interview format (phone_call, virtual_meeting) |
| focus | CharField | Focus area (coding, system_design, behavioral, hiring_manager) |
| interviewer_name | CharField | Interviewer name |
| interviewer_title | CharField | Interviewer title/role |
| scheduled_at | DateTimeField | Interview schedule time |
| notes | TextField | Freeform interview notes |

### InterviewProcessStatus
| Field | Type | Description |
|-------|------|-------------|
| id | IntegerField | Primary key |
| application | OneToOne(Application) | Associated application |
| outcome | CharField | Final outcome (offer, rejected, failed, ghosted, withdrew) |
| outcome_date | DateField | When outcome occurred |
| notes | TextField | Optional context |

---

## Views

### Application Detail View (`/applications/<id>/`)

**Purpose:** Single-application reference page

**Dynamic content based on state:**

**For callbacks:**
- Job details
- Resume (HTML-rendered with styling)
- Upcoming interviews
- Interview history with notes

**For rejections:**
- Job details
- Job requirements (sorted by relevance)
- Resume

**For pending/no status:**
- Job details
- Resume only

**Implementation:**
- Conditional rendering based on ApplicationStatus.state
- Requirements fetched only for rejected applications
- Interviews filtered into upcoming vs past based on current time
- Resume CSS dynamically injected for proper rendering

### Application Metrics View (`/metrics/`)

**Purpose:** Multi-dimensional analytics dashboard

**Analysis sections:**

1. **Overall Summary**
   - Total applications with status breakdown
   - Application volume timeline (line chart)

2. **Callback Analysis**
   - Dimensional breakdowns (role, level, location, work_setting, experience, salary)
   - Callback timeline (bar chart by applied date)

3. **Rejection Analysis**
   - High-level summary (top 3 values for role, location, work_setting)

4. **Dimension Deep Dive**
   - Detailed table per dimension value
   - Shows total/callbacks/rejected/closed/no-response counts

**Filtering:**
- Date range (start/end date)
- All job dimensions (role, specialization, level, location, work_setting)
- Filters apply globally to all sections

**Implementation:**
- Location grouping for Greater Seattle/Chicago areas
- Salary bucketing (<$150k, $150k-$180k, $180k-$200k, >$200k)
- Timeline charts include zero-count dates
- Chart.js for visualizations

### Company Applications View (`/company/<company_name>/`)

**Purpose:** Quick reference when browsing company careers page

**Status filtering:**
- **All**: Every application to company
- **Active**: No response OR interviewing
- **Inactive**: Rejected, closed, or interview concluded

**Status display logic:**
1. Interview process outcome (if exists)
2. Callback → "Interviewing"
3. ApplicationStatus state
4. No status → "No Response"

**Implementation:**
- Q objects for complex status filtering
- Status derived from multiple related models
- Ordered by applied_date (newest first)

### Upcoming Interviews View (`/interviews/upcoming/`)

**Purpose:** Interview preparation dashboard

**Features:**
- Chronological list of future interviews
- Filter by interview stage
- Days-until countdown
- Links to application details

**Implementation:**
- Filters where `scheduled_at > now()`
- Django `timeuntil` filter for countdown
- Select-related optimization for company/job info

---

## User Workflow

### Application Creation

1. User applies to job using generated resume
2. User creates Application record in Django admin
3. Links to Job and Resume records
4. Sets applied_date

### Status Updates

**Callback workflow:**
1. User receives callback request
2. Creates ApplicationStatus record with state="callback"
3. Creates Interview records for scheduled interviews
4. System displays application in "Active" filter

**Rejection workflow:**
1. User receives rejection
2. Creates ApplicationStatus record with state="rejected"
3. Application detail view shows job requirements for gap analysis

**Interview completion workflow:**
1. Interviews complete
2. User creates InterviewProcessStatus record with final outcome
3. System tracks in metrics for interview-to-offer conversion

### Interview Notes

1. User takes notes during/after interview (in separate text file or notepad)
2. User pastes notes into Interview.notes field via Django admin
3. Notes display in application detail view for reference

### Analytics Review

1. User visits `/metrics/` periodically
2. Reviews callback rates by dimension
3. Identifies successful patterns (e.g., "SWE II in Seattle has 40% callback rate")
4. Adjusts application strategy based on insights

---

## Integration with Other Subsystems

### Resume Generation Integration

- Application references Resume via FK
- Enables traceability: JD → Requirements → Resume → Application → Outcome
- Application detail view renders resume for reference

### Job Discovery Integration

- JobListing.status automatically set to APPLIED when Application created
- Prevents duplicate applications in job listings view
- Maintains consistency across subsystems

### Interview Preparation Integration

- Application serves as parent for InterviewPreparationBase
- Interview records link to InterviewPreparation documents
- Enables interview prep workflow

---

## Future Enhancements

- Automated email parsing for status updates
- Browser extension for one-click application logging
- Predictive analytics (ML model for callback probability)
- A/B testing framework for resume variations
- Cohort analysis (track application batches over time)
- Export functionality (CSV, PDF reports)