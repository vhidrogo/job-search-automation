# Tradeoffs Log

## Purpose
This document records significant technical tradeoffs made throughout the project.  
Each entry captures context, options considered, reasoning, and reflections to make design decisions transparent and traceable over time.

Entries should focus on **architectural or system-level choices** — those that:
- Affect maintainability, scalability, or extensibility.
- Influence how components interact or evolve.
- Would be non-trivial to change later.

Minor implementation details (e.g., helper function naming, small API parameter choices) are excluded to keep this log focused on meaningful design reasoning.

## Placeholder Substitution: `.replace()` vs String Formatting

**Context:** Needed a reliable way to insert job descriptions into LLM prompt templates for the job description parser.

**Options Considered:**
1. `.replace()` using a fixed placeholder (e.g., `{{JOB_DESCRIPTION}}`)
2. Python string formatting (e.g., `.format()` or f-strings with `{JOB_DESCRIPTION}`)

**Tradeoffs:**
- `.replace()`: ✅ safe from JSON brace conflicts, ✅ predictable behavior, ✅ simple to debug, ❌ less flexible for multi-placeholder templates  
- String formatting: ✅ scalable for multiple variables, ✅ clearer intent for dynamic fields, ❌ brittle if `{}` appear in JSON or Markdown, ❌ risk of `KeyError` or template corruption

**Decision:** Chose `.replace()` for stability and simplicity in LLM prompt handling, especially since prompts often include braces for JSON examples.

**Reflection:** If future prompts require multiple dynamic fields (e.g., `{COMPANY}`, `{ROLE}`), may revisit string formatting with careful brace escaping or use a templating library like Jinja2 for controlled substitution.

## Requirement-Based Bullet Generation: Per-Requirement LLM Calls vs Bulk Generation

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

## Job Description Preprocessing: Full JD vs Relevant Sections Only

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
