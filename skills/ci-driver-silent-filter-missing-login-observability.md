---
name: ci-driver-silent-filter-missing-login-observability
description: "When an author-filter guard silently drops items with a missing REST field, add a warning-level log inside the filter branch. Use when: (1) a filter uses .get() on a field that could be None from a schema change, (2) silent drops could cause a done-gate to false-green."
category: debugging
date: 2026-06-12
version: "1.1.0"
history: ci-driver-silent-filter-missing-login-observability.history
user-invocable: false
verification: unverified
tags: []
---

# CI Driver Silent Filter Missing Login Observability

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-12 |
| **Version** | 1.1.0 |
| **History** | [ci-driver-silent-filter-missing-login-observability.history](ci-driver-silent-filter-missing-login-observability.history) |
| **Objective** | Add warning-level logs at author-filter sites in `hephaestus/automation/ci_driver.py` so PRs with a missing `user.login` REST field are surfaced rather than silently dropped (issue #1152) |
| **Outcome** | Plan complete; implementation not yet run |
| **Verification** | unverified |

## When to Use

- A filter calls `.get('login')` (or any nullable REST field) and the branch that falls through is silent — no log, no counter, no metric
- Silent drops could cause a done-gate (e.g. "all open PRs are covered") to false-green because missing-login PRs simply vanish from consideration
- The existing codebase already uses `logger.warning(..., extra={...})` elsewhere in the same module, so the pattern is established
- The viewer-scoped author filter is active (viewer != None); the `--all` / `include_all_authors=True` path bypasses the filter entirely and does not need a warning

## Verified Workflow

> **Note:** This workflow is in plan phase only and has not been validated end-to-end. Treat as a hypothesis until CI confirms. Verification status: `unverified`.

### Quick Reference

```python
# Pattern: add warning INSIDE the existing viewer filter branch, before continue
if viewer and user.get('login') != viewer:
    if user.get('login') is None:
        logger.warning(
            "PR #%s has no user.login — skipped by author filter",
            pr.get('number', '?'),
            extra={"pr_number": pr.get('number'), "url": pr.get('html_url')},
        )
    continue
```

### Detailed Steps

1. **Locate both filter sites** in `hephaestus/automation/ci_driver.py`:
   - `_list_open_prs_remaining` (near line 346): filters open PRs by viewer login
   - `_discover_bot_prs` (near line 492): filters Bot-type PRs by viewer login
   - Read lines 285–504 in a single pass to get full context for both sites

2. **Insert the warning guard** at each site, nested inside the existing `if viewer and user.get('login') != viewer:` block, immediately before the `continue` statement.

3. **Verify the `extra=` kwarg style** used by existing `logger.warning` calls in the same file (lines 313, 337, 464, 483) before writing — confirm whether positional-only or `extra=dict` is the established pattern.

4. **Write tests** in `tests/unit/automation/test_ci_driver_author_scope.py` (the file already has the fixture and driver pattern):
   - Add a fixture `_MISSING_LOGIN_OPEN_PULLS` with `login: None` entries
   - Add a fixture `_MISSING_LOGIN_BOT_PULLS` with `"type": "Bot"` and `login: None`
   - For the positive (warning-emitting) tests: assert the warning is emitted via `caplog.at_level(logging.WARNING, logger="hephaestus.automation.ci_driver")`
   - For the negative (no-warning) tests: assert no warning fires AND (where not coupling to other logic) the PR appears in results — see "Negative Test Completeness" below

5. **Order-of-guards check for `_discover_bot_prs`**: The Bot-type guard fires first (`if user.get("type") != "Bot": continue`). A Bot PR with `login: None` passes the type check, then hits the viewer filter — this is the correct path for the warning to fire. Reviewers must confirm this ordering is preserved.

### Negative Test Completeness

**Negative test pattern for conditional guards:**
Negative tests must assert BOTH:
1. The side effect does NOT fire (e.g., no warning logged)
2. The guarded code path executed successfully (e.g., the PR appears in results)

For `_list_open_prs_remaining` under `--all`: assert no warning fires AND the PR appears in the returned list.

For `_discover_bot_prs` under `--all`: assert no warning fires. Asserting the PR appears in results is acceptable to omit here — the bot-type check precedes the viewer check, so a bot PR with `login=None` is included only if it passes the bot-type filter; verifying the PR number would add coupling to bot-type logic that is tested separately.

R1 test methods added:
- `test_list_open_prs_remaining_no_warning_under_all` — asserts no warning + PR in results
- `test_discover_bot_prs_no_warning_under_all` — asserts no warning only (bot-type coupling risk)

Style fixes applied in R1:
- `import logging` moved to module top (was inside `with` block)
- Redundant `include_all_authors = False` removed from positive tests (it is the default; the assignment was a misleading no-op)

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Acknowledging TDD gap without closing it | R0 plan noted the missing negative test for `--all` path with "Consider adding one" but did not add it to the plan | Reviewer correctly issued NOGO — named gaps must be resolved in the same plan, not deferred to the implementer | Any TDD gap identified during planning must be closed in that same plan iteration; "consider adding" is not acceptable |
| None yet (implementation) | Plan phase only | N/A | Line numbers (346, 492) verified at plan time but may drift before implementation — re-read the file before editing |

## Results & Parameters

### Assumptions That May Not Hold

| Assumption | Risk | Mitigation |
|------------|------|------------|
| Line numbers 346 and 492 are stable | Any unrelated commit to ci_driver.py shifts them | Re-read file at implementation time; do not rely on plan-time line numbers |
| `logger.warning(..., extra={...})` is the established kwarg style | Existing calls may be positional-only | Grep the actual call sites (lines 313, 337, 464, 483) before writing new calls |
| `caplog.at_level` with logger string works in pytest | Standard pytest behavior | Confirmed standard; low risk |

### Warning Scope: Viewer-Filter Only

The warning fires **only** when:
- `viewer` is not None (viewer-scoped run)
- `user.get('login')` is None (missing REST field)

It does **not** fire when `include_all_authors=True` because the entire `if viewer and ...` block is skipped. This is intentional — under `--all`, all PRs are included regardless of login.

### Test Pattern (pytest caplog)

```python
import logging

def test_missing_login_emits_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="hephaestus.automation.ci_driver"):
        # call the filter function with a PR where user.login is None
        ...
    assert any("no user.login" in r.message for r in caplog.records)

def test_list_open_prs_remaining_no_warning_under_all(caplog):
    with caplog.at_level(logging.WARNING, logger="hephaestus.automation.ci_driver"):
        result = _list_open_prs_remaining(..., include_all_authors=True)
    assert not any("no user.login" in r.message for r in caplog.records)
    assert any(pr["number"] == EXPECTED_PR_NUMBER for pr in result)

def test_discover_bot_prs_no_warning_under_all(caplog):
    with caplog.at_level(logging.WARNING, logger="hephaestus.automation.ci_driver"):
        _discover_bot_prs(..., include_all_authors=True)
    assert not any("no user.login" in r.message for r in caplog.records)
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1152 planning session | Plan only; implementation pending |
