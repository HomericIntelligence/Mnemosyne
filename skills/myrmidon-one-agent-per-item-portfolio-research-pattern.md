---
name: myrmidon-one-agent-per-item-portfolio-research-pattern
license: BSD-3-Clause
description: "Partition portfolio research by entity when identity confusion or uneven coverage affects results. Choose delegation and batching from task size and host capacity."
category: architecture
date: 2026-05-30
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: [myrmidon, swarm, parallel-agents, l0-commander, one-agent-per-item, portfolio-research, due-diligence, evidence-file-per-item, wave-dispatch, identity-disambiguation]
---

# Myrmidon One-Agent-Per-Item Portfolio Research Pattern

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | Private session date omitted; creation metadata retained above |
| **Objective** | Compare per-item research with multi-item batching when identity confusion affects results |
| **Outcome** | A private research session produced separate evidence files and resolved similarly named entities. Exact portfolio scale, identities, dates, and item-specific findings are omitted. |
| **Verification** | verified-local; no new execution evidence added |

## When to Use

- Independent items with enough research depth to benefit from separate context
- "One document per item" is the natural deliverable (holdings research, contractor invoice audit, paper citation check)
- Items are amenable to identity-disambiguation per-item (e.g. distinguishing similarly-named entities)
- You have previously tried batching (3-4 items/agent) and found lower recall or missed nuances
- Commander synthesis is "read N files, extract verdicts" — not cross-item analysis

**Do NOT use when:**

- Items have cross-item dependencies (e.g., corporate structure where subsidiary classification affects parent)
- A small inventory that is clearer to handle directly in the main context
- Research requires synthesizing relationships *across* items (use a single agent reading all evidence files after per-item agents complete)

## Verified Workflow

### Quick Reference

```
Step 1: Enumerate N independent items → list with item-specific facts injected per prompt
Step 2: Build a per-item prompt when delegation is authorized and useful
         → inject: item name, known identifiers, output file path
         → suggest: write to <dir>/Status_<Item>.md with sufficient independent evidence
Step 3: Choose concurrency from the current host limits; review sequentially if needed
Step 4: Each agent writes to predictable path: <dir>/Status_<Item>.md
Step 5: Commander synthesizes by reading filenames + per-item verdicts
         → no re-prompting agents; just read output files
```

### Per-Item Agent Prompt Template Skeleton

```
You are researching ONE item: <ITEM_NAME>

Known identifiers / disambiguation hints:
  - <ITEM_IDENTIFIER_1>
  - <ITEM_IDENTIFIER_2>

Tasks:
1. Research the requested facts with enough sources to resolve material uncertainty
2. Disambiguate identity if multiple entities share similar names — pick the correct one
3. Write your complete findings to: <OUTPUT_DIR>/Status_<ITEM_SLUG>.md

Suggested output structure (preserve fields consumed by downstream tools):
- ## Summary (2-3 sentences, status verdict)
- ## Evidence (cited sources with dates and remaining uncertainty)
- ## Identity Disambiguation (if needed)
- ## Verdict: [ACTIVE | INACTIVE | UNCERTAIN | INSOLVENT | ACQUIRED]
```

### Wave Dispatch Reference

Use batches within the current host’s available capacity. Assign each item an output
path and track completion. The historical wave layout is omitted because it exposed
private portfolio scale; no particular item count or batch size is required.

### Commander Synthesis Pattern

```python
# After all waves complete, commander reads output files:
for item in items:
    path = f"{output_dir}/Status_{item.slug}.md"
    verdict = extract_verdict_line(path)  # grep for "## Verdict:"
    summary_table.append((item.name, verdict))

# Write master summary from verdict table — no re-prompting agents needed
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Multi-item batching | Assigned several holdings to each research agent | Per-item disambiguation needed a clearer evidence trail for similarly named entities | Per-item focus can help disambiguation; choose granularity from evidence and task size |
| Single-agent complete pass | One agent researching the full private inventory sequentially | Context-window strain; per-item evidence trail lost; early items contaminate later item analysis; agent skips nuanced disambiguation | Parallel per-item agents avoid context bloat and maintain clean evidence trails |
| Dispatch the full inventory in a single wave | Launch all item agents simultaneously | Violates Myrmidon 5-agent-per-wave cap; causes resource exhaustion and agent failures | Respect the active host capacity; the recorded host used a five-agent cap |

## Results & Parameters

The private session supports a reusable decision: per-item focus can help when similar
names, distinct legal entities, and uneven source quality create confusion. Separate
evidence files make the identity decision and remaining uncertainty easier to inspect.
These observations do not establish a universal agent count or token-cost advantage.

### Identity-disambiguation example

Two similarly named entities can operate different businesses. Compare stable
identifiers and source dates before associating a finding with either entity. Keep
uncertain matches explicit instead of accepting the most prominent search result.

### Suggested output parameters

- One stable item identifier and one predictable evidence-file path.
- Sources sufficient for the requested claim, with dates and uncertainty.
- An explicit identity match and a concise disposition.
- Host-appropriate concurrency, or sequential review where that works better.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private project (identity withheld) | Per-item research comparison; session date and exact scale withheld | Local execution supported per-item evidence tracking and identity disambiguation; no public provenance is claimed |

## References

- [parallel-agent-research-and-swarm-orchestration.md](parallel-agent-research-and-swarm-orchestration.md) — General Myrmidon swarm orchestration pattern (wave limits, agent tiers, L0 commander)
- [swarm-agent-status-misread-as-premature-exit.md](swarm-agent-status-misread-as-premature-exit.md) — Handling agent status misreads during wave execution
