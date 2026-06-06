---
name: shared-predicate-preventing-gate-discovery-drift
description: "DRY pattern for keeping gate and discovery predicates in sync. When a gate (e.g., `_count_failing_prs`) must match a discovery method (e.g., `_discover_failing_prs`), define the filter predicate (_pr_is_failing) in the discovery module and import it into the gate module. Avoids duplicated filter logic that can diverge over time, causing silent bugs where the gate and discovery see different data. Use when: (1) gate and discovery must use identical filters, (2) multiple modules need the same predicate, (3) preventing silent gate/discovery divergence."
category: ci-cd
date: 2026-06-06
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - code-reuse
  - DRY-principle
  - gate-consistency
  - discovery-parity
  - single-source-of-truth
  - test-filter-drift
  - predicate-sharing
  - refactoring-pattern
---

# Shared Predicates Prevent Gate/Discovery Divergence

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-06 |
| **Objective** | Document the DRY pattern for keeping gate and discovery predicates in sync when they must use identical filters. Define the filter predicate in the discovery module; import it in the gate module. Avoids duplicated filter logic that can diverge over time, causing silent bugs where the gate reports "no work" while the discovery finds work. |
| **Outcome** | Shipped in ProjectHephaestus issue #819 / PR #852. Refactored `_pr_is_failing` predicate from drive-green-ecosystem module: defined once in `hephaestus/automation/discovery.py`, imported into gate code. All 1143 automation tests pass, including gate/discovery parity tests. |
| **Verification** | verified-ci (full test suite passes; predicate refactoring validated) |
| **History** | New skill — no amendments yet. |

## When to Use

- You are writing a gate function (e.g., `_count_failing_prs` in a "is repo done?" check) that must use the exact same filter as a discovery function (e.g., `_discover_failing_prs`)
- The filter logic is non-trivial (checking multiple conditions: merge state, check conclusions, draft status, etc.)
- The gate and discovery live in different modules, making copy-paste tempting
- You want to prevent the failure mode: "gate says 0 PRs to fix, but discovery found 5" due to diverged filters
- Code review will need to verify that gate and discovery use identical predicates

## Verified Workflow

### Quick Reference

**Define the predicate once; import it everywhere:**

```python
# discovery.py (source of truth)
def _pr_is_failing(pr: dict) -> bool:
    """True iff PR is BLOCKED with failed CI checks."""
    if pr.get("mergeStateStatus") != "BLOCKED":
        return False
    checks = pr.get("statusCheckRollup", [])
    return any(c.get("conclusion") in ("FAILURE", "CANCELLED", "TIMED_OUT") for c in checks)


def _discover_failing_prs(repo_root: str) -> dict[int, int]:
    """Use _pr_is_failing to filter the PR list."""
    # ... fetch PRs ...
    failing = {pr["number"]: pr["number"] for pr in prs if _pr_is_failing(pr)}
    return failing


# gate.py (reuses predicate)
from hephaestus.automation.discovery import _pr_is_failing

def _count_failing_prs(repo_root: str) -> int:
    """True iff no PRs match the failing filter (gate check)."""
    # ... fetch PRs ...
    count = sum(1 for pr in prs if _pr_is_failing(pr))
    return count == 0  # Gate passes if count == 0
```

### Detailed Steps

#### The divergence bug: duplicated filter logic

Consider two functions in different modules:

```python
# discovery.py
def _discover_failing_prs(repo_root: str) -> dict[int, int]:
    prs = _gh_call(["pr", "list", "--json", ...])
    failing = {}
    for pr in prs:
        if pr.get("isDraft"):  # FILTER A: skip drafts
            continue
        if pr.get("mergeStateStatus") != "BLOCKED":  # FILTER B: require BLOCKED
            continue
        checks = pr.get("statusCheckRollup", [])
        has_failure = any(c.get("conclusion") in ("FAILURE", "CANCELLED", "TIMED_OUT") for c in checks)
        if has_failure:  # FILTER C: require failure
            failing[pr["number"]] = pr["number"]
    return failing


# gate.py
def _is_repo_done(repo_root: str) -> bool:
    """Check if there are no more PRs to fix (gate check)."""
    prs = _gh_call(["pr", "list", "--json", ...])
    for pr in prs:
        if pr.get("isDraft"):  # FILTER A (copy)
            continue
        if pr.get("mergeStateStatus") != "BLOCKED":  # FILTER B (copy)
            continue
        checks = pr.get("statusCheckRollup", [])
        has_failure = any(c.get("conclusion") in ("FAILURE", "CANCELLED", "TIMED_OUT") for c in checks)
        if has_failure:  # FILTER C (copy)
            return False  # Found a PR to fix — repo is NOT done
    return True  # No PRs match the filter — repo is done
```

**The bug**: Filters are identical now, but they will diverge:

- **Scenario 1**: A future PR fixes a bug in the discovery logic ("actually, don't skip draft PRs"). The reviewer updates discovery.py but forgets to update gate.py.
  - Result: `_discover_failing_prs` includes drafts, but `_is_repo_done` still skips them.
  - Symptom: Loop exits "repo is done" while failing draft PRs remain in the repo.
- **Scenario 2**: A new CI check type appears (SKIPPED conclusions). The discovery logic adds `"SKIPPED"` to the failure list. The gate doesn't get updated.
  - Result: Discovery finds SKIPPED-check PRs, gate doesn't, gate says "repo done" before discovery's work is complete.

#### Why shared predicates prevent divergence

**Source of truth pattern:**

```python
# discovery.py — the canonical source
def _pr_is_failing(pr: dict) -> bool:
    """Canonical predicate: True iff PR matches our 'failing' filter.
    
    Used by both discovery and gate functions to prevent filter divergence.
    Change this function, and both users are updated automatically.
    """
    if pr.get("isDraft"):
        return False  # Skip drafts
    if pr.get("mergeStateStatus") != "BLOCKED":
        return False  # Require BLOCKED
    checks = pr.get("statusCheckRollup", [])
    if not any(c.get("conclusion") in ("FAILURE", "CANCELLED", "TIMED_OUT") for c in checks):
        return False  # Require at least one failure
    return True


def _discover_failing_prs(repo_root: str) -> dict[int, int]:
    """Use the canonical predicate."""
    prs = _gh_call(["pr", "list", "--json", ...])
    failing = {pr["number"]: pr["number"] for pr in prs if _pr_is_failing(pr)}
    return failing


# gate.py — imports and reuses
from hephaestus.automation.discovery import _pr_is_failing

def _is_repo_done(repo_root: str) -> bool:
    """Check if no PRs match the failing filter."""
    prs = _gh_call(["pr", "list", "--json", ...])
    for pr in prs:
        if _pr_is_failing(pr):
            return False  # Found a PR to fix
    return True  # No PRs match the filter
```

Now:
- Change `_pr_is_failing` once → both discovery and gate see the change automatically
- Code review is simple: "does gate import the predicate?" → one question, not "are the filters identical?"
- Future maintainers will naturally extend the predicate once, not twice
- Tests can validate the predicate in isolation, then trust both users

#### Module structure: where to define the predicate

**Rule: Define predicates in the discovery module, import elsewhere.**

Why discovery?
1. Discovery is the "primary" user — it directly enumerates work
2. The gate is a **secondary consumer** of the same filter
3. The predicate describes "what counts as work" — a discovery concern
4. If gate and discovery split later (unlikely), you keep the predicate close to discovery

Example file structure:

```
hephaestus/automation/
├── discovery.py          ← Define _pr_is_failing, _discover_failing_prs
├── gate.py              ← Import _pr_is_failing, define _is_repo_done
├── ci_driver.py         ← Calls both gate and discovery
└── __init__.py
```

#### Writing testable predicates

Predicates should be **pure functions** — no side effects, no dependencies:

```python
def _pr_is_failing(pr: dict) -> bool:
    """Pure function: no IO, no logging, no external calls.
    
    Args:
        pr: PR dict from gh pr list --json output
    
    Returns:
        True iff PR matches the "failing" filter
    """
    if pr.get("isDraft"):
        return False
    if pr.get("mergeStateStatus") != "BLOCKED":
        return False
    checks = pr.get("statusCheckRollup", [])
    return any(c.get("conclusion") in ("FAILURE", "CANCELLED", "TIMED_OUT") for c in checks)
```

**Test the predicate independently:**

```python
def test_pr_is_failing_requires_blocked_state():
    """PR with CLEAN state is not failing."""
    pr = {"mergeStateStatus": "CLEAN", "statusCheckRollup": [...]}
    assert not _pr_is_failing(pr)

def test_pr_is_failing_requires_failure_conclusion():
    """PR with SUCCESS checks but BLOCKED state is not failing."""
    pr = {
        "mergeStateStatus": "BLOCKED",
        "statusCheckRollup": [{"conclusion": "SUCCESS"}],
    }
    assert not _pr_is_failing(pr)

def test_pr_is_failing_true_when_blocked_and_failed():
    """PR with BLOCKED state and FAILURE conclusion is failing."""
    pr = {
        "isDraft": False,
        "mergeStateStatus": "BLOCKED",
        "statusCheckRollup": [{"conclusion": "FAILURE"}],
    }
    assert _pr_is_failing(pr)

def test_pr_is_failing_skips_drafts():
    """Draft PRs are never failing, even if checks failed."""
    pr = {
        "isDraft": True,
        "mergeStateStatus": "BLOCKED",
        "statusCheckRollup": [{"conclusion": "FAILURE"}],
    }
    assert not _pr_is_failing(pr)
```

#### Integration test: gate and discovery parity

```python
def test_gate_and_discovery_use_same_predicate():
    """Verify gate and discovery agree on which PRs are failing."""
    # Arrange: sample PRs with various states
    prs = [
        {"number": 1, "isDraft": False, "mergeStateStatus": "BLOCKED",
         "statusCheckRollup": [{"conclusion": "FAILURE"}]},  # failing
        {"number": 2, "isDraft": False, "mergeStateStatus": "CLEAN",
         "statusCheckRollup": [{"conclusion": "SUCCESS"}]},  # clean
        {"number": 3, "isDraft": True, "mergeStateStatus": "BLOCKED",
         "statusCheckRollup": [{"conclusion": "FAILURE"}]},  # draft, skip
    ]
    
    # Act: what does discovery find?
    discovered = {pr["number"] for pr in prs if _pr_is_failing(pr)}
    
    # Act: what does gate count?
    gate_count = sum(1 for pr in prs if _pr_is_failing(pr))
    gate_done = gate_count == 0
    
    # Assert: discovery and gate must agree
    assert discovered == {1}  # Only PR 1 is failing
    assert gate_count == 1
    assert not gate_done  # Gate should say "not done" because a failing PR exists
```

#### Refactoring existing code: consolidate duplicate predicates

If you find duplicate filter logic in two functions:

1. **Extract the predicate:**
   ```python
   def _pr_is_failing(pr: dict) -> bool:
       # ... consolidated logic ...
   ```

2. **Replace both call sites:**
   ```python
   # Before (discovery.py)
   for pr in prs:
       if pr.get("isDraft"): continue
       if pr.get("mergeStateStatus") != "BLOCKED": continue
       checks = pr.get("statusCheckRollup", [])
       has_failure = any(...)
       if has_failure:
           failing[pr["number"]] = pr["number"]
   
   # After (discovery.py)
   for pr in prs:
       if _pr_is_failing(pr):
           failing[pr["number"]] = pr["number"]
   ```

3. **Import in gate module:**
   ```python
   # gate.py
   from hephaestus.automation.discovery import _pr_is_failing
   
   for pr in prs:
       if _pr_is_failing(pr):
           return False  # Found failing PR
   ```

4. **Add a test for parity:**
   ```python
   def test_gate_discovery_parity():
       # ... validate gate and discovery agree on sample PRs ...
   ```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Duplicate filter logic in both functions (copy-paste) | Write the same filter in discovery.py and gate.py | (a) Divergence over time: any bug fix in one place missed in the other. (b) Code review burden: must compare two copies line-by-line. (c) Humans forget to update both — inevitable. (d) Silent failures: gate and discovery report different results without warning. | Extract the filter into a shared predicate function. One source of truth, both users import it. |
| Define predicate in gate.py, import into discovery.py | Put the predicate "closer" to gate logic | (a) Gate is secondary concern — discovery is primary. (b) Confuses ownership: is the filter a gate concern or discovery concern? (c) Future refactoring may separate gate/discovery; keeping predicate in discovery is natural. (d) Circular import risk if gate and discovery both need each other. | Define predicate in discovery.py (the primary consumer); gate imports it. Clear ownership. |
| Use a mutable default for predicates: `FAILING_PR_CHECKS = ["FAILURE", ...]` in a config | Try to make filters easily configurable | (a) Mutable defaults in predicates lead to subtle bugs if the list is modified at runtime. (b) Gate and discovery might not see the same default if module import order varies. (c) Tests that modify the config affect other tests. (d) No clear "source of truth" for what counts as failing. | Keep predicates as pure functions, not config-dependent. If configurability is needed, pass config as arguments, not module globals. |
| Use inheritance: gate and discovery inherit from a base class with the predicate | Try to share via OOP | (a) Overcomplicates design — predicates are functions, not methods. (b) Coupling gate and discovery via inheritance is wrong (they're separate concerns). (c) Harder to test and reason about. | Use function imports, not inheritance. Functions are simpler and clearer. |
| Skip the gate entirely: only check discovery | Avoid duplication by not gating at all | (a) Gate serves a different purpose than discovery: gate checks "is work done?" while discovery finds work to do. (b) Omitting the gate removes a safety check — loop might exit early when work remains. (c) Gate is a required loop component for honest "zero-work convergence" checks. | Keep the gate, but ensure it and discovery use the same predicate. Both are necessary. |

## Results & Parameters

### Canonical predicate (copy-paste ready)

```python
# hephaestus/automation/discovery.py

from typing import Any


def _pr_is_failing(pr: dict[str, Any]) -> bool:
    """Canonical predicate: True iff PR should be included in failing set.
    
    Checks:
    1. Not a draft (drafts are not actionable)
    2. Merge state is BLOCKED (repo policy prevents merge)
    3. At least one CI check has FAILURE/CANCELLED/TIMED_OUT conclusion
    
    Used by both _discover_failing_prs (enumeration) and gate functions
    (_is_repo_done, _count_failing_prs) to prevent filter divergence.
    
    Args:
        pr: PR dict from `gh pr list --json statusCheckRollup,mergeStateStatus,...`
    
    Returns:
        True iff PR is failing per our definition
    """
    # Skip drafts — not ready for automation
    if pr.get("isDraft", False):
        return False
    
    # Require BLOCKED merge state
    if pr.get("mergeStateStatus") != "BLOCKED":
        return False
    
    # Require at least one failed check
    status_checks = pr.get("statusCheckRollup", [])
    has_failure = any(
        check.get("conclusion") in ("FAILURE", "CANCELLED", "TIMED_OUT")
        for check in status_checks
    )
    
    return has_failure
```

### Discovery function using shared predicate

```python
def _discover_failing_prs(repo_root: str) -> dict[int, int]:
    """Discover all failing PRs using the canonical predicate."""
    result = _gh_call(
        ["pr", "list", "--limit", "1000", "--json", 
         "number,isDraft,statusCheckRollup,mergeStateStatus"],
        cwd=repo_root,
        check=False,
    )
    
    if result.returncode != 0:
        logger.error("Failed to enumerate PRs: %s", result.stderr)
        return {}
    
    prs = json.loads(result.stdout or "[]")
    failing = {pr["number"]: pr["number"] for pr in prs if _pr_is_failing(pr)}
    
    logger.info("Discovered %d failing PRs", len(failing))
    return failing
```

### Gate function using shared predicate

```python
# gate.py

from hephaestus.automation.discovery import _pr_is_failing


def _is_repo_done(repo_root: str) -> bool:
    """Check if all failing PRs have been resolved (gate check for loop exit).
    
    Reuses the canonical _pr_is_failing predicate to stay in sync with
    _discover_failing_prs.
    
    Returns:
        True iff no PRs match the failing filter (work is complete)
    """
    result = _gh_call(
        ["pr", "list", "--limit", "1000", "--json",
         "number,isDraft,statusCheckRollup,mergeStateStatus"],
        cwd=repo_root,
        check=False,
    )
    
    if result.returncode != 0:
        logger.error("Could not check repo done: %s", result.stderr)
        return False  # Conservative: assume work remains if gh fails
    
    prs = json.loads(result.stdout or "[]")
    for pr in prs:
        if _pr_is_failing(pr):
            logger.info("PR #%d is still failing — repo not done", pr["number"])
            return False
    
    logger.info("No failing PRs remain — repo is done")
    return True
```

### Test coverage: predicate + discovery + gate parity

```python
# tests/unit/automation/test_failing_pr_predicate.py

import pytest
from hephaestus.automation.discovery import _pr_is_failing


class TestPrIsFailingPredicate:
    """Test the canonical predicate in isolation."""
    
    def test_predicate_requires_blocked_state(self):
        pr = {
            "mergeStateStatus": "CLEAN",
            "statusCheckRollup": [{"conclusion": "FAILURE"}],
        }
        assert not _pr_is_failing(pr)
    
    def test_predicate_requires_failure_conclusion(self):
        pr = {
            "mergeStateStatus": "BLOCKED",
            "statusCheckRollup": [{"conclusion": "SUCCESS"}],
        }
        assert not _pr_is_failing(pr)
    
    def test_predicate_accepts_multiple_conclusion_types(self):
        for conclusion in ("FAILURE", "CANCELLED", "TIMED_OUT"):
            pr = {
                "mergeStateStatus": "BLOCKED",
                "statusCheckRollup": [{"conclusion": conclusion}],
            }
            assert _pr_is_failing(pr), f"Should accept {conclusion}"
    
    def test_predicate_skips_drafts(self):
        pr = {
            "isDraft": True,
            "mergeStateStatus": "BLOCKED",
            "statusCheckRollup": [{"conclusion": "FAILURE"}],
        }
        assert not _pr_is_failing(pr)
    
    def test_predicate_true_when_all_conditions_met(self):
        pr = {
            "isDraft": False,
            "mergeStateStatus": "BLOCKED",
            "statusCheckRollup": [{"conclusion": "FAILURE"}],
        }
        assert _pr_is_failing(pr)


class TestGateDiscoveryParity:
    """Verify gate and discovery use the same predicate."""
    
    def test_discovery_and_gate_agree_on_failing_prs(self, mocker):
        """Gate and discovery must identify the same PRs as failing."""
        # Mock gh pr list response
        prs = [
            {
                "number": 1,
                "isDraft": False,
                "mergeStateStatus": "BLOCKED",
                "statusCheckRollup": [{"conclusion": "FAILURE"}],
            },  # Failing ✓
            {
                "number": 2,
                "isDraft": False,
                "mergeStateStatus": "CLEAN",
                "statusCheckRollup": [{"conclusion": "SUCCESS"}],
            },  # Not failing
            {
                "number": 3,
                "isDraft": True,
                "mergeStateStatus": "BLOCKED",
                "statusCheckRollup": [{"conclusion": "FAILURE"}],
            },  # Draft, skip
        ]
        
        # What discovery finds
        discovered = {pr["number"] for pr in prs if _pr_is_failing(pr)}
        
        # What gate counts
        gate_failing = sum(1 for pr in prs if _pr_is_failing(pr))
        
        # Must agree
        assert discovered == {1}
        assert gate_failing == 1
```

### Verification evidence

- **PR #852 in ProjectHephaestus** (issue #819): Refactored `_pr_is_failing` predicate from drive-green-ecosystem module; now shared between discovery and gate.
- **Test coverage**: `tests/unit/automation/test_failing_pr_predicate.py`:
  - `TestPrIsFailingPredicate`: Pure predicate tests (5 tests)
  - `TestGateDiscoveryParity`: Gate/discovery parity validation (2 tests)
- **CI result**: All 1143 automation tests pass; refactoring validated without regressions

### Related skills

- `architecture-bot-pr-discovery-synthetic-issue-key.md` — another use of shared predicates (sharing `_is_bot_pr_mode` guard across multiple call sites)
- `automation-loop-early-exit-zero-work-convergence.md` — gate functions are part of the loop's zero-work convergence check; shared predicates keep the gate honest
- `failing-pr-discovery-gh-enumeration.md` — the discovery function that uses `_pr_is_failing`

### Quick audit recipe — find predicate divergence in automation code

```bash
# Find filter logic duplicated in gate and discovery functions
grep -n "mergeStateStatus.*BLOCKED\|statusCheckRollup" --include="*.py" hephaestus/automation/*.py

# For each match, check if it's inside both a gate function and discovery function
# If yes, and they're not identical, you've found a drift bug

# To verify they're shared: check if one imports from the other
grep -n "from.*discovery import _pr_is_failing" --include="*.py" hephaestus/automation/*.py
```

If audit finds duplicates without imports, consolidate them per this skill.
