# Automation Agent Tool Scopes — Hephaestus Verification Notes

## Context

The ProjectHephaestus issue #2369 implementation plan was applied to a disposable
detached worktree at commit `446b0fea` on 2026-08-05. No Hephaestus source changes
were committed or pushed.

The local patch changed:

- `hephaestus/agents/runtime.py`
- `hephaestus/automation/agent_stage.py`
- `tests/unit/agents/test_runtime.py`
- `tests/unit/automation/test_agent_stage.py`

The behavior was checked against the official
[Claude CLI reference](https://code.claude.com/docs/en/cli-usage) and
[custom tools reference](https://code.claude.com/docs/en/agent-sdk/custom-tools).

## Commands and Results

The focused tests were run with coverage disabled because Hephaestus applies its
global `fail-under=83` threshold even to individual test node selectors:

```bash
uv run pytest --no-cov \
  tests/unit/agents/test_runtime.py::test_run_claude_text_read_only_uses_explicit_non_mutating_policy \
  tests/unit/agents/test_runtime.py::test_run_claude_text_read_only_cannot_be_broadened_by_caller_tools \
  tests/unit/agents/test_runtime.py::test_run_claude_text_builds_stage_command \
  tests/unit/automation/test_agent_stage.py::test_run_agent_propagates_claude_read_only_policy_rejection \
  tests/unit/automation/test_agent_stage.py::test_main_allows_enforced_read_only_policy_with_claude_agent \
  -v
```

Observed result: `5 passed in 0.22s`.

```bash
uv run ruff check \
  hephaestus/agents/runtime.py \
  hephaestus/automation/agent_stage.py \
  tests/unit/agents/test_runtime.py \
  tests/unit/automation/test_agent_stage.py

uv run ruff format --check \
  hephaestus/agents/runtime.py \
  hephaestus/automation/agent_stage.py \
  tests/unit/agents/test_runtime.py \
  tests/unit/automation/test_agent_stage.py
```

Observed results: `All checks passed!` and `4 files already formatted`.

## Coverage-Gate Observation

The first focused pytest invocation omitted `--no-cov`. All four selected
assertions passed, but pytest exited nonzero because their aggregate package
coverage was 5.24%, below the repository-wide 83% threshold. This was a test
selection/configuration mismatch rather than a failure of the command policy.
The complete coverage suite and CI remain pending.
