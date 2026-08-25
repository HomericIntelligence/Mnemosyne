---
name: advise
license: BSD-3-Clause
description: Before work starts, use this skill to search team knowledge. For experiments, unfamiliar errors, or uncertain implementation tasks, use this skill again.
user-invocable: false
---

# /advise

Write all new or changed active technical prose according to the
[Mnemosyne ASD-STE100 writing policy](../../../../../docs/asd-ste100.md).

## Overview

| Item | Details |
| ------ | --------- |
| Date | 2025-12-29 |
| Objective | Search the skill corpus for relevant prior knowledge before work starts |
| Outcome | ✅ Operational |

## When to Use

- Start a new experiment or task.
- Start an uncertain implementation task.
- Debug an unfamiliar error.
- Avoid a repeated mistake.

## Search Priority

1. Search **Failed Attempts** first. These attempts help prevent repeated work.
2. Search for **exact tag matches**. These matches have high relevance.
3. Search **description keywords** for broader matches.
4. When configurations are available, include versions that users can copy.

Write each generated response in ASD-STE100. Before you present an older skill,
rewrite its explanatory text. Preserve exact code, commands, identifiers,
values, quotations, and evidence.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Exact tag search | Searched only exact tag matches | Relevant skills used different tags | Include description keywords |
| Unranked results | Did not prioritize Failed Attempts | Users repeated failed work | Show failures first |
| Vague query | Used a query without context | The search returned irrelevant results | Add specific context |
| Full corpus read | Read every skill file | Large corpora reduced performance | Filter first and read the best matches |
| No parameter snippets | Omitted configurations from the summary | Users had to open each file | Include usable configurations |

## Results & Parameters

This skill describes a workflow pattern. It has no runtime parameters.

## References

- [Athena](https://github.com/HomericIntelligence/Athena) supplies the installed command.
- Read the root `AGENTS.md` file for the current retrieval workflow.
- Read `documentation-patterns` for searchable skill guidance.
