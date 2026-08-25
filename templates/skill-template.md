---
name: <skill-name>
description: "<When condition one or condition two occurs, use this skill. State the skill purpose.>"
category: <category>
date: YYYY-MM-DD
version: "1.0.0"
user-invocable: false
tags: []
---

# Skill Title

<!-- Use [ASD-STE100](../docs/asd-ste100.md) for all prose. Do not rewrite documented software-development principles. -->

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | YYYY-MM-DD |
| **Objective** | What must this skill do? |
| **Outcome** | State the outcome: successful, operational, or deprecated. |

## When to Use

List the conditions in which to use this skill:

- Trigger condition 1
- Trigger condition 2
- Trigger condition 3

## Verified Workflow

### Quick Reference

Provide commands or steps that users can copy:

```bash
# Example command
command --flag value
```

### Detailed Steps

1. Describe step 1.
2. Describe step 2.
3. Describe step 3.

## Failed Attempts

Document each unsuccessful attempt:

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Describe the approach. | Explain the failure. | State what you learned. |
| Attempt 2 | Describe the approach. | Explain the failure. | State what you learned. |

If no failures occurred, write:

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| N/A | The direct approach was successful. | N/A | No change was necessary. |

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
