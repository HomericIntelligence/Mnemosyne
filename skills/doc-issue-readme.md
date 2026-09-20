---
name: doc-issue-readme
license: BSD-3-Clause
description: "Draft or post issue-specific approach, progress, or completion notes when issue documentation is requested."
category: tooling
date: '2026-03-19'
version: "1.1.0"
---
# Issue Documentation Skill

## Overview

| Item | Details |
| ------ | --------- |
| Date | N/A |
| Objective | Post structured documentation to GitHub issues following ML Odyssey standards. - Starting work on a GitHub issue |
| Outcome | Operational |

Post structured documentation to GitHub issues following ML Odyssey standards.

## When to Use

- Starting work on a GitHub issue
- Documenting implementation approach
- Tracking implementation progress
- Consolidating findings and decisions

### Quick Reference

```bash
# Post documentation to issue
gh issue comment <number> --body "$(cat <<'EOF'
## Issue Documentation

### Objective
[What this issue accomplishes]

### Approach
[Implementation approach]

### Files to Modify
- path/to/file1
- path/to/file2

### Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
EOF
)"
```

## Documentation Format

### Starting Work

```bash
gh issue comment <number> --body "$(cat <<'EOF'
## Implementation Started

**Branch**: `<branch-name>`

### Objective
[1-2 sentence description of what this issue accomplishes]

### Approach
[Brief description of implementation approach]

### Files to Create/Modify
- [ ] `path/to/file1.mojo` - [purpose]
- [ ] `path/to/file2.mojo` - [purpose]

### Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

#
## Results & Parameters

N/A — this skill describes a workflow pattern.

## References
- Related: #[other-issue]
- Design: [link to relevant docs]
EOF
)"
```

### Progress Update

```bash
gh issue comment <number> --body "$(cat <<'EOF'
## Progress Update

### Completed
- [x] Item 1
- [x] Item 2

### In Progress
- [ ] Item 3 (70%)

### Blockers
None / [describe blockers]

### Notes
[Any findings or decisions made]
EOF
)"
```

### Completion Summary

```bash
gh issue comment <number> --body "$(cat <<'EOF'
## Implementation Complete

**PR**: #<pr-number>

### Summary
[What was implemented]

### Files Changed
- `path/to/file1.mojo` - [change description]
- `path/to/file2.mojo` - [change description]

### Testing
- All tests pass
- Coverage: X%

### Verification
- [x] `pixi run test` passes
- [x] `just pre-commit-all` passes
EOF
)"
```

## Verified Workflow

1. **Read issue context**: `gh issue view <number> --comments`
2. **Document the approach**: Use relevant template sections; post when issue updates are within the requested scope
3. **Update as work progresses**: Post progress updates
4. **Summarize on completion**: Post completion summary with PR link

## Documentation Rules

### DO

- Keep issue-specific
- Reference related issues and docs
- Update as work progresses
- Be specific and measurable

### DON'T

- Post overly long updates (split if needed)
- Duplicate content across issues
- Add documentation that does not help the task or its readers
- Forget completion summary

## Common Sections

### Objective

Good: "Implement tensor operations (add, multiply, matmul) with SIMD optimization"
Bad: "Work on tensors"

### Approach

Good: "Use SIMD for vectorized operations, implement lazy evaluation for chain operations"
Bad: "Code stuff"

### Success Criteria

Prefer verifiable outcomes, expressed as checkboxes when useful:

- "All 15 unit tests pass"
- "Coverage > 90%"
- "No new warnings"

## Error Handling

| Issue | Fix |
| ------- | ----- |
| Issue locked | Keep the draft locally and continue independent work; request maintainer help if posting is necessary |
| Rate limited | Use bounded retries or retain a local draft while continuing other work |
| Content too long | Split into multiple comments |
| Missing context | Run `gh issue view <number> --comments` first |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| N/A | Direct approach worked | N/A | Solution was straightforward |
## Results & Parameters

N/A — this skill describes a workflow pattern.

## References

- See `.claude/shared/github-issue-workflow.md` for workflow patterns
- See `gh-read-issue-context` skill for reading issue context
- See `gh-post-issue-update` skill for posting updates
