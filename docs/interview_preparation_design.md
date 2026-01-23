# Interview Preparation - Subsystem Design

*LLM-generated interview preparation materials tailored to stage and type*

## Overview

The Interview Preparation subsystem manages interview scheduling and generates structured preparation materials (company context, callback drivers, background narratives, predicted questions) tailored to each interview stage. Preparation documents are dynamically rendered based on interview type (recruiter/technical/hiring manager).

---

## Functional Requirements

### Preparation Document Types

**Base Preparation (once per application):**
Generated when application has scheduled interviews, includes:
- Formatted job description with bolded callback drivers
- Company and product context
- Primary callback drivers (1-3 key screening signals)
- Targeted background narrative (opening, core, forward hook)

**Interview-Specific Preparation (per interview):**
Generated for each scheduled interview, includes:
- Sequential preparation roadmap (4 phases: Foundation Review, Active Practice, Polish & Integration, Final Confidence Check)
- 3-5 predicted questions with structured STAR responses
- 5 interviewer-aligned questions with strategic rationale
- Resume defense preparation for high-risk or high-signal resume bullets
- Targeted technical deep dives based on resume claims, job requirements, and prior interview feedback
- Calibrated to interview stage, interviewer role, and focus area

### Generation Approach

**Base preparation generation:**
- Single LLM call generates all base content
- Input: Job.raw_jd_text + Application metadata
- Output: Markdown-formatted sections
- Validates JSON structure before persistence

**Interview-specific generation:**
- One LLM call per interview
- Input:
  - Base preparation context
  - Resume (rendered bullets)
  - Resume Projects (structured source project data behind resume bullets)
  - Prior Interview Notes (structured notes from earlier rounds)
  - Interview metadata (stage, focus, interviewer)
- Output: Markdown-formatted preparation sections
- Explicitly reuses Resume Projects data to generate authentic STAR responses, resume defense prep, and technical deep dives
- Calibrates depth and focus using interview stage and prior interview feedback

**LLM prompt structure:**
- System prompt defines role and output format
- User prompt includes job context and interview details
- Requests markdown formatting for direct persistence
- JSON wrapper for validation via Pydantic
- Resume Projects provided as structured JSON to preserve technical detail behind resume bullets
- Prior Interview Notes provided as structured JSON to target known weak areas and avoid repetition
- Supports large prompt and output sizes via streaming responses

### Manual Editability

- All content stored as markdown TextField
- Users can edit directly in Django admin
- Re-rendering automatic when viewing prep page

---

## Data Models

### InterviewPreparationBase
| Field | Type | Description |
|-------|------|-------------|
| id | IntegerField | Primary key |
| application | OneToOne(Application) | Associated application |
| formatted_jd | TextField | Markdown-formatted JD with bolded drivers |
| company_context | TextField | Company/product info (markdown) |
| primary_drivers | TextField | 1-3 key screening signals (markdown) |
| background_narrative | TextField | Opening, core, forward hook (markdown) |

### InterviewPreparation
| Field | Type | Description |
|-------|------|-------------|
| id | IntegerField | Primary key |
| interview | OneToOne(Interview) | Associated interview |
| prep_plan | TextField | Sequential preparation roadmap with prioritized tasks (markdown) |
| predicted_questions | TextField | 3-5 questions with STAR responses (markdown) |
| interviewer_questions | TextField | 5 strategic questions with rationale (markdown) |
| resume_defense_prep | TextField | Bullet-by-bullet defense strategies using resume project data (markdown) |
| technical_deep_dives | TextField | Targeted technical topics with prepared explanations (markdown) |

---

## Services

### InterviewPrepGenerator

Service responsible for generating and persisting interview preparation content using LLMs.

**Responsibilities:**
- Generate baseline preparation content for an application
- Generate interview-specific preparation content
- Preserve and reuse resume project data behind resume bullets
- Incorporate prior interview notes to target gaps and weaknesses
- Construct prompts using application, job, resume, and interview context
- Validate generated output against structured schemas
- Persist preparation content in markdown form

**Core workflow:**
- Assemble application and job context
- Generate base preparation content
- Generate interview-specific preparation content
- Validate structured output
- Persist finalized markdown content

---

## Views

### Interview Preparation View (`/applications/<id>/interview-prep/`)

**Purpose:** Single-page interview prep reference with dynamic interview filtering

**Content sections:**

**Always visible (base prep):**
- Formatted job description
- Company context
- Primary callback drivers
- Background narrative

**Interview-specific (dynamic):**
- Preparation roadmap (sequential tasks at candidate's pace)
- Predicted questions with STAR responses
- Interviewer questions with rationale
- Resume defense preparation
- Technical deep dives

**Features:**
- Dropdown selector to switch between interviews
- Markdown rendering with proper formatting
- Print-friendly styling
- Warning if prep not generated yet

**Implementation:**
- URL parameter `?interview_id=X` for direct linking
- `marked.js` for client-side markdown rendering
- OneToOne relationships for data fetching
- Base prep fetched once, interview prep fetched per dropdown change

---

## Django Admin Actions

### Generate Base Preparation (Application Admin)

**Trigger:** Admin action on Application changelist

**Behavior:**
- Available for applications with scheduled interviews
- Generates InterviewPreparationBase if not exists
- Shows success/error message
- Can be run on multiple applications at once

### Generate Interview Preparation (Interview Admin)

**Trigger:** Admin action on Interview changelist

**Behavior:**
- Available for scheduled interviews
- Generates InterviewPreparation for selected interview(s)
- Requires InterviewPreparationBase to exist (generates if missing)
- Shows success/error message
- Can be run on multiple interviews at once

---

## User Workflow

### Initial Setup

1. User creates Interview records via Django admin after scheduling
2. Records include: stage, format, focus, interviewer details, scheduled_at

### Preparation Generation

1. **Generate base preparation:**
   - Navigate to Application admin changelist
   - Select application(s) with scheduled interviews
   - Choose "Generate base preparation" admin action
   - System generates InterviewPreparationBase

2. **Generate interview-specific preparation:**
   - Navigate to Interview admin changelist
   - Select scheduled interview(s)
   - Choose "Generate interview preparation" admin action
   - System generates InterviewPreparation for each selected interview

3. **User reviews prep documents** via `/applications/<id>/interview-prep/`

### Pre-Interview Review

1. User visits prep view before interview
2. Selects specific interview from dropdown
3. Follows preparation roadmap to structure study and practice
4. Reviews predicted questions and STAR responses
5. Reviews interviewer questions and rationale
6. Optionally prints page for offline reference

### Post-Interview Updates

1. User edits Interview.notes field with actual questions asked and self-reflection
2. Notes are used as input for future interview-specific preparation
3. Follow-on interview prep emphasizes areas of uncertainty or poor performance
4. Preparation documents can be regenerated to reflect updated feedback

---

## Integration with Other Subsystems

### Application Tracking Integration

- InterviewPreparationBase links to Application (OneToOne)
- Interview records link to Application (FK)
- Enables prep generation workflow after interview scheduling

### Resume Generation Integration

- Base prep uses Job.raw_jd_text (stored during resume generation)
- Enables reformatting JD with callback drivers highlighted
- Callback drivers derived from resume screening context

### Resume Project Context Integration

- Resume bullets are linked to their source ExperienceProject records
- Interview preparation uses these projects as the authoritative source for:
  - STAR Situation / Action / Result details
  - Technical stack explanations
  - Architectural decisions and tradeoffs
  - Concrete metrics and outcomes
- Ensures interview prep can defend every resume claim with authentic, consistent detail

---

## Future Enhancements

- Interview recording transcription and analysis
- Post-interview reflection prompts
- Question bank with tagging (behavioral, technical, system design)
- Company-specific interview guides (known questions, processes)
- Interview performance self-assessment
- Automated follow-up email generation
- Automatic identification of resume bullets at risk of weak defense
- Confidence scoring for technical topics based on prior interview notes
- Longitudinal tracking of improvement across interview rounds