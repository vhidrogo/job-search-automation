Given a job description, resume, primary callback drivers, and interview details, generate interview-specific preparation content.

# Output Format

Return a JSON object with this exact structure:
```json
{
  "predicted_questions": "markdown string",
  "interviewer_questions": "markdown string"
}
```

# Field Specifications

## predicted_questions
Generate 3-5 predicted interview questions with structured STAR responses.

**Selection Criteria:**
- High likelihood given JD and resume
- Directly evaluate Primary Callback Drivers or adjacent risk areas
- Prefer questions that force evidence, tradeoffs, or decision-making
- Calibrate depth/type based on interview stage and focus

**Format (markdown):**
```markdown
### Question 1
[Specific question text]

**Intent being evaluated:** [1 sentence]

**STAR Answer:**

**Situation:** [1-2 sentences max]

**Task:** [1 sentence max]

**Action:** [2-4 sentences with concrete details]

**Result:** [1-2 sentences with metrics/outcomes]

---

### Question 2
[Continue pattern...]
```

**STAR Answer Constraints:**
- Keep each answer 90-120 seconds when spoken
- Limit Situation + Task to 2 sentences combined
- Emphasize impact, decision rationale, relevance to role
- Tie Action and Result explicitly back to Primary Callback Drivers
- Do not invent experiences not in resume
- Results must be concrete (metrics/outcomes/decisions), not responsibilities

## interviewer_questions
Generate 5 strategic questions to ask the interviewer.

**Selection Criteria:**
- Appropriate for interviewer's role and interview stage
- Avoid technical depth with recruiters
- Emphasize scope/expectations/decision-making with hiring managers
- Emphasize system design/tradeoffs/practices in technical interviews

**Objectives:**
- Demonstrate role understanding and seniority calibration
- Surface information affecting success in role
- Avoid generic or self-serving questions

**Format (markdown):**
```markdown
### Question 1
[Specific question text]

**Why this question works:** [1 sentence explaining signal it sends]

---

### Question 2
[Continue pattern...]
```

# Calibration by Interview Type

**Recruiter Screen:**
- Predicted questions: High-level behavioral, motivation, logistics
- Interviewer questions: Role expectations, team structure, process timeline

**Hiring Manager Screen:**
- Predicted questions: Experience depth, decision-making, leadership/ownership
- Interviewer questions: Team challenges, success metrics, collaboration patterns

**Technical Screen:**
- Predicted questions: Technical depth on callback drivers, problem-solving approach
- Interviewer questions: Architecture decisions, tech stack evolution, engineering practices

**Final Loop:**
- Predicted questions: Mix of technical depth, behavioral, culture fit
- Interviewer questions: Long-term vision, growth opportunities, team dynamics

# Inputs

**Job Description:**
{{JOB_DESCRIPTION}}

**Resume:**
{{RESUME}}

**Primary Callback Drivers:**
{{PRIMARY_DRIVERS}}

**Interview Stage:**
{{INTERVIEW_STAGE}}

**Interview Focus:**
{{INTERVIEW_FOCUS}}

**Interviewer Title:**
{{INTERVIEWER_TITLE}}