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

### Foundation & Infrastructure
Decisions affecting system-wide architecture, validation, and cost management.

---

#### LLM Cost Management Strategy: Granularity and Token Optimization

**Context:**  
As the system scaled to support multiple LLM services (JD parsing, bullet generation, and resume matching), costs became a critical consideration. Each call involves potentially thousands of tokens, making architectural cost discipline essential.

**Options Considered:**  
1. **Inline strategy within each service:**  
   - Each LLM client manages its own token handling and budget logic independently.  
2. **Centralized cost policy:**  
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
Adopt a **centralized LLM cost management strategy**, documented in `llm_cost_strategy.md`. Each LLM client implements shared utilities for token estimation, logging, and model routing. The orchestration layer enforces consistent cost-aware execution across all services.

**Reflection:**  
This design trades slight coordination overhead for long-term scalability and predictability. It future-proofs the system by allowing consistent upgrades in model selection, batching strategy, and analytics integration without rewriting individual service logic.

---

#### Pydantic Schema Validation vs Manual Dictionary-Based Validation

**Context:**  
The JDParser consumes JSON output from an LLM representing job metadata and requirements. This data must be validated before creating Django model instances to prevent schema mismatches or runtime errors.

**Options Considered:**  
1. **Manual dict-based validation:**  
   - Define an expected dictionary structure and verify keys, types, and required fields with custom logic.  
2. **Use Pydantic schemas:**  
   - Define a typed schema (e.g., `JDModel`, `RequirementSchema`, `Metadata`) that enforces types, constraints, and defaults automatically.

**Tradeoffs:**  
- **Dict-based validation:**  
  - ✅ Lightweight and dependency-free.  
  - ❌ Requires repetitive manual checks (`if "role" not in data`, `isinstance(x, list)` etc.).  
  - ❌ Limited error reporting and no support for nested validation.  
- **Pydantic-based:**  
  - ✅ Automatic type coercion and nested validation.  
  - ✅ Expressive constraints (`confloat`, `conlist`) and clear error messages.  
  - ✅ Acts as a contract between the LLM and backend.  
  - ❌ Adds a small dependency.

**Decision:**  
Adopt **Pydantic** for structured, type-safe validation of LLM output before ORM persistence. Use schema class naming (e.g., `RequirementSchema`) to avoid conflict with Django models.

**Reflection:**  
This improves reliability, readability, and alignment with modern Python practices. It also demonstrates familiarity with strongly typed design principles, which transfer well to larger-scale systems and typed languages like Java or TypeScript.

---

#### Multi-Platform Job Board Integration: Model Design Patterns

**Context:**  
The jobs app needed to support multiple job board platforms (Workday, Greenhouse, Lever, etc.) with platform-specific configuration (URLs, API tokens, location filter IDs). Each platform requires different fields, creating a design challenge for storing heterogeneous configuration data without schema pollution.

**Options Considered:**  
1. **JSONField for platform-specific config:**  
   - Single `Company` model with a `platform_config` JSONField storing arbitrary key-value pairs per platform.
2. **Multi-table inheritance:**  
   - Base `Company` model with platform-specific subclasses (`WorkdayCompany`, `GreenhouseCompany`) using Django's multi-table inheritance.
3. **Separate config models with OneToOne relationships:**  
   - Core `Company` model with `platform` field, linked to platform-specific config models (`WorkdayConfig`, `GreenhouseConfig`) via OneToOne foreign keys.
4. **Generic foreign keys (ContentTypes):**  
   - `Company` model with GenericForeignKey to arbitrary platform config models.

**Tradeoffs:**  
- **JSONField:**  
  - ✅ Simple, flexible, easy to add new platforms.
  - ❌ No database-level validation or type safety.
  - ❌ Difficult to query platform-specific fields.
  - ❌ No IDE autocomplete for config fields.
- **Multi-table inheritance:**  
  - ✅ Type-safe with proper field validation.
  - ✅ Clean queries per platform.
  - ❌ Creates separate tables causing JOIN overhead.
  - ❌ Complex cross-platform queries.
  - ❌ Polymorphic retrieval requires careful handling.
- **Separate OneToOne configs:**  
  - ✅ Type-safe with database-level validation.
  - ✅ No NULL fields—each platform has only its required fields.
  - ✅ Clean separation of concerns (core company data vs platform specifics).
  - ✅ Easy to query: `Company.objects.filter(workday_config__isnull=False)`.
  - ✅ IDE autocomplete works (e.g., `company.workday_config.base_url`).
  - ✅ Simple extension—just add new config model for new platform.
  - ❌ Slightly more models in schema (minimal complexity).
- **Generic foreign keys:**  
  - ✅ Maximum flexibility.
  - ❌ Loses referential integrity.
  - ❌ Complex, harder to understand and maintain.
  - ❌ Poor query performance.

**Decision:**  
Adopt **separate config models with OneToOne relationships** (Option 3). Each platform has a dedicated config model (e.g., `WorkdayConfig`) with a OneToOne relationship to `Company`. The `Company` model includes a `platform` CharField and a factory method `get_job_fetcher()` that instantiates the appropriate client based on platform type.

**Reflection:**  
This design prioritizes maintainability and type safety over schema simplicity. The "more models" concern is negligible—each config model is small, self-contained, and maps directly to a real-world entity (platform-specific configuration). The pattern scales elegantly: adding Greenhouse support requires only creating `GreenhouseConfig` and `GreenhouseClient`, with no changes to existing models or migration risks. The OneToOne relationship provides the right balance of normalization (no NULL fields) and usability (direct attribute access via related_name). This approach also demonstrates understanding of Django's relationship patterns and separation of concerns—skills directly applicable to production systems. The decision exemplifies choosing architectural clarity over premature optimization, recognizing that a few extra lightweight models are far less problematic than type-unsafe JSONFields or complex inheritance hierarchies.

---

### Job Description Processing
Decisions related to parsing and extracting requirements from job descriptions.

---

#### Job Description Preprocessing: Full JD vs Relevant Sections Only

**Context:**  
LLM API calls for parsing job descriptions and generating requirement-based bullets can become costly due to long input texts. Job descriptions often include sections like "About Us," "Benefits," and "Culture," which are **not directly relevant** for extracting requirements or generating bullets.

**Options Considered:**  
1. **Send Full JD:**  
   - Include the entire job description text in the prompt.  
2. **Send Relevant Sections Only:**  
   - Manually or programmatically extract only sections such as "What We're Looking For" or "Requirements."  
   - Optionally use regex-based extraction for common section headers.

**Tradeoffs:**  
- **Full JD:**  
  - ✅ Maximum context; no risk of excluding potentially important information.  
  - ❌ High token usage → higher API cost.  
  - ❌ Longer prompts may slightly increase response time.  
  - ❌ Includes irrelevant information, which could distract the LLM.  
- **Relevant Sections Only:**  
  - ✅ Lower token usage → lower API cost.  
  - ✅ Focused input likely improves parsing accuracy.  
  - ❌ Risk of excluding niche or subtle requirements that appear outside standard sections.  
  - ❌ Regex-based automation may fail on unusual JD formats.

**Decision:**  
For now, manually select relevant sections for each JD when copying/pasting into prompts. Automation via regex or other extraction techniques may be implemented later to reduce manual work, but only if it reliably captures all important requirements.

**Reflection:**  
This approach balances cost reduction with the need for complete, relevant context. Even partial preprocessing can meaningfully reduce input tokens, lowering per-call cost without sacrificing bullet quality. Maintaining a manual workflow initially ensures critical requirements are not accidentally omitted, with automation considered as a future improvement.

---

#### Requirement Extraction Granularity: Explicit vs Implied and Sentence vs Phrase Format

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
  - ✅ Maximum completeness and human readability.  
  - ❌ High token cost and redundancy.  
- **Explicit or Implied + Short Phrases:**  
  - ✅ Compact, token-efficient, and still captures most relevant context.  
  - ❌ Slightly less descriptive output, but negligible information loss for LLM use.  
- **Explicit Only + Short Phrases:**  
  - ✅ Minimal token and call cost; very efficient.  
  - ❌ May omit nuanced or implied requirements that improve match quality.

**Decision:**  
Adopt the **explicit or implied + short phrases** approach for now. This maintains full requirement coverage while reducing token usage. Future iterations may test **explicit-only** extraction if the total requirement count becomes too high.

**Reflection:**  
The "short phrase" change provides a clear, low-risk cost optimization. The "explicit-only" change remains an optional lever for future fine-tuning based on observed performance. Requirement count can be tracked dynamically through model relationships rather than stored directly.

---

#### Prompt Placeholder Substitution: `.replace()` vs String Formatting

**Context:**  
Needed a reliable way to insert job descriptions into LLM prompt templates for the job description parser.

**Options Considered:**  
1. **`.replace()` using a fixed placeholder** (e.g., `{{JOB_DESCRIPTION}}`)  
2. **Python string formatting** (e.g., `.format()` or f-strings with `{JOB_DESCRIPTION}`)

**Tradeoffs:**  
- **`.replace()`:**  
  - ✅ Safe from JSON brace conflicts.  
  - ✅ Predictable behavior.  
  - ✅ Simple to debug.  
  - ❌ Less flexible for multi-placeholder templates.  
- **String formatting:**  
  - ✅ Scalable for multiple variables.  
  - ✅ Clearer intent for dynamic fields.  
  - ❌ Brittle if `{}` appear in JSON or Markdown.  
  - ❌ Risk of `KeyError` or template corruption.

**Decision:**  
Chose **`.replace()`** for stability and simplicity in LLM prompt handling, especially since prompts often include braces for JSON examples.

**Reflection:**  
If future prompts require multiple dynamic fields (e.g., `{COMPANY}`, `{ROLE}`), may revisit string formatting with careful brace escaping or use a templating library like Jinja2 for controlled substitution.

---

### Resume Generation
Decisions related to bullet generation and resume content creation.

---

#### Bullet Generation Strategy: Evolution from Bulk → Per-Requirement → Per-Role Batching

**Context:**  
The resume generation system needed a reliable, scalable, and token-efficient method to generate experience bullets from parsed job descriptions. The approach evolved through multiple iterations as practical limitations emerged.

**Options Considered:**  
1. **Bulk Generation (Initial Approach):**  
   - Pass all requirements for all roles in a single LLM call.  
2. **Per-Requirement + Full State Tracking:**  
   - Generate bullets one requirement at a time, maintaining full state of bullets generated so far.  
   - Input includes all work experience + accumulated bullets.  
   - Track which bullets satisfy which requirements with weighted scoring.  
3. **Per-Role Batching (Final Approach):**  
   - Generate all bullets for a single experience role in one call.  
   - Input includes only that role's work history + sorted requirements.  
   - Use preconfigured max bullets per role and included roles for deterministic filtering.

**Tradeoffs:**  
- **Bulk Generation:**  
  - ✅ Fewest API calls → lowest cost.  
  - ✅ Simplest call structure.  
  - ❌ High risk of irrelevant or excessive bullets.  
  - ❌ Inconsistent bullet counts across runs.  
  - ❌ Harder to track coverage of individual requirements.  
- **Per-Requirement + State:**  
  - ✅ Maximum control over bullets and scoring.  
  - ✅ Can implement dynamic pruning based on weighted scores.  
  - ✅ Consistent results even with older models.  
  - ❌ High complexity (state management, token tracking, pruning logic).  
  - ❌ Likely hits API rate limits for output tokens with many requirements.  
  - ❌ Large token usage per request (input + output).  
  - ❌ Higher API call count → higher cost.  
- **Per-Role Batching:**  
  - ✅ Simple, deterministic pipeline.  
  - ✅ Token-efficient (each call small, under input/output limits).  
  - ✅ Avoids irrelevant bullets and inconsistent totals via preconfigured rules.  
  - ✅ Fewer API calls than per-requirement, no state tracking required.  
  - ✅ Better quality than bulk generation.  
  - ❌ Less granular control over individual requirements (rely on LLM to map requirements to bullets effectively).

**Decision:**  
Adopt **per-role batching** as the production approach. Use preconfigured included roles, max bullets per role, and sorted requirements to maintain quality while avoiding the complexity and token/cost issues of per-requirement generation.

**Reflection:**  
The system evolved from bulk generation (too unpredictable) through per-requirement generation (too complex/expensive) to per-role batching (optimal balance). This iterative refinement prioritized quality and predictability while managing cost and complexity. If future use cases reveal very large JDs, unusually many requirements, or quality issues, the per-requirement + state approach remains available as a more granular fallback, but current testing shows per-role batching meets all production needs.

---

#### Resume Bullet Editability

**Context:**  
The system generates structured resume bullets from LLM outputs and stores them in the `ResumeExperienceBullet` and `ResumeSkillBullet` models. Initially, the assumption was that these LLM-generated bullets would remain final and directly populate the resume output. However, in practice, users often want to reword or exclude certain bullets, making direct output editing insufficiently structured and data-destructive. A design was needed that preserves structured data while allowing flexible, manual control over bullet inclusion and wording.

**Options Considered:**  
1. **Edit Output Directly:**  
   - Users manually edit the rendered output (Markdown/PDF) and re-import or regenerate it as needed.  
2. **Add `exclude` and `override_text` Fields to Bullet Models:**  
   - Introduce structured fields allowing toggling and in-place text overrides.  
3. **Physically Edit/Delete Bullet Records:**  
   - Directly modify or remove bullet entries that are unsatisfactory.

**Tradeoffs:**  
- **Option 1:**  
  - ✅ Simple workflow.  
  - ❌ Breaks the link between structured data and final output.  
  - ❌ Makes auditability and analytics impossible.  
- **Option 2:**  
  - ✅ Maintains full traceability.  
  - ✅ Allows reversible edits.  
  - ✅ Enables analytics on LLM accuracy and user edits.  
  - ❌ Adds minor schema complexity.  
- **Option 3:**  
  - ✅ Keeps data minimal.  
  - ❌ Sacrifices edit history.  
  - ❌ Risks losing insights about LLM-generated versus human-edited content.

**Decision:**  
Adopt **Option 2** by adding `exclude: BooleanField(default=False)` and `override_text: TextField(blank=True, null=True)` to both `ResumeExperienceBullet` and `ResumeSkillBullet` models. Resume generation will include only non-excluded bullets and use `override_text` if present, otherwise defaulting to `text`.

**Reflection:**  
This approach strikes the best balance between structure, flexibility, and future analytics. It allows iterative refinement of resume content without data loss or duplication, supporting both human-in-the-loop workflows and later evaluation of model output quality.

---

### Template & Output Rendering
Decisions related to resume templates and PDF generation.

---

#### Resume Template Technology Stack: Markdown vs HTML + CSS + Jinja + WeasyPrint

**Context:**  
The resume generation system requires templates with both static content (name, contact info, section headers, experience titles) and dynamic content (experience bullets, skills) that changes per job application. Additionally, precise visual formatting is needed: consistent font family (Calibri throughout), varying font sizes (20pt for name, 14pt for section headers, 12pt for experience titles, 11pt for bullets), bold emphasis for headers and titles, and controlled spacing between sections. The system must produce professional PDFs suitable for both ATS parsing and human review.

**Options Considered:**  
1. **Markdown + CSS + md2pdf/markdown-pdf:**  
   - Use Markdown for content structure with Jinja2 for variable substitution.  
   - Apply CSS styling via a Markdown-to-PDF converter.  
2. **HTML + CSS + Jinja + WeasyPrint:**  
   - Use HTML templates with Jinja2 for structure and variable substitution.  
   - Apply CSS for precise typography and layout control.  
   - Use WeasyPrint to render HTML + CSS to PDF.  
3. **DOCX templates (python-docx or docxtpl):**  
   - Use Microsoft Word templates with programmatic field replacement.  
4. **LaTeX templates:**  
   - Use LaTeX for typographically perfect PDFs.

**Tradeoffs:**  
- **Markdown + CSS:**  
  - ✅ Lightweight, human-readable templates.  
  - ✅ Simple syntax for structure.  
  - ❌ Limited typography control (no per-element font sizing).  
  - ❌ Unpredictable spacing behavior.  
  - ❌ Depends on Markdown renderer's CSS support.  
  - ❌ Difficult to achieve pixel-perfect layouts.  
- **HTML + CSS + Jinja + WeasyPrint:**  
  - ✅ Complete control over typography (fonts, sizes, spacing, margins).  
  - ✅ Supports template inheritance (base template for static data, child templates for variations).  
  - ✅ Leverages familiar web technologies (HTML/CSS).  
  - ✅ DRY principle via Jinja2 blocks and inheritance.  
  - ✅ Deterministic PDF rendering.  
  - ❌ Slightly more verbose than Markdown.  
  - ❌ Requires understanding of HTML/CSS.  
- **DOCX templates:**  
  - ✅ Native Word-style formatting.  
  - ✅ Familiar to non-technical users.  
  - ❌ Not human-readable or version-control friendly.  
  - ❌ Harder to diff and review.  
  - ❌ Adds external binary dependencies.  
- **LaTeX:**  
  - ✅ Publication-quality typography.  
  - ❌ Steep learning curve.  
  - ❌ Overkill for business resumes.  
  - ❌ Doesn't demonstrate web-relevant SWE skills.

**Decision:**  
Adopt **HTML + CSS + Jinja2 + WeasyPrint** as the resume template technology stack. Templates will be structured as HTML files with Jinja2 template inheritance (base template for static contact info and structure, child templates for role-specific variations). CSS will handle all visual styling (font family, sizes, bold, spacing). WeasyPrint will render the final HTML + CSS to PDF.

**Reflection:**  
This approach balances functional requirements (precise formatting, dynamic content) with portfolio goals (demonstrating modern SWE practices like templating, separation of concerns, DRY). HTML + CSS provides the control needed for professional resume formatting while remaining maintainable and extensible. Template inheritance eliminates duplication of static content across resume variations. The stack also aligns well with the target role (SWE) by showcasing relevant web technologies and design principles. While Markdown would technically work for basic structure, it cannot reliably deliver the spacing and typography control required for polished, professional output. Future iterations may explore optimizations like CSS minification or caching, but the core stack provides a solid foundation for both immediate needs and long-term scalability.

---

#### Template Granularity: One Template Per Role/Level vs Dynamic Title Injection

**Context:**  
Resume templates need to display different experience roles with appropriate titles and formatting. The question was whether to create dedicated templates for each role/level combination or use fewer generic templates with dynamically injected titles and CSS styling via `TemplateRoleConfig`.

**Options Considered:**  
1. **One Template Per Role/Level (e.g., `swe_ii.html`, `data_engineer_ii.html`):**  
   - Static titles, company names, dates, and CSS formatting baked into each HTML template. `TemplateRoleConfig` only controls which roles to include, their order, and bullet counts.

2. **Dynamic Title Injection via Extended TemplateRoleConfig:**  
   - Fewer generic templates (e.g., `generic_ii.html`) with `TemplateRoleConfig` extended to include title fields. Python rendering logic injects both titles and associated CSS classes at runtime.

**Tradeoffs:**  
- **One Template Per Role/Level:**  
  - ✅ Maintains clean separation of concerns—presentation logic (titles, CSS) lives in templates, not Python code
  - ✅ Zero runtime injection of static content—only dynamic bullets are filled in
  - ✅ Self-documenting file structure—`swe_ii.html` immediately indicates purpose
  - ✅ Simpler rendering logic and easier debugging—can visually inspect exact HTML without running code
  - ✅ Type-safe template selection via deterministic `Job.role + Job.level` lookup
  - ❌ More template files required (though mitigated by Jinja2 inheritance for shared structure)

- **Dynamic Title Injection:**  
  - ✅ Fewer template files to maintain
  - ✅ Potentially more flexible for custom title variations per application
  - ❌ Violates separation of concerns—CSS classes and formatting directives leak into Python rendering logic
  - ❌ Repeats static presentation data across Resume instances for the same role/level
  - ❌ Template naming becomes opaque—must query database to understand what `generic_ii.html` renders
  - ❌ Increases rendering complexity—must handle both bullet injection and title formatting logic
  - ❌ Harder to debug—final HTML must be mentally reconstructed from multiple sources

**Decision:**  
**Maintain one dedicated template per role/level combination.** The cost of additional template files is negligible compared to the architectural benefits of keeping presentation logic (titles, CSS) in templates and data logic (bullets) in models. This approach preserves clean separation of concerns, simplifies rendering, and maintains system debuggability.

**Reflection:**  
This decision reinforces that template proliferation is not inherently problematic when templates serve distinct purposes—especially with inheritance mechanisms like Jinja2. The temptation to "reduce files" through dynamic injection often introduces architectural complexity that outweighs storage savings. Future template variations (A/B testing layouts, level-specific formatting) remain trivial to implement with dedicated templates but would require significant refactoring with dynamic injection.

#### Template Path Validation: TextChoices vs Separate Models vs Free Text

**Context:**  
The `ResumeTemplate` model stores file paths to HTML templates and CSS stylesheets. While flexibility to name files arbitrarily was initially desired, free-text path fields risk typos, invalid paths, and stale references in the database.

**Options Considered:**  
1. **Free-text CharField:**  
   - Allow arbitrary path strings to be entered when creating `ResumeTemplate` instances.  
2. **Separate models (TemplatePath, CssPath):**  
   - Create dedicated models to store valid paths as database records.  
   - Reference these via foreign keys from `ResumeTemplate`.  
3. **TextChoices enums:**  
   - Define `TemplatePath` and `StylePath` TextChoices classes listing all valid paths.  
   - Use as `choices` parameter on `template_path` and `style_path` fields.

**Tradeoffs:**  
- **Free-text CharField:**  
  - ✅ Maximum flexibility for arbitrary naming.  
  - ❌ No validation—typos and invalid paths can be saved.  
  - ❌ Risk of stale/orphaned references.  
  - ❌ Poor admin UX (no dropdown guidance).  
- **Separate models:**  
  - ✅ Avoids code changes when adding new templates/stylesheets.  
  - ✅ Database-enforced referential integrity.  
  - ❌ Overkill for files created in code anyway.  
  - ❌ Still allows invalid paths to be entered (just in a different model).  
  - ❌ Adds schema complexity and indirection.  
- **TextChoices enums:**  
  - ✅ Validation at database and form level—prevents invalid paths.  
  - ✅ Self-documenting—code explicitly lists available templates.  
  - ✅ Clean admin UX with dropdown selectors.  
  - ✅ Type-safe and easy to debug.  
  - ❌ Requires code change when adding new templates (but templates are code artifacts anyway).

**Decision:**  
Adopt **TextChoices enums** (`TemplatePath`, `StylePath`) for path validation. Since templates and stylesheets are code artifacts requiring code changes to create, adding entries to TextChoices is a trivial extension of that workflow and enforces intentionality about available templates.

**Reflection:**  
The "code change required" aspect is a feature, not a bug—it keeps the codebase in sync with filesystem reality. The separate models approach would only make sense for user-uploaded templates or multi-tenant systems, neither of which apply here. TextChoices provides the optimal balance of safety, usability, and maintainability for developer-created template assets.

---

### Application Tracking
Decisions related to job application lifecycle and status management.

---

#### Modeling Application Status as a Separate Entity

**Context:**  
The system needed a way to represent the lifecycle of a job application—including whether it resulted in a callback, rejection, closure, or no response—while maintaining flexibility for tracking event timing, analytics, and future extensions (like interviews or offers). The model also had to allow for easily identifying the *latest* status of any given application.

**Options Considered:**  
1. **Embed a `status` field directly in `Application`:**  
   - Store a simple `CharField` with predefined choices (e.g., rejected, callback, closed).  
   - Quick to implement and easy to query.  
   - However, limits historical tracking and timestamping of status changes.  
2. **Use separate models for each outcome type** (e.g., `Rejection`, `Callback`, `Closure`):  
   - Provides flexibility for each event type to have custom fields.  
   - But leads to repetitive boilerplate, scattered logic, and complex relationships.  
3. **Centralize statuses in a dedicated `ApplicationStatus` model:**  
   - A single model to represent all state transitions.  
   - Allows timestamping each status event (`status_date`).  
   - Keeps the `Application` model clean with a single `status` FK pointing to the latest known status.

**Tradeoffs:**  
- **Embedded status field:**  
  - ✅ Simple implementation.  
  - ✅ Easy to query current status.  
  - ❌ No historical tracking of status changes.  
  - ❌ Cannot timestamp individual transitions.  
- **Separate models per outcome:**  
  - ✅ Flexibility for custom fields per event type.  
  - ❌ Repetitive boilerplate code.  
  - ❌ Scattered logic and complex relationships.  
  - ❌ Harder to maintain and extend.  
- **Centralized `ApplicationStatus` model:**  
  - ✅ Extensible and scalable as new states or events are added.  
  - ✅ Simplifies analytics (e.g., querying all applications with a "callback" state).  
  - ✅ Maintains historical integrity by decoupling state records from the main application entity.  
  - ❌ Slightly more complex to manage (requires updating FK on `Application` when a new `ApplicationStatus` is created).  
  - ❌ Indirect queries (need to traverse relationships to get the most recent status).

**Decision:**  
Adopted a separate **`ApplicationStatus` model** linked via a foreign key to `Application`. The `Application` model maintains a `status` FK pointing to the latest known status, while all historical status changes are preserved as individual `ApplicationStatus` records.

**Reflection:**  
This structure provides an elegant balance between normalization and practical usability. It keeps the system event-driven and analytics-ready without overcomplicating the schema or duplicating logic across models. As future events (like interviews or offers) are introduced, they can seamlessly integrate into this pattern or relate to `ApplicationStatus` entries. The design supports both current operational needs (tracking application outcomes) and future analytical capabilities (measuring time-to-callback, conversion rates, etc.).

---

#### Interview Preparation Data Model: Granular Models vs Markdown Text Fields

**Context:**  
The interview preparation system generates structured content (company context, callback drivers, background narrative, predicted questions, interviewer questions) that users consume as complete documents during interview prep. The question was whether to model this content granularly (separate models for questions, answers, narrative sections) or store it as markdown text in minimal models.

**Options Considered:**  
1. **Granular models with separate Question/Answer objects:**  
   - Create models like `PredictedQuestion`, `InterviewerQuestion`, `BackgroundNarrativeSection`.  
   - Store each question, answer, and narrative component as separate database records.  
2. **Minimal models with markdown text fields:**  
   - `InterviewPreparationBase`: four markdown TextField (formatted_jd, company_context, primary_drivers, background_narrative).  
   - `InterviewPreparation`: two markdown TextField (predicted_questions, interviewer_questions).  
3. **Hybrid approach:**  
   - Separate models for questions (to enable filtering/querying by question type).  
   - Markdown fields for narrative sections.

**Tradeoffs:**  
- **Granular models:**  
  - ✅ Enables querying individual questions or filtering by question type.  
  - ✅ Schema-enforced structure for each component.  
  - ✅ Facilitates analytics on question accuracy or user edits per question.  
  - ❌ High model complexity (6-8 additional models).  
  - ❌ Requires complex ORM queries to reconstruct full prep document.  
  - ❌ Over-engineering for content consumed as complete documents.  
  - ❌ Harder to edit in Django admin (navigate between related objects).  
- **Minimal models with markdown:**  
  - ✅ Simple schema (2 models total).  
  - ✅ Natural consumption pattern—read entire prep doc without joins.  
  - ✅ Easy editing in Django admin (single textarea per section).  
  - ✅ Flexible—markdown allows formatting adjustments without schema changes.  
  - ✅ Matches actual use case (users don't need to query/filter individual questions).  
  - ❌ Cannot query or filter by individual questions.  
  - ❌ Less structured—markdown parsing required for component extraction.  
- **Hybrid approach:**  
  - ✅ Structured questions, flexible narratives.  
  - ❌ Inconsistent design pattern across preparation types.  
  - ❌ Still adds schema complexity without clear benefit (no filtering requirement identified).

**Decision:**  
Adopt **minimal models with markdown text fields**. `InterviewPreparationBase` stores base content (formatted_jd, company_context, primary_drivers, background_narrative) and `InterviewPreparation` stores interview-specific content (predicted_questions, interviewer_questions). All content is markdown-formatted for flexibility and direct consumption.

**Reflection:**  
This decision prioritizes simplicity and alignment with actual usage patterns over speculative querying capabilities. The key insight is recognizing that interview preparation content is consumed holistically (users read entire documents), not queried atomically (no need to filter specific questions). Markdown provides sufficient structure for human readability while maintaining flexibility for future formatting changes. If future requirements emerge for question-level analytics or filtering (e.g., "show me all STAR answers mentioning X technology"), the markdown can be parsed or the schema refactored—but building granular models upfront would be premature optimization. The decision demonstrates restraint in data modeling: not every piece of text content requires its own table.

---

#### Interview Notes Storage: External Documents vs Integrated System Field

**Context:**  
As interviews began occurring, a mechanism was needed to capture and reference freeform notes taken during calls (recruiter screens, technical interviews, etc.). The notes are typically brief, bullet-pointed observations rather than detailed narratives, and are contextually tied to specific interviews that already have associated metadata (company, job, application, stage, date).

**Options Considered:**  
1. **External document system (Google Docs):**  
   - Store notes in separate Google Docs with manual naming/filing structure.
2. **Integrated TextField in Interview model:**  
   - Add a `notes` TextField to the existing `Interview` model for freeform text storage.
3. **Structured fields per note category:**  
   - Add separate fields like `next_steps`, `salary_discussion`, `overall_feel` to `Interview`.

**Tradeoffs:**  
- **External documents:**  
  - ✅ Supports rich formatting (bold, italics, tables).  
  - ❌ Requires redundant metadata specification (company, date, stage already in system).  
  - ❌ Difficult to maintain consistent naming/filing structure.  
  - ❌ High transfer friction—notes rarely migrated from scratch pads to docs.  
  - ❌ Retrieval requires remembering document names or searching drive.  
  - ❌ No integration with application tracking or future analytics.
- **Integrated TextField:**  
  - ✅ Zero redundant context—all metadata already linked via model relationships.  
  - ✅ Low friction workflow—paste from scratch pad directly into admin textarea.  
  - ✅ Self-documenting—navigate Application → Interviews to access notes.  
  - ✅ Enables future analytics (e.g., correlate note patterns with outcomes).  
  - ✅ Matches actual note-taking pattern (brief bullets, not formatted prose).  
  - ❌ No rich text formatting (bold, colors, etc.).
- **Structured fields:**  
  - ✅ Schema-enforced note organization.  
  - ❌ Rigid structure doesn't fit varying note types (recruiter vs technical interviews).  
  - ❌ Over-engineered for simple, variable-length observations.

**Decision:**  
Add a **`notes` TextField** to the `Interview` model. Notes are stored as plain text with natural Markdown-lite conventions (newlines, indentation). The Django admin textarea provides sufficient usability for copy/paste workflows, and all interview context is already available via model relationships.

**Reflection:**  
This decision prioritizes workflow efficiency over formatting capabilities. The key insight is that the *actual* note-taking process uses plain text anyway (Sublime, paper), so rich formatting in the storage layer only adds friction without benefit. By integrating notes directly into the system of record, the solution eliminates naming overhead, reduces transfer friction, and positions interview notes as first-class data for future analytics—all while matching the user's natural workflow.

---

#### Application Detail View: Content Scope and Dynamic Display by Application State

**Context:**  
When designing the application detail view, two key questions emerged: (1) whether to include parsed job requirements alongside job metadata, resume, and interview timeline, and (2) whether the view should dynamically adapt based on application outcome (callback vs rejection). The view serves two distinct workflows: interview preparation (for callbacks) and rejection analysis (for rejections).

**Options Considered:**  
1. **Static view with all sections:**  
   - Show job details, requirements, resume, and interview sections for all applications regardless of state.
2. **Static view excluding requirements:**  
   - Show job details, resume, and interviews only; requirements accessible via admin link.
3. **Dynamic view based on application state:**  
   - For **callbacks**: Show job details, resume, upcoming interviews, and interview history (omit requirements).
   - For **rejections**: Show job details, requirements, and resume (omit interview sections entirely, not just empty states).
   - For **no status/pending**: Show only job details and resume.

**Tradeoffs:**  
- **Static view with all sections:**  
  - ✅ Comprehensive—all information in one place.  
  - ❌ Cluttered—10-20+ requirements create visual noise during interview prep.  
  - ❌ Empty interview cards shown for rejections add no value.  
  - ❌ Not optimized for either workflow.
- **Static view excluding requirements:**  
  - ✅ Clean, focused interface for interview prep.  
  - ✅ Resume serves as requirements reference—bullets address requirements.  
  - ❌ Rejection analysis requires navigation to admin.  
  - ❌ Empty "No interviews" cards still shown for rejections.
- **Dynamic view based on state:**  
  - ✅ Context-optimized—shows exactly what's relevant for each workflow.  
  - ✅ Interview prep (callback): Job → Resume → Interviews (no requirements clutter).  
  - ✅ Rejection analysis (rejected): Job → Requirements → Resume (no empty interview sections).  
  - ✅ Single source of truth—one URL adapts to use case.  
  - ✅ Eliminates all visual noise (no empty cards, no irrelevant sections).  
  - ❌ Slightly more complex template logic (conditional rendering).

**Decision:**  
Implement **dynamic view based on application state**. Use conditional rendering to show:
- **Callbacks:** Job details + Resume + Upcoming Interviews + Interview History (requirements omitted)
- **Rejections:** Job details + Requirements (sorted by relevance) + Resume (interview sections omitted entirely)
- **Pending/No Status:** Job details + Resume only

Requirements are fetched and rendered only when `application.status.state == 'rejected'`. Interview sections are rendered only when `application.status.state == 'callback'`.

**Reflection:**  
This decision demonstrates user-centered design that adapts to workflow context rather than forcing a one-size-fits-all approach. The key insight is recognizing that interview prep and rejection analysis are fundamentally different workflows with different information needs. By the interview stage, requirements are satisfied (resume proves it), making them visual noise. During rejection analysis, requirements become critical for gap identification, while empty interview sections add no value. The slight increase in template complexity (simple conditionals) is vastly outweighed by the improved usability for both workflows. This also avoids the pitfall of showing empty state messages ("No interviews") when the application state inherently precludes interviews—the absence itself is the signal, not something to explicitly display. The dynamic approach maintains a single view implementation (avoiding duplication) while optimizing for distinct use cases, exemplifying the principle that views should adapt to user intent rather than rigidly displaying all available data.

---

#### Interview Outcome Tracking: Single ApplicationStatus vs Separate InterviewProcessStatus

**Context:**  
Applications that result in callbacks proceed through multiple interview stages (recruiter screen, technical rounds, final loop), after which the process concludes with an outcome (offer, rejection, ghosting, or withdrawal). The system already tracked initial application screening outcomes via `ApplicationStatus` (callback/rejected/closed), but needed a way to capture the final result of the interview pipeline without conflicting with callback-rate analytics.

**Options Considered:**  
1. **Extend ApplicationStatus with additional states:**  
   - Add states like "interview_rejected", "interview_ghosted", "offer" to the existing `ApplicationStatus.state` choices.  
2. **Add outcome field to individual Interview records:**  
   - Store outcome (passed/failed/rejected) on each `Interview` record to track stage-by-stage progression.  
3. **Create separate InterviewProcessStatus model:**  
   - Event-driven model (OneToOne with Application) that captures only the final outcome of the entire interview pipeline, independent of individual interview stages.

**Tradeoffs:**  
- **Extend ApplicationStatus:**  
  - ✅ Single status field, simple queries.  
  - ❌ Conflates application screening outcomes with interview outcomes—breaks callback-rate analytics (can't distinguish "got callback" from "rejected after interviews").  
  - ❌ Loses temporal separation between screening and interview phases.  
- **Outcome on Interview records:**  
  - ✅ Granular stage-by-stage tracking.  
  - ❌ Requires updating previous interview outcome to "passed" when creating next stage interview (redundant—progression is already implied by existence of later stages).  
  - ❌ Adds complexity for simple use case—most workflows only care about final outcome, not per-stage results.  
  - ❌ No clean way to query "what was the final interview result?" without traversing all interviews.  
- **Separate InterviewProcessStatus:**  
  - ✅ Preserves ApplicationStatus for resume-driven outcomes (callback rate analytics remain intact).  
  - ✅ Event-driven—only created when final outcome occurs, no intermediate updates required.  
  - ✅ Clean separation between screening phase (ApplicationStatus) and interview phase (InterviewProcessStatus).  
  - ✅ Simple queries for interview-to-offer conversion rates.  
  - ✅ Individual Interview records track stages without needing outcome fields (existence of later stages implies progression).  
  - ❌ Additional model in schema (minimal complexity trade).

**Decision:**  
Adopt **separate `InterviewProcessStatus` model** with OneToOne relationship to `Application`. This model captures only the final outcome of the interview pipeline (offer/rejected/failed/ghosted/withdrew) and is created event-driven when an outcome notification is received. Individual `Interview` records continue tracking stages without outcome fields—progression is implicit.

**Reflection:**  
This design maintains clean separation between application-phase and interview-phase analytics while avoiding redundant state management. The event-driven approach matches the existing `ApplicationStatus` pattern, creating consistency across the tracking system. By recognizing that stage progression is inherently implied by the existence of subsequent `Interview` records, the design avoids unnecessary outcome fields that would require manual updates. The model enables distinct funnel analytics: callback rate (ApplicationStatus), interview-to-offer rate (InterviewProcessStatus), and stage-specific analysis (Interview count by stage)—all without conflating conceptually separate workflow phases.

---

### Analytics & Evaluation
Decisions related to measuring resume quality and tracking application outcomes.

---

#### Post-Generation Resume Analysis: Automated Matching vs Manual Review

**Context:**  
The original system design included an automated post-generation analysis step to:
1. Identify which job requirements were not satisfied by the generated resume (for gap analysis and potential input data improvements)
2. Calculate a match ratio (met requirements / total requirements) for analytics and correlation with callback rates

The intended implementation was `ResumeMatcher`—an LLM-assisted utility that would compare job requirements against generated resume bullets and skills to produce `unmet_requirements` (CSV string) and `match_ratio` (float) fields on the `Resume` model.

Initial approach: Pass requirement keywords and skill keywords to the LLM for simple matching.  
Evolved consideration: Realized this would require passing full requirement text + full resume bullets for reliable evaluation, significantly increasing token usage.

**Options Considered:**  
1. **Automated matching with requirement/skill keywords only:**  
   - Pass extracted requirement keywords (e.g., `["Python", "Go", "Java"]`) and skill keywords from resume.  
   - LLM determines which requirements are met based on keyword presence.  
2. **Automated matching with full context:**  
   - Pass full requirement text + full resume bullets (and potentially dates/context).  
   - LLM makes nuanced determination of whether requirements like "3+ years building backend systems" are satisfied.  
3. **Manual review before generation:**  
   - Carefully read JD before deciding to apply and generating resume.  
   - Identify gaps in input data at that stage.  
4. **Periodic manual spot-checks:**  
   - Occasionally pass full JD + generated resume to a chatbot with manual prompt.  
   - Request gap analysis and improvement suggestions.

**Tradeoffs:**  
- **Automated matching (keywords only):**  
  - ✅ Low token usage.  
  - ✅ Fast and cheap.  
  - ❌ Unreliable—cannot determine if requirements are truly met from keywords alone.  
  - ❌ Cannot handle soft skills, experience duration, or nuanced requirements.  
  - ❌ Likely to produce false positives/negatives.  
- **Automated matching (full context):**  
  - ✅ More reliable evaluation.  
  - ✅ Can handle nuanced requirements.  
  - ❌ High token cost (requires full JD text + full resume bullets).  
  - ❌ LLM determination still subjective—different models/runs may give different answers.  
  - ❌ Cost compounds across multiple applications.  
  - ❌ Diminishing returns—once input data is complete, unmet requirements only reflect genuine lack of experience (not actionable).  
- **Manual review before generation:**  
  - ✅ Zero token cost.  
  - ✅ Already part of workflow (deciding whether to apply).  
  - ✅ Human judgment more reliable for identifying relevant gaps.  
  - ✅ Enables updating input data before generation rather than after.  
  - ❌ No automated analytics.  
  - ❌ Requires careful attention per JD.  
- **Periodic manual spot-checks:**  
  - ✅ Low cost (only occasional).  
  - ✅ Human judgment + LLM assistance for improvement ideas.  
  - ✅ Can be done retroactively since data is persisted.  
  - ❌ Not systematic or automated.

**Decision:**  
**Reject automated post-generation resume analysis** (`ResumeMatcher`, `match_ratio`, `unmet_requirements`). Rely on **manual JD review before generation** as the primary mechanism for identifying input data gaps, with **periodic manual spot-checks** using chatbots for improvement suggestions.

**Reasoning:**  
1. **Token cost not justified:** Even with full context, the evaluation would be expensive and of uncertain value. The gap analysis use case has diminishing returns—eventually all input data will be complete, leaving only unmet requirements for experiences genuinely not possessed.  
2. **LLM inconsistency:** Determining "requirement met" is subjective. Different models or runs might give different answers for the same input, making analytics unreliable.  
3. **Analytics unlikely to yield insights:** Since the system is designed to only apply to jobs where the user feels qualified (to justify API costs), match ratios would cluster at 80-100%. Little variation means little analytical value.  
4. **Manual review is more effective:** Reading JDs carefully before deciding to apply is already necessary and is the optimal time to spot input data gaps—before generation, not after.  
5. **Data is persisted for future backfill:** If a concrete analytical use case emerges later, the system can easily backfill match analysis using custom scripts since all JDs and resumes are stored in the database.  
6. **Premature optimization:** Shipping the core resume generation product and using it in practice will reveal whether post-hoc analysis provides real value. Building it upfront risks wasting effort on unused features.

**Reflection:**  
This decision exemplifies the principle of building for current concrete needs rather than speculative future requirements. The original design assumed automated matching would be valuable, but deeper analysis revealed high cost and low ROI. Manual workflows—already necessary for job selection—provide better gap identification at zero additional cost. The system architecture (persisted data, modular services) enables adding automated analysis later if real-world usage demonstrates a clear need, making this a low-risk deferral rather than a permanent rejection.

### Job Discovery & Aggregation
Decisions related to fetching, filtering, and aggregating job listings from external platforms.

---

#### Workday API Job Fetching: List Accumulation vs Generator Streaming

**Context:**  
The WorkdayClient fetches jobs via paginated API calls (20 jobs per page), requiring iteration through multiple pages until all results are retrieved. The question was whether to accumulate results in a list and return everything at once, or yield results one-by-one using a generator pattern.

**Options Considered:**  
1. **List-based accumulation:**  
   - Append each job to an in-memory list during pagination loop.
   - Return complete list after all pages fetched.
2. **Generator with yield:**  
   - Yield each job individually as pages are fetched.
   - Caller iterates over generator to process jobs incrementally.

**Tradeoffs:**  
- **List-based accumulation:**  
  - ✅ Simple, straightforward implementation.
  - ✅ Enables reporting total count (`len(jobs)`) for stats.
  - ✅ Allows multiple iterations over results (needed for ID tracking and sync).
  - ✅ Atomic operation—fetch completes before sync begins.
  - ✅ Better error handling—partial results don't corrupt database.
  - ❌ Holds all results in memory (though dataset is small: 50-200 jobs ≈ 50-200KB).
- **Generator with yield:**  
  - ✅ Memory-efficient for large datasets.
  - ✅ Enables early termination if desired.
  - ✅ Streams data through processing pipeline.
  - ❌ Cannot report total count without consuming entire generator.
  - ❌ Cannot iterate multiple times—would need to convert to list anyway for ID tracking.
  - ❌ Interleaves fetch and sync operations, complicating error handling.
  - ❌ More complex code with minimal benefit for small datasets.

**Decision:**  
Adopt **list-based accumulation**. The WorkdayClient returns a complete list of job dictionaries after fetching all pages. The small dataset size (typically 50-200 jobs per company) makes memory overhead negligible, while the workflow requires the complete list for stats reporting, ID tracking, and database sync operations.

**Reflection:**  
This decision prioritizes simplicity and workflow requirements over premature optimization. Generators excel with truly large datasets (thousands/millions of records) or when early termination is needed—neither applies here. The sync workflow requires iterating over results multiple times (once for tracking IDs, again for database operations) and reporting stats on completion, both of which conflict with generator semantics. The list-based approach provides clearer separation between fetch and sync phases, simpler error handling, and more straightforward debugging. If future requirements involve processing significantly larger result sets or streaming to external systems, the implementation could be refactored to use generators—but current use cases don't justify that complexity.

#### Job Title Filtering: Broad Exclusions vs Exact Term Matching with Related Variants

**Context:**  
Platform search APIs (Workday, Greenhouse, etc.) do not support exact-match operators or boolean logic, resulting in overly broad results. A search for "Business Analyst" returns unrelated titles like "Senior Software Engineer" or "Propulsion Systems Analyst". Initial design used per-config exclusion lists to filter noise, but the high variability in returned titles (e.g., "Senior Sapphire Systems Architecture & Definitions Engineer" from a "Business Analyst" search) made exclusion lists unwieldy and unreliable.

**Options Considered:**  
1. **Broad search with extensive exclusion rules:**  
   - Single API call per search term with large exclusion lists attempting to filter all unwanted variations.
2. **Boolean exclusion operators (e.g., "senior AND software"):**  
   - Allow combined term exclusions to handle multi-word patterns.
   - Requires parsing exclusion strings and implementing AND/OR logic.
3. **Exact term matching with curated related variants:**  
   - Make a single API call for the primary term.
   - Post-process results to keep only jobs whose title contains the `search_term` or any `related_terms`.
   - Apply exclusions as secondary filter after exact matching.

**Tradeoffs:**  
- **Broad search with extensive exclusions:**  
  - ✅ Fewest API calls.
  - ❌ Exclusion lists grow indefinitely as edge cases discovered.
  - ❌ Cannot reliably handle long multi-word variations.
  - ❌ Reactive approach—continuously adding exclusions rather than proactively curating valid terms.
- **Boolean exclusion operators:**  
  - ✅ Handles complex exclusion patterns.
  - ✅ More expressive than simple term lists.
  - ❌ Still reactive—filtering noise rather than specifying intent.
  - ❌ Adds parsing complexity and potential for operator errors.
  - ❌ Doesn't solve root problem of overly broad API results.
- **Exact term matching with related variants:**  
  - ✅ Proactive—explicitly specify what to include rather than what to exclude.
  - ✅ Exact matching eliminates "Propulsion Engineer" from "Software Engineer" searches.
  - ✅ More maintainable—add variations organically as discovered vs. endless exclusion rules.
  - ✅ Clear intent—"I want Software Engineer and these known variations".
  - ✅ Shared exclusions across related terms (DRY).
  - ❌ Slightly more API calls (one per config, but not per related term).
  - ❌ Requires discovering and adding valid variations manually.

**Decision:**  
Adopt **exact term matching with curated related variants**. Each SearchConfig specifies `search_term` + `related_terms` list. JobFetcherService makes a single API call for the search_term, filters results for exact matches against the search_term and related_terms, then applies exclusion rules as secondary filter. This shifts focus from "exclude noise" to "include known valid variations".

**Reflection:**  
This decision reflects a fundamental shift from reactive filtering (exclude everything unwanted) to proactive curation (fetch only known valid terms). Platform APIs return overly broad results, making exclusion-based approaches unmaintainable. Exact matching eliminates entire categories of noise (e.g., "Propulsion Engineer" never matches "Software Engineer" searches). The slightly higher API overhead is acceptable given typical search counts (5-10 configs × 1 primary term each = 5-10 calls), and exact matching dramatically improves signal-to-noise ratio. Related terms are discovered organically and curated over time, while exclusion rules continue to handle level-based ("Senior", "Staff") and role-specific ("Frontend") filtering.

