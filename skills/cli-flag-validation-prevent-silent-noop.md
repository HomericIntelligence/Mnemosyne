---
name: cli-flag-validation-prevent-silent-noop
description: "CLI flag validation at parse time to prevent silent no-ops. When a flag value is incompatible with the selected backend (e.g., --approval with --agent=claude), reject it at parse time with a clear error message describing the constraint from the backend's perspective. Use when: (1) designing CLI tools that support multiple backends with different feature sets, (2) discovering that a flag value silently no-ops for one backend but not another, (3) operators pass incompatible flag combinations without realizing they're being ignored."
category: tooling
date: 2026-06-05
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - argparse
  - cli
  - flag-validation
  - silent-no-op
  - agent
  - backend-compatibility
---

# CLI Flag Validation - Prevent Silent No-Op

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-05 |
| **Objective** | Prevent operators from passing flag values that silently no-op for a selected agent/backend. Flag incompatibilities must be caught at parse time with a clear error message describing which backend honors the flag, not which one doesn't. |
| **Outcome** | Solution implemented in ProjectHephaestus issue #773: `validate_agent_flags()` at parse time in `main()` rejects incompatible flag values for --agent=claude before any operations run. All tests pass (verified-local); CI validation pending. |
| **Verification** | verified-local - Unit tests verify all rejection cases + regression guard for valid combinations like --sandbox=read-only |

## When to Use

Trigger phrases that should route to this skill:

- "Operator passed --flag with --agent=claude but the flag silently no-ops"
- "Flag value works with agent X but not agent Y"
- "Prevent silent failure of incompatible flags"
- "CLI tool with multiple backends and different feature sets"
- "Designing an agent/backend selection CLI"
- "Flag validation at parse time"
- "Silent no-op flag combinations"

Situations:

- Building or maintaining a CLI that supports multiple agents/backends (e.g., claude vs codex)
- Discovering via testing or operator complaints that certain flag values work for one backend but silently ignored for another
- Wanting to fail fast with a clear error instead of silently accepting incompatible combinations
- Refactoring a CLI to add backend selection and need to handle per-backend constraints

## Verified Workflow

> Apply this pattern when you discover a flag value that is incompatible with one or more agents. Validate at parse time in main() to prevent the silent no-op.

### Quick Reference

**Data structure** (module-level, per-agent tuple of tuples):

```python
# Flag values that silently no-op when --agent=claude is selected.
# Structure: (args_attr_name, cli_flag_name, frozenset_of_noop_values)
_CLAUDE_NOOP_VALUES: tuple[tuple[str, str, frozenset[str]], ...] = (
    ("approval", "--approval", frozenset({"untrusted", "on-request"})),
    ("sandbox", "--sandbox", frozenset({"danger-full-access"})),
)
```

**Validation function** (call in main() after parse_args but before operations):

```python
def validate_agent_flags(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """Reject flag values that the selected agent does not honor.

    Only fires when the operator EXPLICITLY passed --agent=<backend>.
    When --agent is omitted, resolve_agent() will auto-detect at run time.
    """
    if args.agent != "claude":
        return
    offending: list[str] = []
    for attr, flag, noop_values in _CLAUDE_NOOP_VALUES:
        value = getattr(args, attr)
        if value in noop_values:
            offending.append(f"{flag}={value}")
    if offending:
        parser.error(
            "--agent=claude does not honor "
            + ", ".join(offending)
            + " (these flag values only apply to --agent=codex)"
        )
```

**Call in main()**:

```python
def main(argv: list[str] | None = None) -> int:
    """Run the agent stage command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_agent_flags(parser, args)  # <-- Validate BEFORE operations
    exit_code = run_agent(args)
    if args.json:
        emit_json_status(exit_code, ...)
    return exit_code
```

### Detailed Steps

1. **Identify incompatible flag values by agent.**
   When testing or reviewing the CLI tool, discover which flag values work for which backends. Document them:
   - `--approval=untrusted`: only works for agent=codex; silently no-op for agent=claude
   - `--approval=on-request`: only works for agent=codex; silently no-op for agent=claude
   - `--sandbox=danger-full-access`: only works for agent=codex; agent=claude has no notion of "danger-full-access"
   - `--sandbox=read-only`: WORKS for agent=claude (run_claude_text:125 gates --permission-mode on it); NOT a no-op

2. **Use a data-driven approach with per-flag frozensets.**
   Do NOT use flat conditionals like:
   ```python
   if args.agent == "claude" and args.approval != "never":
       parser.error(...)
   ```
   Instead, define a tuple of tuples at module level listing (attribute_name, flag_name, frozenset_of_noop_values).
   This makes it easy to add new agents/backends in the future without rewriting the validation logic:
   - Extend the tuple for each new agent
   - Keep the logic generic and reusable

3. **Describe the constraint from the AGENT'S perspective, not from other agents.**
   **BAD**: "--agent=codex honors --approval (claude does not)"
   **GOOD**: "--agent=claude does not honor --approval (only applies to --agent=codex)"
   Why? When you add agent=grok or agent=sonnet in the future, you don't want to rewrite the error message. The constraint belongs to the agent you're validating, not to all the other agents. The future maintainer only needs to update the claude block, not update the codex/grok/sonnet messages.

4. **Validate at parse time, BEFORE operations run.**
   Call `validate_agent_flags(parser, args)` in `main()` immediately after `parse_args()` but before `run_agent()` or any other function. This ensures:
   - The invalid combination is caught and reported before wasted work
   - The error message mentions the flag name with `--` prefix (familiar to operators)
   - Stack trace points to parse time, not buried in agent execution

5. **Reject ONLY the values that actually no-op, not all non-defaults.**
   **BAD**: Reject `--sandbox=*` because the agent doesn't support sandbox in general.
   **GOOD**: Reject ONLY `--sandbox=danger-full-access`; allow `--sandbox=read-only` because it IS honored.
   This is a regression guard: if you over-restrict, you block valid combinations.

6. **Test all three cases: rejected no-op, allowed valid values, unaffected other agents.**
   ```python
   def test_main_rejects_danger_full_access_sandbox_with_claude_agent(...):
       """--sandbox=danger-full-access silently no-ops on claude; must error."""
       argv = [..., "--agent", "claude", "--sandbox", "danger-full-access"]
       with pytest.raises(SystemExit) as exc:
           agent_stage.main(argv)
       assert "--sandbox=danger-full-access" in capsys.readouterr().err

   def test_main_allows_read_only_sandbox_with_claude_agent(...):
       """--sandbox=read-only IS honored and must NOT be rejected."""
       argv = [..., "--agent", "claude", "--sandbox", "read-only"]
       assert agent_stage.main(argv) == 0  # Success, not error

   def test_main_allows_approval_with_codex_agent(...):
       """Codex honors --approval; validation must not fire for codex."""
       argv = [..., "--agent", "codex", "--approval", "on-request"]
       assert agent_stage.main(argv) == 0  # Success
   ```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Over-restricting all non-default flag values | When discovering --sandbox didn't work with claude, rejected all --sandbox values (not just danger-full-access) | Blocked valid --sandbox=read-only, which IS honored by run_claude_text (runtime.py:125 gates --permission-mode on it). Caused regression that silently broke legitimate use cases. | Only reject the SPECIFIC values that no-op. Use frozensets per flag to enumerate the exact noop values. Verify each value individually in runtime before deciding it's a no-op. |
| Asserting "codex honors X but claude doesn't" in error messages | Error message: "--approval only applies to agent=codex (claude does not honor it)" | When the codebase adds agent=sonnet or agent=grok in the future, the error message becomes inaccurate. Maintainer must rewrite it. The constraint logically belongs to claude, not to codex's capabilities. | Describe constraint from the agent being validated: "--agent=claude does not honor --approval (these flag values only apply to --agent=codex)". This remains maintainable as new backends are added — the claude block doesn't change; you just add new blocks for grok/sonnet. |
| Validating late, inside run_agent() or run_claude_text() | Checked compatibility inside the agent function after significant setup (repo root resolution, file I/O, etc.) | Invalid flag combinations discovered late, after wasted work. Error message buried in stack trace. Operators see a confusing failure deep in the call stack instead of a clear parse-time rejection. | Validate at parse time in main() immediately after parse_args(). Early rejection, clear error, no wasted work. |
| Flat conditional checks without data structure | Validation logic: `if args.agent == "claude" and args.approval != "never": parser.error(...)` | Hard to extend to new backends or flag values. Logic scattered across multiple if-statements. Adding agent=grok requires finding and updating every compatibility check. | Use a tuple-of-tuples data structure per agent listing (attr, flag, noop_values). Loop over it generically. Adding a new agent is a single data entry, not scattered code changes. |

## Results & Parameters

### Implementation Details

**Location**: `hephaestus/automation/agent_stage.py`

**Changes made**:
1. Added module-level `_CLAUDE_NOOP_VALUES` tuple documenting which flag values no-op for claude
2. Implemented `validate_agent_flags(parser, args)` function
3. Called `validate_agent_flags(parser, args)` in `main()` after `parse_args()` but before `run_agent()`

**Test coverage**: 5 new test functions in `tests/unit/automation/test_agent_stage.py`
- `test_main_rejects_approval_flag_with_claude_agent` — rejection of no-op values
- `test_main_rejects_danger_full_access_sandbox_with_claude_agent` — rejection of sandbox no-op value
- `test_main_allows_read_only_sandbox_with_claude_agent` — regression guard for valid --sandbox=read-only
- `test_main_allows_default_flags_with_claude_agent` — defaults must pass
- `test_main_allows_approval_with_codex_agent` — validation must not fire for other agents

### Error message example

When operator runs:
```bash
hephaestus-automation-loop agent_stage --prompt-file p.md --repo-root . --agent claude --approval on-request
```

Output:
```
usage: agent_stage [-h] --prompt-file PROMPT_FILE [--repo-root REPO_ROOT] ...
agent_stage: error: --agent=claude does not honor --approval=on-request (these flag values only apply to --agent=codex)
```

Exit code: 2 (argparse.ArgumentParser.error calls sys.exit(2))

### Verification command

Run unit tests to verify all three cases:

```bash
pixi run pytest tests/unit/automation/test_agent_stage.py::test_main_rejects_approval_flag_with_claude_agent -v
pixi run pytest tests/unit/automation/test_agent_stage.py::test_main_allows_read_only_sandbox_with_claude_agent -v
pixi run pytest tests/unit/automation/test_agent_stage.py::test_main_allows_approval_with_codex_agent -v
```

All tests pass locally.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #773 / Commit 7f24c89 | `hephaestus/automation/agent_stage.py`: `validate_agent_flags()` function added at parse time in `main()`; 5 test functions cover rejection, allowed-values regression guard, and cross-agent compatibility. Verified-local (all unit tests pass; CI validation pending). |
