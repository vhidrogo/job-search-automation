Given a job description, resume and resume source projects generate comprehensive base interview preparation content.

# Output Format

Return a JSON object with this exact structure:
```json
{
  "formatted_jd": "markdown string",
  "company_context": "markdown string", 
  "primary_drivers": "markdown string",
  "background_narrative": "markdown string",
  "resume_defense_prep": "markdown string"
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

## resume_defense_prep
For each resume bullet point, generate a defense strategy that prepares the candidate to speak confidently on any detail.

**Selection Criteria:**
- Focus on bullets most likely to be questioned by technical interviewers
- Prioritize projects with complex technical decisions or impressive scale
- Prioritize bullets that align with Primary Callback Drivers
- Use Resume Projects data as the authoritative source for technical details

**Format (markdown):**
```markdown
### Resume Bullet: "[Exact text from resume]"

**Likely Follow-up Questions:**
1. [Specific technical question about this bullet]
  - Optimal answer
2. [Question about decision-making/tradeoffs]
  - Optimal answer
3. [Question about impact/outcomes]
  - Optimal answer

**How to Defend This Bullet:**

**The Technical Stack:**
- Technologies used: [List from tools in Resume Projects with brief "why chosen" from problem_context]
- Alternatives considered: [Infer from problem_context what wasn't used and why]

**Key Decision Points:**
- Decision 1: [Extract from actions in Resume Projects with rationale]
- Decision 2: [Extract from actions in Resume Projects with rationale]

**If They Drill Deeper, Be Ready to Explain:**
- Architecture: [High-level system design from problem_context and tools]
- Scale: [Specific numbers from outcomes in Resume Projects]
- Challenges: [Extract 1-2 challenges from problem_context and solutions from actions]
- Outcomes: [Use metrics from outcomes in Resume Projects]

**30-Second Elevator Pitch:**
"[Synthesize problem_context, actions, tools, and outcomes into complete, confident explanation]"

---

### Resume Bullet: "[Next bullet]"
[Continue pattern...]
```

# Inputs

**Job Description:**
{{JOB_DESCRIPTION}}

**Resume:**
{{RESUME}}

**Resume Projects:**
{{RESUME_PROJECTS}}