---
name: phase-implement
license: BSD-3-Clause
description: Coordinate implementation phase by delegating tasks and ensuring code
  quality. Use during implementation phase to manage engineer tasks.
category: tooling
date: '2026-03-19'
version: "1.1.0"
mcp_fallback: none
phase: Impl
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/ed1bd4f54fd4aaba446af92c8b3ab9aff2589ae3/skills/phase-implement.history"
history-cleanup-date: "2026-09-20"
---
# Implementation Coordination Skill

## Overview

| Item | Details |
| ------ | --------- |
| Date | N/A |
| Objective | Coordinate implementation phase by breaking down work, delegating to engineers, and maintaining quality standards. |
| Outcome | Operational |

Coordinate implementation phase by breaking down work, delegating to engineers, and maintaining quality standards.

## When to Use

- Starting implementation phase (after Plan completes)
- Running in parallel with Test and Package phases
- Need to delegate implementation tasks
- Managing multiple engineering tasks simultaneously

### Quick Reference

```bash
# Review GitHub issue for implementation tasks
gh issue view <number> --json body --jq '.body'

# Verify code quality
pixi run mojo test -I . tests/
pixi run mojo build -I . <module>
just pre-commit-all

# Check for warnings (zero-warnings policy)
# Any output = fix before committing
```

## Verified Workflow

1. **Review plan specifications** - Understand deliverables and success criteria
2. **Break into tasks** - Create granular implementation work items
3. **Delegate by complexity**:
   - **Senior Engineer**: Complex algorithms, SIMD, memory management
   - **Engineer**: Standard implementations, business logic
   - **Junior Engineer**: Boilerplate, simple helpers, type definitions
4. **Monitor progress** - Check completion status, unblock issues
5. **Code review** - Verify quality, standards, tests, documentation
6. **Complete the task** - Correct relevant failures, use proportionate checks, and report remaining limits

## Delegation Matrix

| Complexity | Task | Engineer |
| ------------ | ------ | ---------- |
| High | Complex algorithms, SIMD optimizations | Senior |
| High | Memory management, ownership patterns | Senior |
| Medium | Standard functions, business logic | Standard |
| Medium | Data structures, operations | Standard |
| Low | Boilerplate, type aliases | Junior |
| Low | Simple helpers, constants | Junior |

## Mojo Implementation Standards

**Function definitions**:

```mojo
# High-performance critical
fn simd_add[dtype: DType](a: Tensor[dtype], b: Tensor[dtype]) -> Tensor[dtype]:
    """SIMD-optimized addition."""
    pass

# Flexible/Python interop
def load_model(path: String) -> PythonObject:
    pass
```

**Memory management**:

```mojo
# Transfer ownership
fn process(owned data: Tensor) -> Tensor:
    return data^

# Read-only access
fn analyze(borrowed data: Tensor):
    pass

# Mutable access (Mojo v0.26.1+)
fn modify(mut data: Tensor):
    pass
```

## Suggested Quality Checks

Select checks for the changed behavior and the repository's current contract:

- [ ] All tests passing
- [ ] Coverage of the changed behavior and applicable repository thresholds
- [ ] Relevant compiler warnings investigated; actual repository warning policy satisfied
- [ ] `pixi run mojo format` applied
- [ ] Docstrings complete
- [ ] Remaining work recorded accurately, without using unrelated TODOs as blockers
- [ ] Performance meets requirements
- [ ] Follows Mojo syntax standards (Mojo v0.26.1+)

## Phase Dependencies

- **Input from**: Plan phase (specifications and deliverables)
- **Parallel with**: Test phase (TDD) and Package phase
- **Precedes**: Cleanup phase (after parallel phases complete)

## Output Location

- **Implementation**: `/shared/<module>/`, `/examples/`, `/tooling/`
- **Documentation**: GitHub issue comments
- **Issue updates**: Track progress, blockers, learnings via `gh issue comment`

## Error Handling

| Blocker | Resolution |
| --------- | ----------- |
| Unclear requirements | Inspect context and resolve routine choices; ask about material ambiguity |
| Performance issues | Consult Performance Specialist |
| Test failures | Debug with Test Specialist |
| Missing dependencies | Update Plan, communicate status |
| Compiler warnings | Investigate affected warnings and follow the current repository policy |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| N/A | Direct approach worked | N/A | Solution was straightforward |
## Results & Parameters

N/A — this skill describes a workflow pattern.

## References

- `CLAUDE.md` - "Mojo Syntax Standards" (current v0.26.1+ patterns)
- `CLAUDE.md` - "Critical Pre-Flight Checklist" (before committing)
- `CLAUDE.md` - "Common Mistakes to Avoid" (64+ test failure learnings)
- `notes/review/mojo-test-failure-learnings.md` - Real implementation patterns

---

**Key Principle**: Implement to make tests pass, not the other way around.
