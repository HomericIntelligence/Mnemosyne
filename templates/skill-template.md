---
name: <skill-name>
description: "<Capability>. Use when <specific trigger>."
category: <category>
date: YYYY-MM-DD
version: "1.0.0"
user-invocable: false
tags: []
---

# Skill Title

<!-- Use [ASD-STE100](../docs/asd-ste100.md) for prose. The headings and table columns
below preserve corpus compatibility. Omit optional detail that adds no decision value.
Prefer generalized advice and task-specific conditions over fixed process gates.
Preserve technical prerequisites and actual authorization boundaries. Explain their
source and protected action when relevant. Avoid permission requests for work already
authorized, and continue useful work when an optional step is unavailable.
Do not rewrite documented software-development principles. -->

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | YYYY-MM-DD |
| **Objective** | What outcome does this skill help achieve? |
| **Outcome** | State the outcome: successful, operational, or deprecated. |

## When to Use

List the conditions in which to use this skill:

- Trigger condition 1
- Trigger condition 2
- Trigger condition 3

## Verified Workflow

### Quick Reference

Give the shortest useful rule or command, with its applicability conditions:

```bash
# Example command
command --flag value
```

### Suggested Approach

Describe the decision criteria, relevant design principles, and techniques that
help reach the outcome. Use ordered steps only when a technical dependency
makes their order useful. Link to notes for supporting detail and explain when
that detail is useful.

Describe how to continue when a suggested step is unavailable. Reserve requests
for input for material ambiguity or missing authorization. Define completion
by the requested outcome and available evidence, not a plan or review stage.

## Failed Attempts

Document each unsuccessful attempt:

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Describe the approach. | Explain the failure. | State what you learned. |
| Attempt 2 | Describe the approach. | Explain the failure. | State what you learned. |

If the evidence records a successful direct attempt with no failures, use:

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| N/A | The direct approach was successful. | N/A | No change was necessary. |

If failure evidence is unavailable, state that limitation in the table instead
of claiming that no failures occurred.

## Results & Parameters

### Configuration

Provide configurations or parameters that users can copy:

```yaml
key: value
nested:
  key: value
```

### Expected Output

Describe the output from a successful operation:

- Output 1
- Output 2
- Output 3

## Verified On

List the projects in which you tested this skill:

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectName | PR #XXX or brief context | If you need more context, add [notes.md](../skills/skill-name.notes.md). |

## References

- [Link to relevant documentation](https://example.com)
- [Link to related skill](related-skill.md)
- [Link to related discussion](https://github.com)
