Given a job description, resume, primary callback drivers, and interview details, generate interview-specific preparation content that ensures the candidate can confidently defend every resume bullet point and technical claim.

# Output Format

Return a JSON object with this exact structure:
```json
{
  "predicted_questions": "markdown string",
  "interviewer_questions": "markdown string",
  "resume_defense_prep": "markdown string",
  "technical_deep_dives": "markdown string"
}
```

# Field Specifications

## predicted_questions
Generate 3-5 predicted interview questions with structured STAR responses.

**Selection Criteria:**
- High likelihood given JD and resume
- Directly evaluate Primary Callback Drivers or adjacent risk areas
- Prefer questions that force evidence, tradeoffs, or decision-making
- Calibrate depth/type based on interview stage, interviewer role, and focus

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

**Answer Structure Tips:**
- Opening: [Direct answer in one sentence]
- Closing: [Tie back to role requirement or callback driver]

**If Asked for More Detail, Be Ready to Explain:**
- [Technical decision 1 and rationale]
- [Technical decision 2 and rationale]
- [Challenge faced and how resolved]

---

### Question 2
[Continue pattern...]
```

**STAR Answer Constraints:**
- Keep each answer 60-90 seconds when spoken
- Limit Situation + Task to 2 sentences combined
- Emphasize impact, decision rationale, relevance to role
- Tie Action and Result explicitly back to Primary Callback Drivers
- Do not invent experiences not in resume
- Results must be concrete (metrics/outcomes/decisions), not responsibilities
- Avoid trailing off - end with a clear conclusion
- Replace filler phrases with purposeful transitions

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
- Show genuine technical curiosity with technical interviewers

**Format (markdown):**
```markdown
### Question 1
[Specific question text]

**Why this question works:** [1 sentence explaining signal it sends]

**Interviewer Calibration:** [Who this is best for: recruiter/HM/technical/team lead]

---

### Question 2
[Continue pattern...]
```

## resume_defense_prep
For each resume bullet point, generate a defense strategy that prepares the candidate to speak confidently on any detail.

**Selection Criteria:**
- Focus on bullets most likely to be questioned by technical interviewers
- Prioritize projects with complex technical decisions or impressive scale
- Include any tailored resume content that needs extra validation

**Format (markdown):**
```markdown
### Resume Bullet: "[Exact text from resume]"

**Likely Follow-up Questions:**
1. [Specific technical question about this bullet]
2. [Question about decision-making/tradeoffs]
3. [Question about impact/outcomes]

**How to Defend This Bullet:**

**The Technical Stack:**
- Technologies used: [List with brief "why chosen"]
- Alternatives considered: [What you didn't use and why]

**Key Decision Points:**
- Decision 1: [What you decided and rationale]
- Decision 2: [What you decided and rationale]

**If They Drill Deeper, Be Ready to Explain:**
- Architecture: [High-level system design]
- Scale: [Specific numbers - users, data volume, throughput]
- Challenges: [1-2 technical challenges and solutions]
- Outcomes: [Specific metrics if available]

**Red Flags to Avoid:**
- [Common mistake candidates make when explaining this]
- [Terminology to use correctly vs incorrectly]

**30-Second Elevator Pitch:**
"[Complete, confident explanation you can deliver smoothly]"

---

### Resume Bullet: "[Next bullet]"
[Continue pattern...]
```

## technical_deep_dives
Based on the resume and job requirements, identify technical concepts the candidate mentioned but should be prepared to explain in depth.

**Selection Criteria:**
- Technologies/patterns mentioned in resume
- Core technologies in job description
- Concepts relevant to interviewer's domain expertise
- Areas where shallow knowledge would be exposed in technical screens

**Format (markdown):**
```markdown
### Deep Dive Topic: [Technology/Concept Name]

**Why This Matters:**
[1-2 sentences on why interviewer will probe this given role requirements]

**What You Need to Know:**
1. **Core Concept:** [Fundamental explanation in simple terms]
2. **How It Works:** [Technical details - architecture, mechanisms]
3. **When to Use It:** [Use cases and tradeoffs]
4. **Common Pitfalls:** [What goes wrong and how to avoid]

**Your Experience With It:**
[2-3 sentences connecting to resume projects]

**Likely Questions:**
- "[Specific technical question]"
  - **Answer:** [Prepared response]
- "[Architecture/design question]"
  - **Answer:** [Prepared response]

**Practice Explanation:**
"[60-second explanation you should be able to deliver smoothly]"

**If You Don't Know Something:**
"[Honest pivot - acknowledge gap and relate to what you do know]"

---

### Deep Dive Topic: [Next concept]
[Continue pattern...]
```

**Priority Topics for Deep Dives:**
1. Any technology mentioned multiple times in resume
2. Core technologies from job description
3. Technologies interviewer specifically works with
4. Foundational concepts for the role

# Calibration by Interview Type

**Recruiter Screen:**
- Predicted questions: High-level behavioral, motivation, logistics
- Interviewer questions: Role expectations, team structure, process timeline
- Resume defense: Focus on impact stories and career progression
- Technical deep dives: Skip or very high-level only

**Hiring Manager Screen:**
- Predicted questions: Experience depth, decision-making, leadership/ownership
- Interviewer questions: Team challenges, success metrics, collaboration patterns, vision
- Resume defense: Focus on decision-making rationale and business impact
- Technical deep dives: Moderate depth on architectural decisions

**Technical Screen:**
- Predicted questions: Technical depth on callback drivers, problem-solving, system design
- Interviewer questions: Architecture decisions, tech stack evolution, engineering practices, team dynamics
- Resume defense: Be ready to defend every technical detail
- Technical deep dives: Deep technical understanding required

**Follow-On Technical Screen:**
- Predicted questions: Drill deeper on areas where confidence was lacking in previous round
- Interviewer questions: Clarifying questions on technical practices and decision-making
- Resume defense: Expect challenges on every technical claim
- Technical deep dives: They are specifically testing technical depth

**Final Loop:**
- Predicted questions: Mix of technical depth, behavioral, culture fit, leadership
- Interviewer questions: Long-term vision, growth opportunities, team dynamics
- Resume defense: Be ready for any bullet point to be questioned
- Technical deep dives: Comprehensive across all resume technologies

# Interviewer-Specific Calibration

**If Interviewer Is:**
- **Recruiter:** Minimize technical jargon, focus on impact and fit
- **Hiring Manager:** Balance technical and business perspectives
- **Team Lead:** Maximum technical depth - they will test fundamentals
- **Peer Engineer:** Collaborative tone, discuss tradeoffs and learn from each other
- **Senior Engineer:** Expect system design and architectural discussions

# Red Flags to Prevent

**Trailing Off:**
- Generate endings for each answer that circle back to impact
- Provide alternative closings to replace weak endings

**Uncertainty on Own Resume:**
- Flag any resume bullets that need extra validation
- Provide technical deep dives for anything candidate might not remember

**Incorrect Terminology:**
- Clarify commonly confused terms
- Provide correct usage examples

**Rambling When Unsure:**
- Provide honest pivot templates for unknown areas
- Teach graceful ways to redirect to known territory

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

**Previous Interview Feedback:**
{{PREVIOUS_FEEDBACK}}

**Specific Technical Gaps to Address:**
{{TECHNICAL_GAPS}}