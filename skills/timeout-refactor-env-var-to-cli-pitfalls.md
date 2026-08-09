---
name: timeout-refactor-env-var-to-cli-pitfalls
description: "CI and boundary-validation patterns when moving timeout controls into explicit CLI options. Use when: (1) replacing timeout env shims with --*-timeout flags, (2) requiring shared timeout helpers to reject zero and negatives while omission selects defaults, (3) preserving a separate zero-disables timeout contract, (4) keeping exports, Protocols, tests, and worktree tooling aligned."
category: ci-cd
date: 2026-08-06
version: "1.1.0"
user-invocable: false
verification: unverified
history: timeout-refactor-env-var-to-cli-pitfalls.history
tags:
  - timeout
  - refactor
  - env-var
  - cli
  - pytest
  - tmp_path
  - mypy
  - type-ignore
  - attr-defined
  - union-attr
  - barrel-export
  - __all__
  - protocol
  - stub
  - rebase
  - merge-conflict
  - duplicate-definition
  - ruff-f811
  - PYTHONPATH
  - pre-commit
  - ci-fix
  - hephaestus
  - positive-integer
  - zero-semantics
---

# Timeout Refactor: Env-Var to CLI — CI Pitfalls

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 (v1.1.0; originally 2026-06-28) |
| **Objective** | Document timeout CLI migration failures and define explicit positive-domain versus zero-disables contracts for shared timeout options. |
| **Outcome** | The original migration fixes were CI-verified. The v1.1.0 positive-integer hardening is a source-reviewed plan only; it was not implemented or run in this session. |
| **Verification** | unverified for v1.1.0; the v1.0.0 migration workflow remains archived as verified-ci |
| **History** | [changelog](./timeout-refactor-env-var-to-cli-pitfalls.history) |

## When to Use

- Removing env-var timeout shims (`HEPH_PLAN_TIMEOUT`, `HEPH_REVIEW_TIMEOUT`, etc.) and replacing with CLI `--agent-timeout` / `--plan-timeout` args
- Adding new `add_*_timeout_arg` helpers to `cli/utils.py` — always check `cli/__init__.__all__` stays in sync
- Changing a method's default argument type in implementation (e.g., `timeout: int | None` → `timeout: int`) — update the matching Protocol stub too
- Tests verify that env-var X controls behavior Y — after removing the env var, tests must be updated to verify the new fixed-default behavior
- A branch has survived an interactive rebase and now has duplicate function definitions or missing variables
- Pre-commit runs fine on CI but fails locally with `hephaestus-check-*` console script errors
- Shared `--agent-timeout`, `--advise-timeout`, `--poll-max-wait`, `--git-message-timeout`, `--learn-timeout`, or `--follow-up-timeout` helpers currently use bare `type=int` and therefore accept zero or negative values.
- One nearby option intentionally defines zero or negatives as "disabled" and must remain outside a shared strictly-positive parser.

## Verified Workflow

> **Warning:** The v1.1.0 positive-domain subsection is unverified. Treat it as
> a hypothesis until the focused timeout-helper tests and CI pass. The original
> env-var-to-CLI migration and its ten CI fixes were `verified-ci`.

### Quick Reference

```bash
# After a timeout refactor, run this triage checklist in order:

# 1. Verify tmp_path annotations in new tests
grep -rn "TempPathFactory" tests/
# Should be empty; fix to: from pathlib import Path; tmp_path: Path

# 2. Audit new type: ignore codes against mypy's actual error
pixi run mypy hephaestus/ 2>&1 | grep "error:"
# For dict-value attribute access captured["options"].xxx → type: ignore[attr-defined]
# NOT union-attr (that fires when the object itself may be None)

# 3. Check cli/__init__.__all__ covers cli/utils.__all__
python3 - <<'EOF'
import ast, pathlib
utils_src = pathlib.Path("hephaestus/cli/utils.py").read_text()
init_src  = pathlib.Path("hephaestus/cli/__init__.py").read_text()
utils_all = {n for n in ast.literal_eval(
    next(n for n in ast.parse(utils_src).body
         if isinstance(n, ast.Assign) and
            any(t.id == "__all__" for t in n.targets if isinstance(t, ast.Name))
    ).value.elts if isinstance(n, ast.Constant))}
init_all  = {n for n in ast.literal_eval(
    next(n for n in ast.parse(init_src).body
         if isinstance(n, ast.Assign) and
            any(t.id == "__all__" for t in n.targets if isinstance(t, ast.Name))
    ).value.elts if isinstance(n, ast.Constant))}
missing = utils_all - init_all
print("Missing from cli/__init__.__all__:", sorted(missing))
EOF

# 4. Check for duplicate function definitions (post-rebase)
pixi run ruff check hephaestus/ --select F811

# 5. Grep callers of removed timeout functions
grep -rn "planner_claude_timeout\|pr_reviewer_claude_timeout\|learn_claude_timeout" hephaestus/

# 6. Verify Protocol stubs match implementation signatures
pixi run mypy hephaestus/automation/ 2>&1 | grep "arg-type\|override"

# 7. Check tests that asserted env-var timeout behavior
grep -rn "HEPH_AGENT\|HEPH_PLAN\|HEPH_REVIEW" tests/

# 8. Local pre-commit workaround when PYTHONPATH is polluted
env -u PYTHONPATH git commit -S -s -m "fix: ..."
```

### Detailed Steps

#### Proposed hardening — make timeout domains explicit

1. Inventory all shared timeout argument helpers and any intentional disable contracts before introducing a common parser. Do not infer equivalent semantics merely because options contain the word "timeout".
2. Use one private `argparse` type for options whose domain is strictly positive. Omission (`default=None`) selects configured behavior; zero is invalid and must not be overloaded as "use default" or "disable".
3. Append one shared help suffix to every affected flag: "Must be a positive integer; zero does not disable the timeout." This makes the rejection and omission semantics visible in generated help.
4. Keep any explicit zero-disables option on its own parser and normalization path. In ProjectHephaestus, `--phase-timeout` accepts a float and normalizes non-positive values to `None`; it is intentionally not one of the six shared positive timeout helpers.
5. Parameterize the same zero, negative, help-text, positive, omitted-default, and non-integer assertions across every shared helper. A single representative-helper test does not prove the domain is consistently applied.

```python
_POSITIVE_TIMEOUT_HELP = (
    " Must be a positive integer; zero does not disable the timeout."
)

def _positive_int(value: str) -> int:
    """Parse a strictly positive integer."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"expected a positive integer, got {value!r}"
        ) from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError(
            f"expected a positive integer, got {parsed}"
        )
    return parsed
```

#### Fix 1 — `tmp_path` annotation: `Path`, not `TempPathFactory`

pytest's `tmp_path` fixture yields a `pathlib.Path`, not `pytest.TempPathFactory`.
`TempPathFactory` is the *factory* injected by `tmp_path_factory`.

```python
# WRONG — causes mypy arg-type errors
from pytest import TempPathFactory
def test_foo(tmp_path: TempPathFactory) -> None: ...

# CORRECT
from pathlib import Path
def test_foo(tmp_path: Path) -> None: ...
```

Check all new test files: `grep -n "TempPathFactory" tests/`.

#### Fix 2 — Correct `# type: ignore` code for dict-value attribute access

`union-attr` fires when the **object itself** may be `None` or a union.
`attr-defined` fires when the **attribute** doesn't exist on a known type.

Dict lookups (`d["key"]`) return `Any` in non-strict mypy; accessing `.something` on `Any` raises `attr-defined`, not `union-attr`.

```python
# WRONG — wrong ignore code silently passes but mypy --strict re-flags it
result = captured["options"].timeout  # type: ignore[union-attr]

# CORRECT
result = captured["options"].timeout  # type: ignore[attr-defined]
```

#### Fix 3 — `cli/__init__.__all__` must mirror `cli/utils.__all__`

The `test_cli_all_covers_module_all` test fails whenever a name is in `cli/utils.__all__` but missing from `cli/__init__.__all__`. After adding helpers like `add_advise_timeout_arg`, `add_agent_timeout_arg`, `add_learn_timeout_arg`, `add_plan_timeout_arg`, `add_review_timeout_arg`, `add_pr_review_timeout_arg`:

1. Add to `hephaestus/cli/utils.py` `__all__`
2. Add to `hephaestus/cli/__init__.py` `__all__` **and** import list

The CI check that enforces this is `test_cli_all_covers_module_all` in `tests/unit/cli/test_cli_init.py`.

#### Fix 4 — Resolving an in-progress interactive rebase

When `git status` shows `UU` (both-modified) files, the branch is mid-rebase:

```bash
# See which files need resolution
git status | grep "^UU"

# For each conflict, accept the PR branch side (ours during rebase = what was replayed = the PR commit)
git checkout --ours -- hephaestus/automation/implementer.py
git checkout --ours -- hephaestus/automation/planner.py
# ... etc for each conflicted file

git add hephaestus/automation/implementer.py hephaestus/automation/planner.py  # ...
git rebase --continue
```

**Note**: In a rebase, `--ours` is the **replayed commit** (the PR side), `--theirs` is the base branch (main). This is the opposite of merge conflict semantics.

#### Fix 5 — Duplicate definitions after rebase replay (ruff F811)

When the rebase replays a commit that adds `create_validation_parser` and `resolve_repo_root` on top of a base that already had them (merged separately), the functions appear twice, triggering `ruff F811 (redefinition of unused name)`.

```bash
# Find duplicates
pixi run ruff check hephaestus/ --select F811

# Remove the second (redundant) definition block
# Verify function signatures are identical before removing — if different, keep the newer one
```

#### Fix 6 — Update callers after removing timeout helper functions

After removing `planner_claude_timeout()`, `pr_reviewer_claude_timeout()`, `learn_claude_timeout()`:

```bash
# Find all callers
grep -rn "planner_claude_timeout\|pr_reviewer_claude_timeout\|learn_claude_timeout" hephaestus/
```

Replace each call with the appropriate value:

```python
# BEFORE (removed function call)
timeout=planner_claude_timeout()

# AFTER (use fixed default or CLI-supplied value)
timeout=timeout          # when timeout comes from CLI arg
timeout=600              # when a fixed default is appropriate
```

#### Fix 7 — Restore variables lost in conflict resolution

After taking `--ours` for a whole file, check for module-level variables that might have been in the conflict block but not in the PR-side resolution:

```python
# This can be silently dropped if it lived between conflict markers:
_FUTURE_POLL_INTERVAL_SECONDS: float = 1.0
```

Run `pixi run mypy hephaestus/automation/implementer.py` immediately after conflict resolution to catch these.

#### Fix 8 — Protocol stub must match implementation signature

When `Planner._call_claude(timeout: int | None = None)` changes to `timeout: int = 300`, update the `PlannerHost` Protocol stub to match:

```python
# hephaestus/automation/_interfaces.py or similar

# BEFORE — mismatches implementation
class PlannerHost(Protocol):
    def _call_claude(self, ..., timeout: int | None = None) -> str: ...

# AFTER — matches new implementation
class PlannerHost(Protocol):
    def _call_claude(self, ..., timeout: int = 300) -> str: ...
```

mypy error: `Argument "timeout" to "_call_claude" has incompatible type "int"; expected "int | None"` signals this mismatch.

#### Fix 9 — Update tests that asserted env-var timeout behavior

After removing env-var support, tests like `test_omitted_timeout_uses_env_configured_plan_timeout` will fail because the env var no longer has any effect.

```python
# BEFORE — tests env-var behavior (now removed)
def test_omitted_timeout_uses_env_configured_plan_timeout(monkeypatch):
    monkeypatch.setenv("HEPH_PLAN_TIMEOUT", "999")
    result = call_planner(timeout=None)
    assert result.timeout_used == 999  # env var was controlling it

# AFTER — tests fixed-default behavior
def test_omitted_timeout_uses_fixed_default_plan_timeout():
    result = call_planner()
    assert result.timeout_used == 300  # fixed default in implementation
```

Four such tests typically exist for: compact-session/learn timeout, plan timeout, review timeout (direct), review timeout (via reviewer).

#### Fix 10 — PYTHONPATH pollution blocking local pre-commit

When `PYTHONPATH=/home/<user>/<repo>` is set in the shell (e.g., from a `.envrc`), the pre-commit environment resolves console scripts (`hephaestus-check-test-structure`, `hephaestus-check-api-table-docs`) from the **main repo**, not the worktree. CI is unaffected because it does not export `PYTHONPATH`.

```bash
# Option A: Unset for the commit
env -u PYTHONPATH git commit -S -s -m "..."

# Option B: Re-install the package in the worktree's pixi env
# (needed when a NEW console script was added in this PR)
pixi run pip install -e ".[automation]" --no-deps
env -u PYTHONPATH git commit -S -s -m "..."

# Option C: Permanent fix — unset in .envrc or shell profile
unset PYTHONPATH
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| `tmp_path: pytest.TempPathFactory` | Used TempPathFactory annotation for `tmp_path` fixture argument | `tmp_path` yields `pathlib.Path`; `TempPathFactory` is for the `tmp_path_factory` fixture | Always use `from pathlib import Path; tmp_path: Path`; verify with `pixi run mypy` |
| `# type: ignore[union-attr]` on dict subscript | Suppressed `attr-defined` error with wrong ignore code | mypy `--strict` treats wrong codes as errors too; also gives a false sense of correctness | Match the ignore code to mypy's actual reported code; `union-attr` is for `x.attr` where `x: T \| None`; `attr-defined` is for `x.attr` where `x: Any` or `x: SomeDict[str, ...]` |
| Skipping `cli/__init__.__all__` update | Added 6 helpers to `cli/utils.__all__` but forgot `cli/__init__.__all__` | `test_cli_all_covers_module_all` catches any gap; CI fails | After any `cli/utils.__all__` change, immediately mirror it in `cli/__init__.py` |
| Taking `--theirs` during rebase for PR changes | Confused rebase `ours`/`theirs` semantics with merge semantics | During `rebase`, `--ours` = replayed commit (PR side), `--theirs` = base (main); opposite of merge | In a rebase, `--ours` IS the PR branch changes |
| Leaving old Protocol stub after signature change | Changed `_call_claude` to `timeout: int = 300` in `Planner` but left Protocol as `timeout: int \| None = None` | mypy `arg-type` error on every call site that passes an `int` | Always grep for Protocol/ABC definitions of any method being refactored |
| Not checking all callers of removed functions | Removed timeout helpers but only updated obvious call sites | 3 callers in different automation modules retained dead imports → `ImportError` at runtime | `grep -rn "<removed_func>" hephaestus/` before removing any function |
| Trusting `PYTHONPATH` set in shell for local commits | Used project-root `PYTHONPATH` to ensure correct imports | Pre-commit's isolated env uses the system/pixi-installed scripts, which resolve via `PYTHONPATH` to stale code | Always use `env -u PYTHONPATH git commit` in worktrees; new console scripts require re-install in the worktree env |
| Reuse bare `type=int` for timeout flags | Accepted zero and negative integers because argparse only validated syntax, not the timeout domain | Downstream code receives values with ambiguous semantics; zero may be mistaken for disable even when omission is the only default-selection contract | Centralize a strictly positive parser for flags that require it and document zero semantics in shared help |
| Apply the positive parser to every option named timeout | Included an option whose established contract says zero or negative disables the bound | A shared validator would silently remove an intentional operator capability | Inventory semantic domains first and preserve explicit disable contracts on their separate parsing and normalization path |
| Test only `--agent-timeout` | Added boundary tests for one helper and assumed five siblings matched | Copy-pasted helpers can retain `type=int` or omit the help suffix while the representative test stays green | Parameterize the helper/flag matrix so every shared timeout entry point proves the same boundary and help contract |

## Results & Parameters

### Pattern: Timeout Refactor Checklist

When removing env-var timeout controls and adding CLI `--*-timeout` args:

```text
1. [ ] All callers of removed timeout functions updated (grep -rn "<func_name>" hephaestus/)
2. [ ] Protocol stubs updated to match new implementation signatures
3. [ ] cli/__init__.__all__ mirrors cli/utils.__all__
4. [ ] Tests asserting env-var behavior updated to assert fixed-default behavior
5. [ ] New test files use: from pathlib import Path; tmp_path: Path
6. [ ] New type: ignore codes match mypy's actual reported error code
7. [ ] After rebase: ruff check --select F811 to catch duplicate definitions
8. [ ] After rebase: check for lost module-level variables in conflict resolutions
9. [ ] Local commits: env -u PYTHONPATH git commit -S -s -m "..."
10. [ ] Shared timeout helpers reject zero and negatives with one domain parser
11. [ ] Help says zero is invalid and omission selects the configured default
12. [ ] Separate zero-disables timeout options retain their documented behavior
```

### Proposed Shared-Timeout Test Matrix

```python
_TIMEOUT_ARGUMENTS = (
    (add_agent_timeout_arg, "--agent-timeout"),
    (add_advise_timeout_arg, "--advise-timeout"),
    (add_git_message_timeout_arg, "--git-message-timeout"),
    (add_learn_timeout_arg, "--learn-timeout"),
    (add_follow_up_timeout_arg, "--follow-up-timeout"),
    (add_poll_max_wait_arg, "--poll-max-wait"),
)

@pytest.mark.parametrize(("add_timeout_argument", "flag"), _TIMEOUT_ARGUMENTS)
@pytest.mark.parametrize("value", ["0", "-1"])
def test_timeout_helpers_reject_non_positive_values(
    add_timeout_argument: Callable[[argparse.ArgumentParser], None],
    flag: str,
    value: str,
) -> None:
    parser = argparse.ArgumentParser()
    add_timeout_argument(parser)
    with pytest.raises(SystemExit) as exc:
        parser.parse_args([flag, value])
    assert exc.value.code == 2
```

Run both focused and combined suites after implementation:

```bash
uv run pytest tests/unit/automation/test_timeout_cli_threading.py -q
uv run pytest tests/unit/cli/test_utils.py tests/unit/automation/test_timeout_cli_threading.py -q
```

### mypy Error Code Reference

| Error Code | Cause | Fix |
|------------|-------|-----|
| `attr-defined` | Attribute does not exist on the static type (incl. `Any`) | Use correct type annotation or correct attribute name |
| `union-attr` | Object may be `None` or a union type; attribute access unsafe | Add `assert x is not None` or `if x is not None` guard |
| `arg-type` | Argument type incompatible with parameter | Update call site or update parameter type in definition |
| `override` | Method signature in subclass incompatible with base | Update subclass or Protocol stub to match |

### Rebase Conflict Semantics (versus Merge)

| Operation | `--ours` | `--theirs` |
|-----------|----------|------------|
| `git merge feature` | current branch (main) | incoming branch (feature) |
| `git rebase main` | replayed commit (PR/feature) | base branch (main) |

### Console Script Re-install in Worktree

```bash
# Required when a NEW console script is added in the PR being worked on
# (existing scripts are already installed; new ones appear only after re-install)
cd /path/to/worktree
pixi run pip install -e ".[automation]" --no-deps
# Verify the new script is now on PATH:
pixi run which hephaestus-check-api-table-docs
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1526, PR #1657 — HEPH_* env-var timeouts → --agent-timeout CLI options | 10 CI failure modes fixed; pre-commit clean; CI green; PR merged |
| ProjectHephaestus | CLI boundary-hardening plan — positive domains for six shared timeout helpers, separate `--phase-timeout` disable contract | unverified plan, 2026-08-06 |

## References

- [python-type-hints-and-mypy-patterns.md](python-type-hints-and-mypy-patterns.md) — Broader mypy annotation patterns
- [python-abc-protocol-contract-test-regression.md](python-abc-protocol-contract-test-regression.md) — Protocol/ABC stub regression patterns
- [ci-failure-triage-and-diagnosis.md](ci-failure-triage-and-diagnosis.md) — General CI triage workflow
