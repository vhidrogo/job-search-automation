# LLM Cost Strategy

## Purpose
This document defines the cost management and token-optimization strategy for LLM usage within the Job Search Automation system.  
Its goal is to balance **output quality, token efficiency, and operational predictability** across the core LLM-powered services (`JDParser`, `ResumeWriter`, and `InterviewPreparationService`).

---

## Overview

The system makes several types of LLM calls that vary in length, purpose, and frequency.  
Without cost controls, token usage can grow exponentially with job complexity or number of requirements.  
This strategy formalizes how cost is monitored, estimated, and optimized.

This document covers:
- The call-types and their relative token profiles.
- Cost-control principles and levers.
- Implementation notes (token estimation, logging, streaming).
- Example cost estimates (with actual usage data).
- Future directions for more advanced cost-aware orchestration.

---

## Actual Anthropic Pricing (Claude Sonnet 4.5)
- **Input tokens:** $3 / million tokens
- **Output tokens:** $15 / million tokens

---

## Primary Cost Drivers

| Service | Call Type | Avg Input Tokens | Avg Output Tokens | Frequency | Cost per Call | Notes |
|----------|-----------|------------------|-------------------|-------------|---------------|-------|
| **JDParser** | `parse_jd` | 1,455 | 845 | Once per JD | $0.017 | Most predictable call |
| **ResumeWriter** | `resume_bullets` | 3,823 | 171 | Per included role | $0.014 | Main volume driver |
| **ResumeWriter** | `resume_skills` | 842 | 184 | Once per resume | $0.005 | Small, consistent |
| **InterviewPrep** | `generate_interview_prep_base` | 1,802 | 1,532 | Once per interview | $0.028 | Base preparation content |
| **InterviewPrep** | `generate_interview_prep_specific` | 6,190 | 20,574 | Once per interview | $0.402 | Largest single call; specific prep with full context |

> Notes:
> - Values above reflect actual production usage averages from `LlmRequestLog` analytics.
> - Interview preparation calls have highest per-call cost but occur infrequently (~2.6% callback rate = ~13 interviews/year on 500 applications).
> - Resume generation remains the largest aggregate driver due to frequency (per-role batching across many applications).

---

## Cost Control Principles

1. **Granular Batching**  
   The system favors **per-role batching** instead of per-requirement calls for resume generation.  
   This achieves predictable costs, limits token expansion, and avoids exceeding rate or context limits.

2. **Prompt Compression**  
   - Requirements are expressed as **short phrases** instead of full sentences.  
   - Input data (experience, actions, outcomes) is summarized or pruned to essential context.
   - Interview preparation prompts use structured Resume Projects data to avoid verbose bullet text.

3. **Model Selection**  
   - Default model: **Claude Sonnet 4.5** (balanced cost vs reasoning quality).
   - High-stakes workflows (interview preparation) prioritize output quality over marginal cost savings.
   - Future support for dynamic model selection: switch to cheaper models (e.g., Claude Haiku) for non-critical parsing or reformatting tasks.

4. **Streaming for Large Outputs**  
   - Interview preparation requests use streaming (`stream=True`) to handle outputs exceeding 20K tokens.
   - Prevents timeout errors on long-running operations (>10 minutes).
   - Enables processing up to 64K output tokens for comprehensive interview prep documents.

5. **Token Budget Estimation**  
   - Each LLM call estimates token count via `ClaudeClient.count_tokens()` before execution.
   - Estimated cost = `(input_tokens * $0.000003) + (output_tokens * $0.000015)`.
   - Logging of per-call actual usage enables analytics and budget reporting.

6. **Incremental Execution**  
   Each step in the orchestration (parse → generate → evaluate) can run independently, allowing partial workflows for debugging or reruns without unnecessary repeated calls.

7. **Manual Preprocessing**  
   - Early-stage JD parsing and experience selection remain manual to reduce irrelevant input tokens.
   - Automated JD preprocessing introduced cautiously once its reliability matches manual accuracy.

8. **Structured Validation**  
   - All responses validated through Pydantic schemas before persistence.
   - Prevents wasteful retries caused by malformed or incomplete responses.

---

## Example Cost Breakdown

### Per Job Application (Resume Generation)
| Operation | Calls | Avg Input | Avg Output | Cost (USD) | Notes |
|------------|--------|------------|------------|------------|-------|
| Parse JD | 1 | 1,455 | 845 | $0.017 | Predictable single call |
| Generate Bullets | 4 roles | 3,823 each | 171 each | $0.056 | Main driver (4 × $0.014) |
| Generate Skills | 1 | 842 | 184 | $0.005 | Small overhead |
| **Total (per application)** | ~6 calls | ~16,555 | ~1,529 | **~$0.078** | Dominated by bullet generation |

### Per Interview (Interview Preparation)
| Operation | Calls | Avg Input | Avg Output | Cost (USD) | Notes |
|------------|--------|------------|------------|------------|-------|
| Base Prep | 1 | 1,802 | 1,532 | $0.028 | Company context + narrative |
| Specific Prep | 1 | 6,190 | 20,574 | $0.402 | STAR answers + deep dives |
| **Total (per interview)** | 2 calls | ~9,209 | ~6,436 | **~$0.804** | High per-call cost but infrequent |

### Annual Cost Estimates (500 applications, ~13 interviews)
| Workflow | Volume | Cost per Unit | Annual Cost |
|----------|---------|---------------|-------------|
| Resume Generation | 500 apps | $0.078 | **$39.00** |
| Interview Prep | 13 interviews | $0.124 | **$10.45** |
| **Total Annual** | | | **~$49.45** |

> At 2.6% callback rate, interview preparation represents <4% of total LLM costs despite highest per-call expense.

---

## Optimization Levers

| Lever | Type | Effect | Tradeoff |
|--------|------|--------|-----------|
| Reduce requirements (explicit-only) | Cost ↓ | Resume quality ↓ |
| Use shorter role context | Cost ↓ | May reduce bullet specificity |
| Use cheaper model (Haiku) for parsing | Cost ↓ | Reasoning quality ↓ |
| Prune output length | Cost ↓ | May remove nuance |
| Aggregate less relevant roles | Cost ↓ | Missed coverage |
| Use streaming for large outputs | Complexity ↑ | Enables high-quality comprehensive prep |
| Switch interview prep to Haiku | Cost ↓ 67% | Risk missing technical nuances in high-stakes prep |

---

## Implementation Notes

### Token Estimation & Streaming
All LLM client calls wrap around `ClaudeClient` with standard interface:
```python
client.count_tokens(prompt_text)  # Pre-execution estimation
client.generate(prompt_text, model="claude-sonnet-4-5", max_tokens=4000)  # Default non-streaming
client.generate(prompt_text, max_tokens=64000)  # Streaming enabled automatically for large outputs
```

The `ClaudeClient` implementation:
- Uses streaming by default (`messages.stream()`) to handle outputs >20K tokens
- Estimates input tokens via `count_tokens()` before execution
- Logs actual input/output tokens to `LlmRequestLog` in finally block (ensures logging even on errors)
- Supports configurable `max_tokens` per call type

### Logging and Monitoring
Every LLM call logs via `LlmRequestLog`:
- `timestamp`: When call occurred
- `call_type`: One of `CallType` choices (parse_jd, resume_bullets, resume_skills, generate_interview_prep_base, generate_interview_prep_specific)
- `model`: Model identifier (e.g., claude-sonnet-4-5)
- `input_tokens`: Actual input token count
- `output_tokens`: Actual output token count
- Calculated fields: `total_tokens()` method

Analytics queries:
```python
# Average tokens by call type
LlmRequestLog.objects.values('call_type').annotate(
    avg_input=Avg('input_tokens'),
    avg_output=Avg('output_tokens')
)

# Total cost for date range
logs = LlmRequestLog.objects.filter(timestamp__gte=start_date)
total_cost = sum(
    (log.input_tokens * 0.000003) + (log.output_tokens * 0.000015)
    for log in logs
)
```

Future: Extend with duration tracking, validation outcomes, and dashboard visualizations.

### Streaming Implementation
For interview preparation and other high-output workflows:
```python
with self.client.messages.stream(
    model=model,
    max_tokens=max_tokens,
    messages=[{"role": "user", "content": prompt}]
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            chunks.append(event.delta.text)
    
    final_message = stream.get_final_message()
    output_tokens = final_message.usage.output_tokens
```

Streaming prevents timeout errors on operations >10 minutes and enables outputs up to 64K tokens.

### Reuse and Caching
Planned future optimizations:
- Cache parsed JDs (keyed by hash of JD text)
- Cache bullets by (experience_role, requirement_set) tuple
- Cache interview prep base content by company (company_context, background_narrative reusable across interviews)

---

## Future Directions

1. **Dynamic Model Routing:**  
   Assign models by task type and cost sensitivity:
   - Parsing → Sonnet (balanced)
   - Resume bullets → Sonnet (quality critical for callbacks)
   - Interview prep → Sonnet (high-stakes, infrequent)
   - Future candidates for Haiku: reformatting, simple extraction

2. **Cost-Aware Orchestration:**  
   The Orchestrator can adaptively skip or downscale calls based on estimated cost ceiling or apply tiered strategies (quick mode vs comprehensive mode).

3. **Analytics Integration:**  
   Extend tracker app to:
   - Visualize cost trends over time
   - Correlate token usage with application outcomes
   - Identify optimization opportunities via outlier detection

4. **Interview Prep Optimization:**  
   - Cache base prep content (company_context reusable across multiple interviews)
   - Explore partial regeneration (only update specific sections vs full rerun)
   - Consider splitting prep into smaller focused calls if needed

---

## Summary
The LLM cost strategy formalizes a **controlled, transparent, and measurable** approach to token-based cost management.  
It prioritizes high-quality outputs while maintaining predictable costs through batching, validation, streaming, and pre-estimation.

Annual LLM costs remain well under $50 for 500 applications, with interview preparation representing minimal incremental cost despite comprehensive output. The system demonstrates that thoughtful architectural choices (per-role batching, prompt compression, streaming) enable sophisticated LLM workflows at sustainable costs.