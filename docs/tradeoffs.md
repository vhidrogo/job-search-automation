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
