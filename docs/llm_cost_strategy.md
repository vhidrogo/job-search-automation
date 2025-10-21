# LLM Cost Strategy

## Purpose
This document defines the cost management and token-optimization strategy for LLM usage within the Job Search Automation system.  
Its goal is to balance **output quality, token efficiency, and operational predictability** across the core LLM-powered services (`JDParser`, `ResumeWriter`, and `ResumeMatcher`).

---

## Overview

The system makes several types of LLM calls that vary in length, purpose, and frequency.  
Without cost controls, token usage can grow exponentially with job complexity or number of requirements.  
This strategy formalizes how cost is monitored, estimated, and optimized.

This document covers:
- The call-types and their relative token profiles.
- Cost-control principles and levers.
- Implementation notes (token estimation, logging, caching).
- Example cost estimates (with assumptions).
- Future directions for more advanced cost-aware orchestration.

---

## Primary Cost Drivers

| Service | Function | Input Size | Frequency | Output Size | Notes |
|----------|-----------|-------------|-------------|--------------|-------|
| **JDParser** | Extracts structured metadata + requirements from JDs | 0.5–2K tokens | Once per JD | 0.5–1K tokens | Most predictable call. |
| **ResumeWriter** | Generates bullets from experience + requirements | 1–3K tokens | Per included role | 0.5–1K tokens | Largest aggregate driver due to per-role batching. |
| **ResumeMatcher** | Evaluates resume–requirement match coverage | 1–2K tokens | Optional, iterative | 0.5–1K tokens | Used selectively during iterative improvements. |

> Notes:
> - Values above are intentionally conservative ranges. Real usage depends on JD length, number of requirements, and per-role experience verbosity.
> - The system favors **many small, predictable calls** (per-role) rather than very large monolithic prompts. This reduces burst token usage and improves failure isolation.

---

## Cost Control Principles

1. **Granular Batching**  
   The system favors **per-role batching** instead of per-requirement calls.  
   This achieves predictable costs, limits token expansion, and avoids exceeding rate or context limits.

2. **Prompt Compression**  
   - Requirements are expressed as **short phrases** instead of full sentences.  
   - Input data (experience, actions, outcomes) is summarized or pruned to essential context.

3. **Model Selection**  
   - Default model: **Claude Sonnet 4.5** (balanced cost vs reasoning quality).  
   - Future support for dynamic model selection: switch to cheaper models (e.g., Claude Haiku) for non-critical parsing or reformatting tasks.

4. **Token Budget Estimation**  
   - Each LLM call estimates token count via `ClaudeClient.count_tokens()` before execution.  
   - Estimated cost = `(input_tokens + output_tokens) * per_token_price`.  
   - Logging of per-call estimates enables future analytics and budget reporting.

5. **Incremental Execution**  
   Each step in the orchestration (parse → generate → evaluate) can run independently, allowing partial workflows for debugging or reruns without unnecessary repeated calls.

6. **Manual Preprocessing**  
   - Early-stage JD parsing and experience selection remain manual to reduce irrelevant input tokens.  
   - Automated JD preprocessing will be introduced cautiously once its reliability matches manual accuracy.

7. **Structured Validation**  
   - All responses validated through Pydantic schemas before persistence.  
   - Prevents wasteful retries caused by malformed or incomplete responses.

---

## Example Cost Breakdown

| Operation | Calls | Avg Tokens (I/O) | Cost (USD)* | Notes |
|------------|--------|------------------|--------------|-------|
| Parse JD (JDParser) | 1 | ~2K | $0.03 | Predictable single call |
| Generate Bullets (ResumeWriter) | 4 roles × 1 call | ~4K per call | ~$0.48 | Main driver |
| Evaluate Match (ResumeMatcher) | 1 | ~2.5K | $0.04 | Optional |
| **Total (per JD)** | ~6 calls | ~18K | **~$0.55** | Average cost per job |

\*Assuming $0.03 per 1K input + output tokens using Claude Sonnet 4.5 rates (as of 2025).

---

## Optimization Levers

| Lever | Type | Effect | Tradeoff |
|--------|------|--------|-----------|
| Reduce requirements (explicit-only) | Cost ↓ | Quality ↓ |
| Use shorter role context | Cost ↓ | May reduce bullet specificity |
| Use cheaper model (Haiku) | Cost ↓ | Reasoning quality ↓ |
| Prune output length | Cost ↓ | May remove nuance |
| Aggregate less relevant roles | Cost ↓ | Missed coverage |
| Partial rerun caching | Cost ↓ | Adds orchestration complexity |

---

## Implementation Notes

### Token Estimation Utility
All LLM client calls wrap around a standard interface:
```python
client.count_tokens(prompt_text)
client.generate(prompt_text, model="claude-sonnet-4-5")
```

The count function is used by the orchestrator to pre-log token usage and dynamically skip or split requests if they approach model limits.

### Token estimation & gating
Wrap LLM calls with a utility that:
1. Assembles prompt.  
2. Calls `client.count_tokens(prompt)` to estimate input tokens.  
3. Estimates expected output tokens (heuristic or fixed cap).  
4. If estimate > safety threshold:
   - either split or reduce context, **or**
   - switch to a cheaper model, **or**
   - abort with a developer-facing warning.

### Logging and Monitoring
- Every LLM call logs:
  - Model used
  - Token estimate and actual usage
  - API cost
  - Duration
  - Validation outcome (pass/fail)
- Logs will later feed into an analytics dashboard for per-job or per-month reporting.

### Logging schema (minimum fields)
- `timestamp`
- `call_type` (JDParser / ResumeWriter.generate_experience_bullets / ResumeWriter.generate_skill_bullets / ResumeMatcher)
- `model`
- `estimated_input_tokens`
- `estimated_output_tokens`
- `actual_input_tokens`
- `actual_output_tokens`
- `cost_estimate_usd`
- `actual_cost_usd` (if available)
- `duration_ms`
- `validation_passed` (bool)

Persist logs in tracker tables, and aggregate daily/weekly for budgeting dashboards.

### Reuse and Caching
Planned future optimizations:
- Cache parsed JDs (keyed by hash of JD text).
- Cache bullets by (experience_role, requirement_set) tuple.
- Cache validation results to skip redundant parsing.

---

## Hybrid & Tiered matching modes (recommended patterns)

- **Keyword mode (default)** — fastest & cheapest. Match using requirement keywords vs resume skill keywords (any-match rule). Use for analytics and base matching.
- **Semantic mode** — uses full requirement text and full resume bullets; higher recall on paraphrased or conceptual matches. Use on-demand or A/B test sets.
- **Hybrid mode** — run keyword mode first; only run semantic checks for requirements flagged as unmet or borderline.

This tiering lets the Orchestrator minimize cost while preserving a path to higher-quality matching where needed.

---

## Future Directions

1. **Dynamic Model Routing:**  
   Assign models by task type and budget threshold (e.g., parsing → Sonnet, bullet generation → Haiku).

2. **Cost-Aware Orchestration:**  
   The Orchestrator can adaptively skip or downscale calls based on estimated cost ceiling.

3. **Analytics Integration:**  
   Extend tracker app to log cost metrics, enabling trend analysis and budget dashboards.

4. **Automated hybrid fallback:**  
   When keyword-only matcher identifies many unmet items, an automated semantic fallback run can be scheduled (async) to reconcile borderline cases.

---

## Summary
The LLM cost strategy formalizes a **controlled, transparent, and measurable** approach to token-based cost management.  
It prioritizes high-quality outputs while maintaining predictable costs through batching, validation, and pre-estimation.
