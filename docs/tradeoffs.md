# Tradeoffs Log

## Purpose
This document records significant technical tradeoffs made throughout the project.  
Each entry captures context, options considered, reasoning, and reflections to make design decisions transparent and traceable over time.

Entries should focus on **architectural or system-level choices** — those that:
- Affect maintainability, scalability, or extensibility.
- Influence how components interact or evolve.
- Would be non-trivial to change later.

Minor implementation details (e.g., helper function naming, small API parameter choices) are excluded to keep this log focused on meaningful design reasoning.

## Tradeoffs

### Prompt Placeholder Substitution: `.replace()` vs String Formatting

**Context:** Needed a reliable way to insert job descriptions into LLM prompt templates for the job description parser.

**Options Considered:**
1. `.replace()` using a fixed placeholder (e.g., `{{JOB_DESCRIPTION}}`)
2. Python string formatting (e.g., `.format()` or f-strings with `{JOB_DESCRIPTION}`)

**Tradeoffs:**
- `.replace()`: ✅ safe from JSON brace conflicts, ✅ predictable behavior, ✅ simple to debug, ❌ less flexible for multi-placeholder templates  
- String formatting: ✅ scalable for multiple variables, ✅ clearer intent for dynamic fields, ❌ brittle if `{}` appear in JSON or Markdown, ❌ risk of `KeyError` or template corruption

**Decision:** Chose `.replace()` for stability and simplicity in LLM prompt handling, especially since prompts often include braces for JSON examples.

**Reflection:** If future prompts require multiple dynamic fields (e.g., `{COMPANY}`, `{ROLE}`), may revisit string formatting with careful brace escaping or use a templating library like Jinja2 for controlled substitution.

### Pydantic schema validation vs manual dictionary-based validation

**Context**  
The JDParser consumes JSON output from an LLM representing job metadata and requirements. This data must be validated before creating Django model instances to prevent schema mismatches or runtime errors.

**Options Considered**  
1. **Manual dict-based validation:**  
   Define an expected dictionary structure and verify keys, types, and required fields with custom logic.  
2. **Use Pydantic schemas:**  
   Define a typed schema (e.g., `JDModel`, `RequirementSchema`, `Metadata`) that enforces types, constraints, and defaults automatically.

**Tradeoffs**  
- **Dict-based validation:**  
  Lightweight and dependency-free, but requires repetitive manual checks (`if "role" not in data`, `isinstance(x, list)` etc.). Limited error reporting and no support for nested validation.  
- **Pydantic-based:**  
  Adds a small dependency but provides automatic type coercion, nested validation, expressive constraints (`confloat`, `conlist`), and clear error messages. It acts as a contract between the LLM and your backend.

**Decision**  
Adopt **Pydantic** for structured, type-safe validation of LLM output before ORM persistence. Use schema class naming (e.g., `RequirementSchema`) to avoid conflict with Django models.

**Reflection**  
This improves reliability, readability, and alignment with modern Python practices. It also demonstrates familiarity with strongly typed design principles, which transfer well to larger-scale systems and typed languages like Java or TypeScript.

### Requirement-Based Bullet Generation: Per-Requirement LLM Calls vs Bulk Generation

**Context:**  
When building the LLM-assisted resume writer, each requirement extracted from a job description must be satisfied with one or more bullets generated from structured work experience data. There is a decision to be made whether to generate bullets **per requirement** (many calls, fine-grained control) or **in bulk** (fewer calls, more general output).

**Options Considered:**  
1. **Per-Requirement LLM Calls:**  
   - Make an API call for each requirement, passing in the requirement, relevant experience data, and the current state of generated bullets.  
   - Track which bullets satisfy which requirements with a weighted score to later select top bullets for the final resume.  

2. **Bulk LLM Call:**  
   - Pass all requirements for all roles in a single call, asking the LLM to generate bullets for the entire set at once.

**Tradeoffs:**  
- **Per-Requirement Calls:**  
  - **Pros:**  
    - High control over relevance and quantity of bullets.  
    - Reduces risk of irrelevant or bloated output.  
    - Allows state tracking to avoid duplicates and measure coverage of requirements.  
    - Consistent results even if using older models (useful for cost management).  
  - **Cons:**  
    - Higher API call count → higher cost.  
    - More complex workflow.  

- **Bulk Call:**  
  - **Pros:**  
    - Fewer API calls → lower cost.  
    - Simpler call structure.  
  - **Cons:**  
    - Higher risk of irrelevant or excessive bullets.  
    - Harder to track coverage of individual requirements.  
    - Inconsistent outputs if model version changes or input is too large.  

**Decision:**  
Use **per-requirement calls** despite higher cost and complexity. This maximizes control, maintains high-quality bullet generation, allows consistent results across model versions, and supports the weighted score system for selecting final bullets. Bulk generation is rejected due to higher risk of irrelevant output and inconsistent quality.

**Reflection:**  
- Cost optimizations (e.g., filtering experience data or limiting requirements) are considered but largely rejected because they may degrade quality.  
- Manual or lightweight preprocessing of job descriptions (e.g., stripping non-essential sections) is a safe cost-saving measure.  
- This design prioritizes **quality and predictability over minimal cost**, which is appropriate for the resume-building use case.

### Job Description Preprocessing: Full JD vs Relevant Sections Only

**Context:**  
LLM API calls for parsing job descriptions and generating requirement-based bullets can become costly due to long input texts. Job descriptions often include sections like “About Us,” “Benefits,” and “Culture,” which are **not directly relevant** for extracting requirements or generating bullets.

**Options Considered:**  
1. **Send Full JD:**  
   - Include the entire job description text in the prompt.  
2. **Send Relevant Sections Only:**  
   - Manually or programmatically extract only sections such as “What We’re Looking For” or “Requirements.”  
   - Optionally use regex-based extraction for common section headers.

**Tradeoffs:**  
- **Full JD:**  
  - **Pros:**  
    - Maximum context; no risk of excluding potentially important information.  
  - **Cons:**  
    - High token usage → higher API cost.  
    - Longer prompts may slightly increase response time.  
    - Includes irrelevant information, which could distract the LLM.  

- **Relevant Sections Only:**  
  - **Pros:**  
    - Lower token usage → lower API cost.  
    - Focused input likely improves parsing accuracy.  
  - **Cons:**  
    - Risk of excluding niche or subtle requirements that appear outside standard sections.  
    - Regex-based automation may fail on unusual JD formats.

**Decision:**  
For now, manually select relevant sections for each JD when copying/pasting into prompts. Automation via regex or other extraction techniques may be implemented later to reduce manual work, but only if it reliably captures all important requirements.

**Reflection:**  
- This approach balances cost reduction with the need for complete, relevant context.  
- Even partial preprocessing can meaningfully reduce input tokens, lowering per-call cost without sacrificing bullet quality.  
- Maintaining a manual workflow initially ensures critical requirements are not accidentally omitted, with automation considered as a future improvement.

### Requirement Extraction Granularity: Explicit vs Implied and Sentence vs Phrase Format

**Context:**  
When parsing job descriptions into structured requirements for the resume builder, the level of granularity and phrasing impacts both the quality and cost of downstream LLM calls. The original prompt extracted all explicit and implied requirements, expressed as full sentences.

**Options Considered:**  
1. **Explicit or Implied + Full Sentences (Baseline):**  
   - Capture every possible requirement in full-sentence form.  
   - Maximizes coverage but increases token usage.  
2. **Explicit or Implied + Short Phrases:**  
   - Keep all requirements (explicit and implied) but express them concisely.  
   - Reduces input/output tokens with minimal loss of meaning.  
3. **Explicit Only + Short Phrases:**  
   - Capture only clearly stated requirements.  
   - Further reduces token count and number of API calls, but risks missing subtle or implied expectations.

**Tradeoffs:**  
- **Explicit or Implied + Full Sentences:**  
  - **Pros:** Maximum completeness and human readability.  
  - **Cons:** High token cost and redundancy.  
- **Explicit or Implied + Short Phrases:**  
  - **Pros:** Compact, token-efficient, and still captures most relevant context.  
  - **Cons:** Slightly less descriptive output, but negligible information loss for LLM use.  
- **Explicit Only + Short Phrases:**  
  - **Pros:** Minimal token and call cost; very efficient.  
  - **Cons:** May omit nuanced or implied requirements that improve match quality.

**Decision:**  
Adopt the **explicit or implied + short phrases** approach for now. This maintains full requirement coverage while reducing token usage. Future iterations may test **explicit-only** extraction if the total requirement count becomes too high.

**Reflection:**  
- The “short phrase” change provides a clear, low-risk cost optimization.  
- The “explicit-only” change remains an optional lever for future fine-tuning based on observed performance.  
- Requirement count can be tracked dynamically through model relationships rather than stored directly.

### Bullet Generation Strategy: Per-Role Batching vs Per-Requirement + State

**Context:** 
Needed a reliable, scalable, and token-efficient method to generate resume bullets from parsed job descriptions. Previous large-prompt approach (all roles + all requirements in one call) caused inconsistent bullet counts, irrelevant bullets, and token/throughput issues.

**Options Considered:**
1. **Per-requirement + full state tracking:** 
   - Generate bullets one requirement at a time, maintaining full state of bullets generated so far.
   - Input includes all work experience + accumulated bullets.
2. **Per-role batching (simplified MVP):** 
   - Generate all bullets for a single experience role in one call.
   - Input includes only that role’s work history + sorted requirements.
   - Use preconfigured max bullets per role and included roles for deterministic filtering.

**Tradeoffs:**
- Per-requirement + state:
  - ✅ Maximum control over bullets and scoring.
  - ✅ Can implement dynamic pruning based on weighted scores.
  - ❌ High complexity (state management, token tracking, pruning logic).
  - ❌ Likely hits API rate limits for output tokens if many requirements.
  - ❌ Large token usage per request (input + output).
- Per-role batching:
  - ✅ Simple, deterministic pipeline.
  - ✅ Token-efficient (each call small, under input/output limits).
  - ✅ Avoids irrelevant bullets and inconsistent totals by preconfigured rules.
  - ✅ Fewer API calls, no state tracking required.
  - ❌ Less granular control over individual requirements (rely on LLM to map requirements to bullets effectively).

**Decision:** Adopt per-role batching as the MVP approach. Use preconfigured included roles, max bullets per role, and sorted requirements to maintain quality.  

**Reflection:** 
If future use cases reveal very large JDs, unusually many requirements, or quality issues, consider revisiting per-requirement generation with state tracking and weighted scoring. For now, this approach balances quality, efficiency, and simplicity.

### Modeling Application Status as a Separate Entity

**Context**  
I needed a way to represent the lifecycle of a job application — including whether it resulted in a callback, rejection, closure, or no response — while maintaining flexibility for tracking event timing, analytics, and future extensions (like interviews or offers). The model also had to allow for easily identifying the *latest* status of any given application.

**Options Considered**  
1. **Embed a `status` field directly in `Application`**  
   - Store a simple `CharField` with predefined choices (e.g., rejected, callback, closed).  
   - Quick to implement and easy to query.  
   - However, limits historical tracking and timestamping of status changes.

2. **Use separate models for each outcome type (e.g., `Rejection`, `Callback`, `Closure`)**  
   - Provides flexibility for each event type to have custom fields.  
   - But leads to repetitive boilerplate, scattered logic, and complex relationships.

3. **Centralize statuses in a dedicated `ApplicationStatus` model** *(chosen)*  
   - A single model to represent all state transitions.  
   - Allows timestamping each status event (`status_date`).  
   - Keeps the `Application` model clean with a single `status` FK pointing to the latest known status.

**Tradeoffs**  
- **Pros:**  
  - Extensible and scalable as new states or events are added.  
  - Simplifies analytics (e.g., querying all applications with a “callback” state).  
  - Maintains historical integrity by decoupling state records from the main application entity.  
- **Cons:**  
  - Slightly more complex to manage (requires updating FK on `Application` when a new `ApplicationStatus` is created).  
  - Indirect queries (need to traverse relationships to get the most recent status).

**Decision**  
Adopted a separate `ApplicationStatus` model linked via a foreign key to `Application`, with the following schema:

#### Application
| Field | Type | Description |
|--------|------|-------------|
| id | IntegerField (primary_key=True) | Primary key |
| applied_date | DateField | When application was submitted |
| resume_id | FK(Resume) | Resume used |
| job_id | FK(Job) | Job applied to |
| status | FK(ApplicationStatus) | Latest known status |

#### ApplicationStatus
| Field | Type | Description |
|--------|------|-------------|
| id | IntegerField (primary_key=True) | Primary key |
| state | CharField(max_length=50, choices=STATUS_CHOICES) | Application state (e.g., rejected, callback, closed, etc.) |
| application_id | FK(Application) | Associated application |
| status_date | DateField | When the event occurred or was recorded |

**Reflection**  
This structure provides an elegant balance between normalization and practical usability. It keeps the system event-driven and analytics-ready without overcomplicating the schema or duplicating logic across models. As future events (like interviews or offers) are introduced, they can seamlessly integrate into this pattern or relate to `ApplicationStatus` entries.

### Resume Bullet Editability

**Context:**
The system generates structured resume bullets from LLM outputs and stores them in the `ResumeBullet` model. Initially, the assumption was that these LLM-generated bullets would remain final and directly populate the markdown resume. However, in practice, users often want to reword or exclude certain bullets, making direct markdown editing insufficiently structured and data-destructive. A design was needed that preserves structured data while allowing flexible, manual control over bullet inclusion and wording.

**Options Considered:**
1. **Edit Markdown Directly**  
   Users manually edit the markdown output and re-import or regenerate it as needed.
2. **Add `exclude` and `override_text` Fields to `ResumeBullet`**  
   Introduce structured fields allowing toggling and in-place text overrides.
3. **Physically Edit/Delete `ResumeBullet` Records**  
   Directly modify or remove bullet entries that are unsatisfactory.

**Tradeoffs:**
- **Option 1** offers simplicity but breaks the link between structured data and the final markdown output, making auditability and analytics impossible.  
- **Option 2** adds minor schema complexity but maintains full traceability, allowing reversible edits and analytics on LLM accuracy and user edits.  
- **Option 3** keeps the data minimal but sacrifices edit history and risks losing insights about LLM-generated versus human-edited content.

**Decision:**
Adopt **Option 2** by adding `exclude: BooleanField(default=False)` and `override_text: TextField(blank=True, null=True)` to the `ResumeBullet` model. Resume generation will include only non-excluded bullets and use `override_text` if present, otherwise defaulting to `text`.

**Reflection:**
This approach strikes the best balance between structure, flexibility, and future analytics. It allows iterative refinement of resume content without data loss or duplication, supporting both human-in-the-loop workflows and later evaluation of model output quality.

### LLM Cost Management Strategy: Granularity and Token Optimization

**Context:**  
As the system scaled to support multiple LLM services (JD parsing, bullet generation, and resume matching), costs became a critical consideration. Each call involves potentially thousands of tokens, making architectural cost discipline essential.

**Options Considered:**  
1. **Inline strategy within each service:**  
   - Each LLM client manages its own token handling and budget logic independently.  
2. **Centralized cost policy (chosen):**  
   - Define a shared cost strategy (`llm_cost_strategy.md`) and enforce consistent batching, token estimation, and model selection across all services.

**Tradeoffs:**  
- **Inline (per-service):**  
  - ✅ Simple and isolated.  
  - ❌ Inconsistent; duplicate logic across services.  
  - ❌ Hard to globally tune or audit total token usage.  
- **Centralized strategy:**  
  - ✅ Enables unified cost governance and global tuning.  
  - ✅ Easier to monitor and optimize with shared logging.  
  - ✅ Scales across services and future models.  
  - ❌ Requires maintaining a separate policy document and coordination layer.  

**Decision:**  
Adopt a **centralized LLM cost management strategy**, documented in `llm_cost_strategy.md`.  
Each LLM client implements shared utilities for token estimation, logging, and model routing. The orchestration layer enforces consistent cost-aware execution across all services.

**Reflection:**  
This design trades slight coordination overhead for long-term scalability and predictability.  
It future-proofs the system by allowing consistent upgrades in model selection, batching strategy, and analytics integration without rewriting individual service logic.
