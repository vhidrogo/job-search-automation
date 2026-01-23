Given a job description, resume, primary callback drivers, and interview details, generate interview-specific preparation content that ensures the candidate can confidently defend every resume bullet point and technical claim.

# Output Format

Return a JSON object with this exact structure:
```json
{
  "prep_plan": "markdown string",
  "predicted_questions": "markdown string",
  "interviewer_questions": "markdown string",
  "resume_defense_prep": "markdown string",
  "technical_deep_dives": "markdown string"
}
```

# Field Specifications

## prep_plan
Generate a sequential, prioritized preparation roadmap that the candidate can work through at their own pace.

**Selection Criteria:**
- Order tasks by logical prerequisites (understand before practice, practice before polish)
- Prioritize gaps identified in Prior Interview Notes
- Calibrate depth and focus based on Interview Stage and Focus
- Include both consumption (review/study) and production (practice/drill) activities
- Balance time investment with impact on interview performance

**Format (markdown):**
```markdown
## Preparation Roadmap

### Phase 1: Foundation Review (Do First)
**Goal:** Build confident baseline understanding before practicing

1. **Review Generated Interview Prep Materials**
   - Read through all predicted questions and STAR answers
   - Study resume defense prep for all bullets
   - [If Prior Interview Notes exist: Flag weak areas from prior round for extra attention]
   - **Why this order:** Need to know what you're preparing for before drilling specifics

2. **Study Technical Deep Dives**
   - Focus order: [List topics in priority order based on callback drivers and Prior Interview Notes]
   - [If Prior Interview Notes show gaps: "PRIORITY: Review [specific topic] - you struggled with this when asked about [specific question]"]
   - **Why this order:** Conceptual understanding enables better code/design practice

3. **[Interview Focus-Specific Study]**
   - [For coding: "Review [specific algorithms/patterns] relevant to [job requirements]"]
   - [For system design: "Study [specific architectural patterns] used in [domain]"]
   - [For behavioral: "Re-read STAR method and your prepared stories"]
   - [For case: "Review business case frameworks and practice reading/evaluating code"]
   - **Why this order:** Interview-specific preparation should build on general foundation

---

### Phase 2: Active Practice (Do Second)
**Goal:** Convert knowledge into confident execution under pressure

4. **[Interview Focus Practice Activity 1]**
   - [For coding: "Practice 2-3 problems on [specific platform from job/recruiter materials] to familiarize yourself with the environment"]
   - [For system design: "Whiteboard 2-3 [system type relevant to role] architectures on paper, explaining trade-offs aloud"]
   - [For behavioral: "Record yourself answering 3-5 predicted questions using STAR method"]
   - [For case: "Practice reading code + making business recommendations on [topic]"]
   - **Practice focus:** [Specific skill this develops]
   - [If Prior Interview Notes: "Focus on [specific scenario] since you were uncertain about [concept] last time"]

5. **[Interview Focus Practice Activity 2]**
   - [For coding: "Build 2-3 end-to-end [type of system/project relevant to role] using [primary languages from job description]"]
   - [For system design: "Practice explaining [key technical tradeoffs from job requirements] with concrete examples from your experience"]
   - [For behavioral: "Practice your 30-second elevator pitches for each resume bullet"]
   - [For case: "Work through sample case with code evaluation + business recommendation"]
   - **Practice focus:** [Specific skill this develops]

6. **Resume Defense Dry Run**
   - Pick 3-5 most technical bullets
   - Explain each one aloud as if interviewer asked "tell me about this"
   - Practice the 30-second elevator pitch for each
   - [If Prior Interview Notes: "Especially practice [specific bullet] - your explanation last time lacked [specific detail]"]
   - **Why this order:** Confidence on resume is foundational to entire interview

---

### Phase 3: Polish & Integration (Do Third)
**Goal:** Smooth rough edges and build interview-day confidence

7. **Mock Interview Yourself**
   - Answer all predicted questions aloud, timing yourself (60-90 seconds each)
   - Identify where you trail off or sound uncertain
   - Revise weak answers and re-record
   - **Why this order:** Reveals gaps that reading alone doesn't expose

8. **Prepare Your Questions for Interviewer**
   - Select 2-3 questions from generated list appropriate for this interviewer
   - [If Prior Interview Notes: "Avoid repeating [questions already asked], focus on [new angles]"]
   - Practice asking them naturally, not reading from notes
   - **Why this order:** Questions should feel organic after you've internalized the prep

9. **Technical Environment Prep**
   - [If using CodeSignal: "Log into CodeSignal, verify you can access it, test screen sharing"]
   - [If virtual: "Test webcam, microphone, screen share, backup internet plan"]
   - Have resume and notes open for quick reference
   - **Why this order:** Technical issues on interview day kill confidence - eliminate risk now

---

### Phase 4: Final Confidence Check (Do Last, Ideally Day Before)
**Goal:** Quick validation that you're ready, targeted fixes only

10. **Speed Review**
    - Skim all generated materials one more time
    - [If Prior Interview Notes: "Double-check you can now confidently answer [specific question that caused difficulty]"]
    - Practice the 3 most likely questions one final time
    - **Why this order:** Light refresh to keep content top of mind without over-studying

11. **Mental Prep**
    - Review Primary Callback Drivers - remind yourself why they wanted you
    - [If Prior Interview Notes: "Reflect on what went well last time: [specific strengths]"]
    - Trust your preparation
    - **Why this order:** Confidence is the final ingredient

---

## Minimum Viable Prep (If Time-Constrained)
If you can't complete all phases, prioritize in this order:
1. **Must do:** Steps 1, 2, 6 (understand materials, know your resume)
2. **Should do:** Steps 4, 7 (practice the interview focus area, mock yourself)
3. **Nice to have:** Steps 3, 5, 8-11 (polish and environment prep)

[If Prior Interview Notes exist with identified gaps:]
**CRITICAL for this round:** Steps 2 and 4 - you must address [specific technical gap] or it will be exposed again
```

**Calibration by Interview Focus:**

**Coding Focus:**
- Phase 2 emphasizes live coding practice in actual environment (CodeSignal)
- Include specific algorithm/data structure review based on job requirements
- Practice talking through code while writing it

**System Design Focus:**
- Phase 2 emphasizes whiteboarding and explaining trade-offs aloud
- Include architecture pattern review for relevant domain
- Practice drawing schemas and data flow diagrams

**Behavioral Focus:**
- Phase 2 emphasizes STAR method practice and storytelling
- Include recording yourself to catch filler words and trailing off
- Practice smooth transitions between situation/action/result

**Case Focus:**
- Phase 2 emphasizes code reading + business analysis integration
- Include business framework review (profitability, market sizing, etc.)
- Practice making recommendations that balance technical and business factors

**Prior Interview Notes Integration:**
- Flag specific steps with "PRIORITY" when they address known gaps
- Reference specific questions/topics that caused difficulty
- Provide corrected explanations in context of practice activities
- Adjust minimum viable prep to always include gap remediation

## predicted_questions
Generate 3-5 predicted interview questions with structured STAR responses.

**Selection Criteria:**
- High likelihood given JD and resume
- Directly evaluate Primary Callback Drivers or adjacent risk areas
- Prefer questions that force evidence, tradeoffs, or decision-making
- Calibrate depth/type based on interview stage, interviewer role, and focus
- Reference Prior Interview Notes to identify areas where confidence was lacking
- Use Resume Projects data for authentic details in STAR responses

**Format (markdown):**
```markdown
### Question 1
[Specific question text]

**Intent being evaluated:** [1 sentence]

**STAR Answer:**

**Situation:** [1-2 sentences max - use problem_context from Resume Projects]

**Task:** [1 sentence max]

**Action:** [2-4 sentences with concrete details - draw from actions and tools in Resume Projects]

**Result:** [1-2 sentences with metrics/outcomes - use outcomes from Resume Projects]

**Answer Structure Tips:**
- Opening: [Direct answer in one sentence]
- Closing: [Tie back to role requirement or callback driver]

**If Asked for More Detail, Be Ready to Explain:**
- [Technical decision 1 and rationale - reference tools from Resume Projects]
- [Technical decision 2 and rationale]
- [Challenge faced and how resolved - use problem_context]

---

### Question 2
[Continue pattern...]
```

**STAR Answer Constraints:**
- Keep each answer 60-90 seconds when spoken
- Limit Situation + Task to 2 sentences combined
- Emphasize impact, decision rationale, relevance to role
- Tie Action and Result explicitly back to Primary Callback Drivers
- Use authentic details from Resume Projects data - do not invent experiences
- Results must be concrete (metrics/outcomes/decisions), not responsibilities
- Avoid trailing off - end with a clear conclusion
- Replace filler phrases with purposeful transitions
- If Prior Interview Notes indicate uncertainty on a topic, provide extra preparation for related questions

## interviewer_questions
Generate 5 strategic questions to ask the interviewer.

**Selection Criteria:**
- Appropriate for interviewer's role and interview stage
- Avoid technical depth with recruiters
- Emphasize scope/expectations/decision-making with hiring managers
- Emphasize system design/tradeoffs/practices in technical interviews
- Reference Prior Interview Notes to avoid repeating previously asked questions
- Address any gaps or concerns identified in prior rounds

**Objectives:**
- Demonstrate role understanding and seniority calibration
- Surface information affecting success in role
- Avoid generic or self-serving questions
- Show genuine technical curiosity with technical interviewers
- Show learning from previous interview if applicable

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
- Prioritize bullets that align with Primary Callback Drivers
- Reference Prior Interview Notes to identify which bullets were questioned or caused uncertainty
- Use Resume Projects data as the authoritative source for technical details

**Format (markdown):**
```markdown
### Resume Bullet: "[Exact text from resume]"

**Likely Follow-up Questions:**
1. [Specific technical question about this bullet]
2. [Question about decision-making/tradeoffs]
3. [Question about impact/outcomes]
4. [If Prior Interview Notes indicate this bullet was discussed, include: "They already asked about X - be ready for deeper follow-up on Y"]

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

**Red Flags to Avoid:**
- [Based on Prior Interview Notes, identify mistakes made when explaining similar topics]
- [Common terminology mistakes - e.g., if Prior Interview Notes show "mentioned atomicity uncertainly", flag this]

**30-Second Elevator Pitch:**
"[Synthesize problem_context, actions, tools, and outcomes into complete, confident explanation]"

**Prior Interview Performance:**
[If this bullet was discussed in Prior Interview Notes, summarize how it went and what to improve]

---

### Resume Bullet: "[Next bullet]"
[Continue pattern...]
```

## technical_deep_dives
Based on the resume and job requirements, identify technical concepts the candidate mentioned but should be prepared to explain in depth.

**Selection Criteria:**
- Technologies/patterns mentioned in resume or Resume Projects
- Core technologies in job description
- Concepts relevant to interviewer's domain expertise
- Areas where shallow knowledge would be exposed in technical screens
- **CRITICAL:** Prioritize topics from Prior Interview Notes where candidate showed uncertainty or gaps
- Technologies in tools field of Resume Projects that candidate should know deeply

**Format (markdown):**
```markdown
### Deep Dive Topic: [Technology/Concept Name]

**Why This Matters:**
[1-2 sentences on why interviewer will probe this given role requirements]
[If from Prior Interview Notes: "You struggled with this in the last interview when asked about X"]

**What You Need to Know:**
1. **Core Concept:** [Fundamental explanation in simple terms]
2. **How It Works:** [Technical details - architecture, mechanisms]
3. **When to Use It:** [Use cases and tradeoffs]
4. **Common Pitfalls:** [What goes wrong and how to avoid]

**Your Experience With It:**
[Reference specific usage from Resume Projects - cite problem_context, actions, and tools]

**Likely Questions:**
- "[Specific technical question - if from Prior Interview Notes, use actual question asked]"
  - **Answer:** [Prepared response using Resume Projects details]
- "[Architecture/design question]"
  - **Answer:** [Prepared response]

**Practice Explanation:**
"[60-second explanation using authentic details from Resume Projects]"

**If You Don't Know Something:**
"[Honest pivot - acknowledge gap and relate to what you do know from Resume Projects]"

**Gap Analysis from Prior Interview:**
[If Prior Interview Notes show weakness here, explicitly call it out: "Last time you said X but should have said Y"]

---

### Deep Dive Topic: [Next concept]
[Continue pattern...]
```

**Priority Topics for Deep Dives:**
1. Any technology from Prior Interview Notes where candidate showed uncertainty
2. Technologies mentioned multiple times across Resume Projects
3. Core technologies from job description
4. Technologies interviewer specifically works with
5. Foundational concepts for the role

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
- Resume defense: Be ready to defend every technical detail using Resume Projects data
- Technical deep dives: Deep technical understanding required

**Follow-On Technical Screen:**
- Predicted questions: Drill deeper on areas where confidence was lacking in previous round - HEAVILY reference Prior Interview Notes
- Interviewer questions: Clarifying questions on technical practices and decision-making
- Resume defense: Expect challenges on every technical claim - use Prior Interview Notes to identify vulnerable areas
- Technical deep dives: MANDATORY - they are specifically testing technical depth on topics from prior round

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

**If Same Interviewers from Prior Round:**
- Acknowledge learning from previous conversation if relevant
- Address any concerns they raised directly
- Demonstrate improved understanding of topics where you were uncertain

# Red Flags to Prevent

**Trailing Off:**
- Generate endings for each answer that circle back to impact
- Provide alternative closings to replace weak endings
- If Prior Interview Notes show this pattern, provide specific alternative endings

**Uncertainty on Own Resume:**
- Flag any resume bullets that need extra validation
- Cross-reference Resume Projects to ensure candidate has authentic details
- Highlight discrepancies between resume bullets and Resume Projects data

**Incorrect Terminology:**
- Clarify commonly confused terms
- If Prior Interview Notes show terminology mistakes, explicitly correct them
- Provide correct usage examples

**Rambling When Unsure:**
- Provide honest pivot templates for unknown areas
- Teach graceful ways to redirect to known territory
- If Prior Interview Notes show rambling on specific topics, provide structured talking points

**Repeating Prior Mistakes:**
- Identify specific errors from Prior Interview Notes
- Provide corrected explanations
- Flag areas where candidate seemed uncertain and needs confidence-building

# Using Resume Projects Data

**Resume Projects Structure:**
Each project contains:
- **problem_context:** Background and challenges - use for STAR Situation
- **actions:** What was done - use for STAR Action and technical decisions
- **tools:** Technologies used - use for technical stack and architecture
- **outcomes:** Results achieved - use for STAR Result and impact metrics

**How to Use Resume Projects:**
1. **For STAR responses:** Map Resume Projects fields directly to STAR components
2. **For technical details:** Reference specific tools and actions when explaining architecture
3. **For authenticity:** Use exact metrics from outcomes, not approximations
4. **For consistency:** Ensure resume defense matches Resume Projects data exactly
5. **For depth:** When Resume Projects provide more detail than resume bullet, use it to prepare for follow-up questions

# Using Prior Interview Notes

**Prior Interview Notes Structure:**
Structured notes from previous interview rounds containing:
- Interviewers and their roles
- Questions asked and candidate responses
- Self-reflection on performance
- Identified strengths and weaknesses
- LLM feedback on gaps

**How to Use Prior Interview Notes:**
1. **Identify weak areas:** Look for self-reflection on poor answers or LLM-identified gaps
2. **Avoid repetition:** Don't suggest questions already asked unless they're drill-down follow-ups
3. **Build on strengths:** Reinforce what went well
4. **Address gaps directly:** Create technical deep dives specifically for concepts candidate struggled with
5. **Provide corrected answers:** When candidate gave wrong/incomplete answer, provide the right one
6. **Anticipate follow-ups:** If interviewer asked about X, expect deeper questions on X in next round

**Follow-On Interview Priority:**
When Prior Interview Notes exist and Interview Stage is another "Technical Screen":
- Technical deep dives section is HIGHEST PRIORITY
- Focus 70% of content on gaps identified in prior round
- Provide explicit "what you said vs what you should have said" corrections
- Generate practice answers for the exact questions that caused difficulty

# Inputs

**Job Description:**
{{JOB_DESCRIPTION}}

**Resume:**
{{RESUME}}

**Resume Projects:**
{{RESUME_PROJECTS}}

**Primary Callback Drivers:**
{{PRIMARY_DRIVERS}}

**Interview Stage:**
{{INTERVIEW_STAGE}}

**Interview Focus:**
{{INTERVIEW_FOCUS}}

**Interviewer Title:**
{{INTERVIEWER_TITLE}}

**Prior Interview(s) Notes:**
{{PRIOR_INTERVIEW_NOTES}}