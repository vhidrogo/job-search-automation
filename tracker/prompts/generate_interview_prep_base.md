Given a job description and resume, generate comprehensive base interview preparation content.

# Output Format

Return a JSON object with this exact structure:
```json
{
  "formatted_jd": "markdown string",
  "company_context": "markdown string", 
  "primary_drivers": "markdown string",
  "background_narrative": "markdown string"
}
```

# Field Specifications

## formatted_jd
Format the job description in readable markdown with clear section headers and bullet points where appropriate.

**Bolding Rules:**
- Bold phrases (requirements, responsibilities, qualifications) that directly support Primary Callback Drivers
- Bold phrases that will be referenced in the Targeted Background Narrative
- Use `**text**` markdown syntax for bolding

**Exclusions:**
- Remove benefits, perks, awards, and employer-branding content
- Exclude content that doesn't inform role expectations or product context

## company_context
Summarize only information explicitly present in the job description. Focus on interview-usable context.

Use markdown with these subsections:
```markdown
### What the company does
(1-2 sentences)

### Core product(s) and users

### Stated mission or values relevant to this role

### Why this team exists within the company
```

**Constraints:**
- No marketing language, awards, or generic culture statements
- Focus on: what company builds, who users are, how role contributes

## primary_drivers
Identify 1-3 specific skills/experiences that most likely caused resume to pass screening.

**Selection Criteria:**
- Must appear explicitly in BOTH job description AND resume
- Must be central (not nice-to-have or peripheral)
- Prefer signals that reduce hiring risk or fill hard requirements
- Exclude generic qualifications unless explicitly emphasized in JD

**Format (markdown):**
```markdown
**Signal Name**: 1-2 sentence justification referencing JD + resume

**Signal Name**: 1-2 sentence justification referencing JD + resume
```

## background_narrative
Generate a targeted narrative for interview opening questions (e.g., "Tell me about your background").

**Objectives:**
- Anchor narrative around Primary Callback Drivers
- Present coherent progression toward this role
- Exclude unrelated roles/education unless they support drivers
- Keep concise and interview-ready (60-120 seconds spoken)

**Format (markdown with 3 subsections):**
```markdown
### Opening one-liner
(role-aligned positioning statement)

### Core narrative
(2-3 tightly scoped talking points tied to callback drivers)

### Forward hook
(what you're looking for next in this role, 1-2 sentences)
```

**Constraints:**
- No chronological resume walkthrough
- No generic traits unless explicitly required by JD
- Each talking point should invite natural follow-up questions

# Inputs

**Job Description:**
{{JOB_DESCRIPTION}}

**Resume:**
{{RESUME}}