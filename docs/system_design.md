# Job Search Automation System Design

## Overview
The Job Search Automation project automates the generation and tailoring of resumes to job descriptions (JDs).  
The system reads a JD, extracts structured requirements and metadata via an LLM, and generates role-specific experience bullet points and skills aligned with selected experience templates.  
This design emphasizes modularity, configurability, and token-efficient LLM orchestration.

---

## High-Level Architecture

```
job_search_automation/ (Django Project)
├── job_search_automation/        # Django project settings, URLs, WSGI
├── resume/                       # LLM-based resume generation app
│   ├── models/                   # Models for persisting resume data
│   ├── prompts/                  # Reusable and versioned LLM prompts
│   ├── schemas/                  # Pydantic schemas for validating all LLM outputs
│   ├── services/                 # External API clients (ClaudeClient)
│   ├── templates/                # Markdown templates per role
│   ├── utils/                    # Internal logic: ResumeWriter, JDParser
├── tracker/                      # Job/application logging and analytics
│   ├── models/                   # Models for persisting job and application data
│   └── utils/                    # ApplicationLogger
├── orchestration/                # CLI / orchestration entrypoints (management commands or scripts)
│   ├── orchestrator.py           # thin Orchestrator that imports resume + tracker logic and runs end-to-end
│   ├── management/commands/      # CLI commands / Django commands (run_orchestrator.py)
├── db.sqlite3                    # Local data store
└── manage.py
```

---

## Core Classes and Responsibilities

| Class | Responsibility |
|-------|----------------|
| **ClaudeClient** | Wraps LLM API calls (`generate()`, `count_tokens()`), handles configuration and model defaults. |
| **ResumeWriter** | Handles LLM-driven **bullet generation** for a given experience role and requirements; includes `generate_experience_bullets()` and `generate_skill_bullets()` to produce both experience and skill-section entries used by `Resume` rendering. |
| **JDParser (JDParser)** | Parses JD text → extracts requirements and metadata (JSON). |
| **Orchestrator** | Orchestrator CLI/entrypoint: invokes JDParser, calls ResumeWriter for bullets, persists Job/Requirement/Resume/ResumeBullet via tracker models, and manages iterative match/repair flows. |
| **Resume (model methods)** | Responsible for on-demand rendering: `_generate()` (assemble template + bullets), `saveToMarkdown()`, `saveToPdf()` — these use persisted models to render output when called. |
| **ResumeMatcher** | LLM-assisted utility that, given a job's requirements and the current resume (bullets), returns which requirements are met/missing and enables iterative improvement of `match_ratio`. |

---

## Functional Requirements

### JD Ingestion
- Read JD from a local file (e.g., `jd.txt`).
- Normalize and clean text.

### Requirements & Metadata Extraction
- Make LLM API call.
- Return structured JSON:
- **Validate the returned JSON against the `JDModel` Pydantic schema** to ensure the response adheres to expected types and structure before persisting to the database. Any validation failure halts the flow and surfaces a descriptive error.


```
{
   "metadata": {
      "company": "Meta",
      "listing_job_title": "Software Engineer",
      "role": "Software Engineer",
      "work_setting": "Remote"
   },
   "requirements": [
         {
            "text": "Strong Python skills",
            "keywords": ["Python"], 
            "relevance": 0.9
         }
   ]
}
```

### Template Handling
- Maintain Markdown templates for multiple roles in `resume/templates/`.  
- Template selection is driven by `ResumeTemplate` + the `TemplateRoleConfig` rows (use `template.role_configs` to find which `ExperienceRole`s to include and the configured `max_bullet_count` per role).  
- The orchestrator / resume-renderer should fetch `ResumeTemplate`, then `template.role_configs.filter(include=True).order_by(...)` to determine role order and bullet counts for generation and rendering.

### Bullet Generation

#### Previous (Complex) Design
- One LLM call per requirement.
- Shared state between calls to maintain context.
- Complex pruning, deduplication, and weighted scoring.
- Token-heavy and required rate limiting.

#### Current (Simplified Per-Role) Design
- One LLM call per **experience role**, not per requirement.
- Input: all requirements (sorted by relevance) + experience details for one role.
- Output: up to *N* bullets (preconfigured) for that role.
- **All bullet-generation responses are also validated with Pydantic models** before any ORM persistence, ensuring schema correctness and safe downstream usage.

This approach:
- Keeps input well under the per-request token limit.
- Avoids rate limiting due to fewer calls.
- Produces consistent bullet counts and relevance.
- Simplifies orchestration while maintaining strong quality control.
- Ensures validated, structured outputs for downstream persistence.

### Output Generation
- Save Markdown resume.
- Optional PDF conversion.
- Maintain versioning.

### Application Logging
- Store JD metadata, extracted requirements, and generated resume info.
- Validate and persist via Django ORM.

---

## Validation Layer

All LLM outputs—whether from **JDParser** (requirements extraction), **ResumeWriter** (bullet generation), or **ResumeMatcher** (evaluation)—undergo **schema validation via Pydantic** before any persistence or downstream processing.

### Purpose
- Guarantee structured and type-safe data flowing into the Django model layer.
- Catch malformed or incomplete LLM responses early, with clear developer-facing error messages.
- Standardize validation logic across all services interacting with the LLM.

### Implementation Summary
- Each LLM service defines its corresponding Pydantic schema (e.g., `JDModel`, `BulletListModel`, `MatchResultModel`).
- Validation occurs immediately after receiving LLM output and before ORM operations.
- Validation failures raise descriptive exceptions to prevent silent data corruption or inconsistent states.

This validation step is mandatory across all LLM-integrated modules.

---

## Data Model Design

### App and Model Organization

To maintain modularity between the resume-generation domain and the job-tracking domain, models are distributed across **domain-specific Django apps** rather than centralized in one location. This structure supports future growth (e.g., adding analytics or orchestration apps) without creating coupling between unrelated domains.

| App | Domain | Core Models | Responsibility |
|------|---------|--------------|----------------|
| **resume** | Resume generation | `ResumeTemplate`, `TemplateRoleConfig`, `Resume`, `ResumeExperienceBullet`, `ResumeSkillBullet`, `ExperienceRole`, `ExperienceProject` | Manages templates, experience data, and generated resume artifacts. |
| **tracker** | Job and application tracking | `Job`, `Requirement`, `ContractJob`, `Application`, `ApplicationStatus` | Manages job postings, parsed requirements, applications, and status updates. |

**Rationale:**
- Keeps resume logic independent from job tracking logic.
- Enables modular testing and database migrations.
- Supports clean orchestration via `Orchestrator`, which coordinates both domains.
- Allows new domain apps (e.g., analytics, orchestration) to be added without refactoring existing models.

**Cross-App Relationships:**
- The `Resume` model references `tracker.Job` (via FK) since resumes are generated for specific jobs.
- Cross-app foreign keys are defined using the `app_label.ModelName` convention, e.g.:

    ```python
    job = models.ForeignKey("tracker.Job", on_delete=models.CASCADE)
    ```

**Model Organization:**
Each app uses a `models/` directory instead of a single `models.py` file, improving maintainability and clarity as the model layer expands.

```
resume/
  models/
    resume.py
    resume_experience_bullet.py
    resume_skill_bullet.py
    resume_template.py
    experience_role.py
    template_role_config.py

tracker/
  models/
    job.py
    requirement.py
    application.py
    application_status.py
```

Each directory includes an `__init__.py` file that imports all model classes, enabling simple imports throughout the codebase (e.g., `from resume.models import Resume`).

### Models by Domain Diagram
```mermaid
flowchart TD
    subgraph Resume App
        RT[ResumeTemplate]
        TRC[TemplateRoleConfig]
        R[Resume]
        REB[ResumeExperienceBullet]
        RSB[ResumeSkillBullet]
        ER[ExperienceRole]
        EP[ExperienceProject]

        RT --> TRC
        TRC --> ER
        R --> REB
        R --> RSB
        ER --> EP
    end

    subgraph Tracker App
        J[Job]
        C[ContractJob]
        Req[Requirement]
        A[Application]
        AS[ApplicationStatus]

        J --> Req
        J --> C
        A --> R
        A --> J
        A --> AS
    end

    %% Cross-app references
    R --> J
```

### Core Models

#### Job
| Field | Type | Description |
|--------|------|-------------|
| id | IntegerField | Primary key |
| company | CharField | Company name |
| listing_job_title | CharField | Title from job description |
| role | CharField | Job role |
| specialization | CharField | Optional specialization |
| level | CharField | Level designation |
| location | CharField | Job location |
| work_setting | CharField | Work setting |
| min_experience_years | PositiveIntegerField | Minimum years of experience |
| min_salary | IntegerField | Minimum salary |
| max_salary | IntegerField | Maximum salary |

#### ContractJob
| Field | Type | Description |
|-------|------|-------------|
| id | int | Primary key |
| job_id | FK(Job) | Base job this contract role is associated with |
| consulting_company | CharField | Optional consulting company through which the contract is offered |
| contract_length_months | PositiveIntegerField | Duration of the contract in months |
| hourly_rate | FloatField | Hourly pay rate for the contract |
| provides_benefits | BooleanField | Whether the contract provides benefits |
| provides_pto | BooleanField | Whether the contract provides paid time off |

#### Requirement
| Field | Type | Description |
|--------|------|-------------|
| id | IntegerField | Primary key |
| job_id | FK(Job) | Source JD |
| text | TextField | Requirement text |
| relevance | FloatField | Relevance score (0–1, higher means more important) |
| order | IntegerField | Position in the LLM-sorted list; used to preserve a deterministic order when relevance scores are equal |

#### ResumeTemplate
| Field | Type | Description |
|--------|------|-------------|
| id | IntegerField | Primary key |
| target_role | CharField | e.g., "Software Engineer" |
| target_level | CharField | e.g., "II" |
| template_path | CharField | Path to Markdown template |

#### Resume
| Field | Type | Description |
|--------|------|-------------|
| id | IntegerField | Primary key |
| template_id | FK(ResumeTemplate) | Which template was used |
| job_id | FK(Job) | Job description source |
| unmet_requirements | CharField | CSV string of unmatched tools/technologies (e.g., "Go,Ruby on Rails") |
| match_ratio | FloatField | (Met requirements / total requirements) |

#### ResumeExperienceBullet
| Field | Type | Description |
|--------|------|-------------|
| id | IntegerField | Primary key |
| resume | FK(Resume) | Associated resume |
| order | IntegerField | Display order |
| text | TextField | Bullet content |
| exclude | BooleanField | Whether to exclude this bullet from the generated resume |
| override_text | TextField | Optional manually edited version of the bullet that takes priority over `text` |

#### ResumeSkillBullet
| Field | Type | Description |
|--------|------|-------------|
| id | IntegerField | Primary key |
| resume | FK(Resume) | Associated resume |
| category | CharField | Category label such as "Programming Languages" or "Data & Visualization" |
| skills_text | TextField | CSV string of related skills (e.g., "Python, Java") |

#### ExperienceRole
| Field | Type | Description |
|--------|------|-------------|
| id | IntegerField | Primary key |
| key | CharField | Stable identifier used by templates (e.g., "navit_swe", "amazon_sde") |
| company | CharField | Employer name (e.g., "Nav.it") |
| title | CharField | Job title (e.g., "Software Engineer") |
| display_name | CharField | Optional human-facing name; if null, render as `title – company` |

#### ExperienceProject
| Field | Type | Description |
|--------|------|-------------|
| id | IntegerField | Primary key |
| experience_role | FK(ExperienceRole) | Associated role |
| short_name | CharField | Short label for the project/task |
| problem_context | TextField | Short problem statement (concise) |
| actions | CharField | CSV string of action items (e.g., "implemented X, rewrote Y") |
| tools | CharField | CSV string of tools/technologies (e.g., "Django,Postgres") |
| outcomes | CharField | CSV string of short outcomes (e.g., "reduced latency 80%") |
| impact_area | CharField | e.g., "Performance Optimization", "User Engagement" |

#### TemplateRoleConfig
| Field | Type | Description |
|--------|------|-------------|
| id | IntegerField | Primary key |
| template | FK(ResumeTemplate) | Which template |
| experience_role | FK(ExperienceRole) | Which experience role |
| include | BooleanField | Whether to include this role in this template |
| max_bullet_count | PositiveIntegerField | Max number of bullets to generate for this role |

#### Application
| Field | Type | Description |
|--------|------|-------------|
| id | IntegerField | Primary key |
| applied_date | DateField | When application was submitted |
| resume_id | FK(Resume) | Resume used |
| job_id | FK(Job) | Job applied to |
| status | FK(ApplicationStatus) | Latest known status |

#### ApplicationStatus
| Field | Type | Description |
|--------|------|-------------|
| id | IntegerField | Primary key |
| state | CharField | Application state (e.g., rejected, callback, closed, etc.) |
| application_id | FK(Application) | Associated application |
| status_date | DateField | When the event occurred or was recorded |

---

### End-to-End Flow Diagram

```mermaid
flowchart TD
    A["User saves JD file (jd.txt)"] --> B["Orchestrator.run()"]
    B --> C["JDParser.parse(path_to_file)"]
    C --> D["Persist Job + Requirements via tracker models"]
    D --> E["Fetch ResumeTemplate (by Job.role + Job.level)"]
    E --> F["Fetch TemplateRoleConfig → ExperienceRoles"]
    F --> G["For each ExperienceRole: ResumeWriter.generate_experience_bullets()"]
    G --> H["ResumeWriter.generate_skill_bullets()"]
    H --> I["Persist Resume + ResumeExperienceBullet + ResumeSkillBullet objects"]
    I --> J["ResumeMatcher.evaluate() → update match_ratio + unmet_requirements"]
    J --> K["User reviews + edits bullets (override/exclude)"]
    K --> L["ResumeMatcher re-run (optional)"]
    L --> M["User triggers application save (Application + Resume.saveToPdf())"]
    M --> N["Admin updates ApplicationStatus for outcome tracking"]
    N --> O["Analytics layer: compute feedback loops & high-ROI insights"]
```

---

## Design Decisions & Tradeoffs

See [Tradeoffs](./tradeoffs.md)

---

## Incremental Build Plan

Incremental Build Plan

| Phase | Focus | Output |
|--------|--------|---------|
| [x] Phase 1 | Django project + resume app setup | Working environment |
| [x] Phase 2 | JD extraction (metadata + requirements) | JSON output |
| [ ] Phase 3 | Template selection | Correct Markdown template (TemplateRoleConfig-based) |
| [ ] Phase 4 | Bullet generation loop | Persisted Resume + ResumeBullet entries |
| [ ] Phase 5 | Skill-section generation | Persisted ResumeSkillBullet entries (generated after experience bullets) |
| [ ] Phase 6 | Resume rendering | `_generate()` + `saveToMarkdown()` / `saveToPdf()` |
| [ ] Phase 7 | Iterative match utility | `ResumeMatcher` to evaluate & improve `match_ratio` |
| [ ] Phase 8 | tracker app expansion | End-to-end automation, analytics, dashboards |

---

## Future Enhancements
- *Iterative Match Workflow:* add `ResumeMatcher` (LLM-assisted) to enable on-demand evaluation of which requirements are satisfied, drive iterative `ExperienceProject` additions/overrides, and update `match_ratio`.
- Batch generation for multiple JDs.
- *Resume feedback analytics:* correlate application outcomes (rejected/callback) with resume features (match_ratio, template, overrides) to identify high-ROI targets and guide generation improvements. 
- Analytics/Dashboarding
- **General and Company-Tailored Resume Modes:**
  - *General Target Role Resume:* Generate a “framed” resume for a target role (e.g., *Data Engineer*) when limited or no requirements are provided — such as when a recruiter message lacks a full JD. The system leverages the role-specific template and weighted prior experience configurations to infer likely requirements and produce a strong generic framing.
  - *Company-Tailored Resume:* Generate resumes explicitly aligned with a company’s known leadership principles or values (e.g., Amazon LPs, Meta Leadership). This mode enriches bullet phrasing and ordering to reflect organizational priorities without requiring a full job description.
- **Model Flexibility and Benchmarking:**
  - Introduce configurable model selection to allow using different LLM providers (e.g., Anthropic, OpenAI) and versions (e.g., `claude-sonnet-4-5`, `claude-haiku-4-5`, `gpt-4.1`, etc.).
  - Support per-utility model selection so that modules can use optimal models for their complexity:
    - Example: more context-heavy tasks (e.g., `generate_experience_bullets()` or iterative match evaluation) may use higher-capacity models like `claude-sonnet-4-5`.
    - Example: `generate_skill_bullets()` may use a faster, cheaper model like `claude-haiku-4-5`.
  - Implement a benchmarking and metrics layer to track model **cost**, **latency**, and **output quality** (e.g., validation success rate, token usage).
  - Aggregate and visualize results to guide model selection decisions and cost-performance optimization over time.


---
